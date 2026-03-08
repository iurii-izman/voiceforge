"""STT via faster-whisper (CTranslate2, INT8)."""

import time
from dataclasses import dataclass

import numpy as np
import psutil
import structlog
from faster_whisper import WhisperModel

log = structlog.get_logger()

# RSS threshold above which we log a warning (bytes)
RSS_WARNING_BYTES = 4 * 1024**3
MAX_DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_BACKOFF_BASE_SEC = 1.0


@dataclass
class Segment:
    """One transcribed segment."""

    start: float
    end: float
    text: str
    language: str | None
    confidence: float


def _load_whisper_model(model_size: str, device: str, compute_type: str):
    """Load Whisper model with download log and retry on network failure (E3 #126)."""
    log.info("stt.downloading_model", size=model_size, message=f"Downloading Whisper model ({model_size})...")
    last_error: Exception | None = None
    for attempt in range(MAX_DOWNLOAD_ATTEMPTS):
        try:
            return WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            last_error = e
            if attempt < MAX_DOWNLOAD_ATTEMPTS - 1:
                delay = DOWNLOAD_BACKOFF_BASE_SEC * (2**attempt)
                log.warning(
                    "stt.model_download_retry",
                    attempt=attempt + 1,
                    error=str(e),
                    retry_sec=delay,
                )
                time.sleep(delay)
    raise last_error


class Transcriber:
    """Wrapper around faster-whisper. Model loaded once and reused."""

    def __init__(
        self,
        model_size: str = "small",
        compute_type: str = "int8",
        device: str = "cpu",
    ) -> None:
        self._model = _load_whisper_model(model_size, device, compute_type)
        self._model_size = model_size
        self._process = psutil.Process()  # cache once — Process() does a syscall per call

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        sample_rate: int = 16000,
        *,
        beam_size: int = 1,
        vad_filter: bool = True,
        vad_parameters: dict | None = None,
    ) -> list[Segment]:
        """Transcribe audio (int16 or float32). Returns list of Segment."""
        if audio.dtype == np.int16:
            audio_f = audio.astype(np.float32) / 32768.0
        else:
            audio_f = audio.astype(np.float32, copy=False)

        if sample_rate != 16000:
            log.debug("transcribe.sample_rate_ignored", sample_rate=sample_rate, expected=16000)

        vad_params = vad_parameters or {"min_silence_duration_ms": 600}
        # faster-whisper expects 16 kHz float32; we pass pre-resampled audio
        segments_iter, info = self._model.transcribe(
            audio_f,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=vad_params,
        )

        out: list[Segment] = []
        lang = getattr(info, "language", None) or language
        for s in segments_iter:
            confidence = 1.0 - getattr(s, "no_speech_prob", 0.0)
            out.append(
                Segment(
                    start=s.start,
                    end=s.end,
                    text=s.text.strip(),
                    language=lang,
                    confidence=confidence,
                )
            )

        rss = self._process.memory_info().rss
        log.info("transcribe.done", segments=len(out), rss_mb=round(rss / 1024**2, 1))
        if rss > RSS_WARNING_BYTES:
            log.warning("transcribe.high_rss", rss_gb=round(rss / 1024**3, 2))

        return out
