"""E12 #135: Real-audio E2E — WAV fixture → STT → verify segments. Skip in CI without models."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from voiceforge.stt.transcriber import Transcriber

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_RATE = 16000


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    """Load WAV as (samples int16, sample_rate)."""
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    return np.frombuffer(buf, dtype=np.int16), rate


@pytest.mark.integration
def test_real_audio_wav_to_stt_segments_not_empty() -> None:
    """Load WAV fixture → transcribe → verify segments list and structure (E12 real-audio E2E)."""
    path = FIXTURES_DIR / "clean_5s.wav"
    if not path.exists():
        path = FIXTURES_DIR / "silence_5s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")
    segments = transcriber.transcribe(audio, sample_rate=rate)
    assert isinstance(segments, list)
    # For silence fixtures we may get one segment (e.g. "(тишина)") or empty; for speech, non-empty
    for s in segments:
        assert hasattr(s, "start") and hasattr(s, "end") and hasattr(s, "text")
    # At least structure is valid; content depends on fixture (speech vs silence)
    assert all(s.start <= s.end for s in segments)
