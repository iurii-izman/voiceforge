"""Block 4.4: Smart Trigger — auto-analyze on semantic pause (silence after speech).
Uses Silero VAD from faster-whisper."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import structlog

log = structlog.get_logger()

# Defaults from BLOCKS.md: silence > 3 s after >= 30 s speech; cooldown 2 min
DEFAULT_MIN_SPEECH_SEC = 30.0
DEFAULT_MIN_SILENCE_SEC = 3.0
DEFAULT_COOLDOWN_SEC = 120.0
DEFAULT_ANALYZE_SECONDS = 30


class SmartTrigger:
    """Trigger analyze when silence > min_silence_sec after at least min_speech_sec of speech.
    Uses Silero VAD from faster-whisper (no extra models)."""

    def __init__(
        self,
        sample_rate: int = 16000,
        min_speech_sec: float = DEFAULT_MIN_SPEECH_SEC,
        min_silence_sec: float = DEFAULT_MIN_SILENCE_SEC,
        cooldown_sec: float = DEFAULT_COOLDOWN_SEC,
        analyze_seconds: int = DEFAULT_ANALYZE_SECONDS,
    ) -> None:
        self.sample_rate = sample_rate
        self.min_speech_sec = min_speech_sec
        self.min_silence_sec = min_silence_sec
        self.cooldown_sec = cooldown_sec
        self.analyze_seconds = analyze_seconds
        self._last_trigger_time: float = 0.0

    def check(self, ring_path: str | Path) -> bool:
        """Read ring buffer, run VAD; return True if trigger fired (semantic pause + cooldown).
        Call every ~2 sec from daemon."""
        path = Path(ring_path)
        if not path.is_file():
            return False
        raw = path.read_bytes()
        # Need at least min_speech_sec + min_silence_sec of audio
        min_samples = int(self.sample_rate * (self.min_speech_sec + self.min_silence_sec))
        if len(raw) < min_samples * 2:  # 2 bytes per sample (int16)
            return False
        audio_i16 = np.frombuffer(raw, dtype=np.int16)
        audio_f = audio_i16.astype(np.float32) / 32768.0

        try:
            from faster_whisper.vad import VadOptions, get_speech_timestamps
        except ImportError:
            log.debug("smart_trigger.no_vad", hint="faster-whisper not installed")
            return False

        vad_options = VadOptions(
            min_silence_duration_ms=int(self.min_silence_sec * 1000),
            min_speech_duration_ms=250,
        )
        segments = get_speech_timestamps(
            audio_f,
            vad_options=vad_options,
            sampling_rate=self.sample_rate,
        )
        if not segments:
            return False

        total_speech_samples = sum(seg["end"] - seg["start"] for seg in segments)
        total_speech_sec = total_speech_samples / self.sample_rate
        if total_speech_sec < self.min_speech_sec:
            return False

        last_end = segments[-1]["end"]
        silence_samples = len(audio_f) - last_end
        silence_sec = silence_samples / self.sample_rate
        if silence_sec < self.min_silence_sec:
            return False

        now = time.monotonic()
        if now - self._last_trigger_time < self.cooldown_sec:
            return False

        self._last_trigger_time = now
        log.info(
            "smart_trigger.fired",
            speech_sec=round(total_speech_sec, 1),
            silence_sec=round(silence_sec, 1),
            analyze_seconds=self.analyze_seconds,
        )
        return True
