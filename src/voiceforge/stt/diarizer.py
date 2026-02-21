"""Speaker diarization via pyannote.audio. STRICT 3.3.2 — 4.x = OOM."""

import gc
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

# TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD is scoped inside _get_pipeline() to avoid
# disabling pickle safety globally at import time.
# torchaudio 2.9+ removed list_audio_backends and AudioMetaData; pyannote 3.3.2 still uses them
import torch
import torchaudio

if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: [""]  # type: ignore[attr-defined]
if not hasattr(torchaudio, "AudioMetaData"):

    class _AudioMetaData:
        def __init__(
            self,
            sample_rate: int = 0,
            num_frames: int = 0,
            num_channels: int = 1,
            **kwargs: Any,
        ) -> None:
            self.sample_rate = sample_rate
            self.num_frames = num_frames
            self.num_channels = num_channels
            for k, v in kwargs.items():
                setattr(self, k, v)

    torchaudio.AudioMetaData = _AudioMetaData  # type: ignore[attr-defined,misc]

# huggingface_hub v0.20+ dropped use_auth_token; pyannote 3.3.2 still passes it
import huggingface_hub

_orig_hf_hub_download = huggingface_hub.hf_hub_download


def _hf_hub_download(*args, **kwargs):
    if "use_auth_token" in kwargs:
        kwargs.setdefault("token", kwargs.pop("use_auth_token"))
    return _orig_hf_hub_download(*args, **kwargs)


huggingface_hub.hf_hub_download = _hf_hub_download

import numpy as np
import psutil
import structlog
from pyannote.audio import Pipeline

log = structlog.get_logger()

WINDOW_SEC = 30.0
RSS_GUARD_BYTES = 5 * 1024**3
DEFAULT_MODEL = "pyannote/speaker-diarization-3.0"


@dataclass
class DiarSegment:
    """One speaker segment."""

    start: float
    end: float
    speaker: str


class Diarizer:
    """Wrapper around pyannote.audio Pipeline. Call AFTER STT, not in parallel."""

    def __init__(
        self,
        auth_token: str,
        model_id: str = DEFAULT_MODEL,
        restart_hours: int = 2,
    ) -> None:
        self._auth_token = auth_token
        self._model_id = model_id
        self._refresh_interval_sec = restart_hours * 3600
        self._pipeline: Pipeline | None = None
        self._pipeline_created_at: float = 0.0
        self._pipeline_lock = threading.Lock()  # prevents double-load OOM under concurrent calls

    def _get_pipeline(self) -> Pipeline:
        with self._pipeline_lock:
            if self._pipeline is None or (time.monotonic() - self._pipeline_created_at > self._refresh_interval_sec):
                if self._pipeline is not None:
                    log.info("diarizer.pipeline_refresh", reason=f"{self._refresh_interval_sec // 3600}h interval")
                    del self._pipeline
                    gc.collect()
                # Scope weights_only override to just this load; don't pollute the whole process
                _prev = os.environ.get("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD")
                os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
                try:
                    self._pipeline = Pipeline.from_pretrained(
                        self._model_id,
                        use_auth_token=self._auth_token,
                    )
                finally:
                    if _prev is None:
                        os.environ.pop("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", None)
                    else:
                        os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = _prev
                self._pipeline_created_at = time.monotonic()
            return self._pipeline

    def _memory_guard(self) -> None:
        rss = psutil.Process().memory_info().rss
        if rss > RSS_GUARD_BYTES:
            log.warning("diarizer.high_rss", rss_gb=round(rss / 1024**3, 2))
            gc.collect()

    def diarize(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> list[DiarSegment]:
        """Diarize audio in 30s windows. Returns list of DiarSegment."""
        if audio.dtype == np.int16:
            audio_f = audio.astype(np.float32) / 32768.0
        else:
            audio_f = audio.astype(np.float32)

        duration_sec = len(audio_f) / sample_rate
        out: list[DiarSegment] = []
        pipeline = self._get_pipeline()
        # (channel, time) for waveform input
        step = WINDOW_SEC
        t = 0.0
        while t < duration_sec:
            self._memory_guard()
            t_end = min(t + step, duration_sec)
            start_sample = int(t * sample_rate)
            end_sample = int(t_end * sample_rate)
            chunk = audio_f[start_sample:end_sample]

            if chunk.size == 0:
                t = t_end
                continue

            # Pipeline accepts {"waveform": (C, T) Tensor, "sample_rate": int}
            waveform = torch.from_numpy(chunk.reshape(1, -1)).float()
            input_dict = {"waveform": waveform, "sample_rate": sample_rate}
            with torch.no_grad():
                diar = pipeline(input_dict)
            for segment, _, speaker in diar.itertracks(yield_label=True):
                out.append(
                    DiarSegment(
                        start=segment.start + t,
                        end=segment.end + t,
                        speaker=speaker,
                    )
                )
            t = t_end

        self._memory_guard()
        log.info("diarize.done", segments=len(out), duration_sec=round(duration_sec, 1))
        return out
