"""WAV-based STT integration tests (faster-whisper on real audio)."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from voiceforge.stt.transcriber import Transcriber

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_RATE = 16000
TYISHINA = "(тишина)"


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    """Load WAV as (samples int16, sample_rate)."""
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    return np.frombuffer(buf, dtype=np.int16), rate


@pytest.mark.integration
@pytest.mark.slow
def test_silence_5s_returns_tyishina() -> None:
    """Silence fixture should transcribe to '(тишина)'."""
    path = FIXTURES_DIR / "silence_5s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")
    segments = transcriber.transcribe(audio, sample_rate=rate)
    transcript = " ".join(s.text for s in segments if s.text).strip() or TYISHINA
    assert transcript == TYISHINA


@pytest.mark.integration
@pytest.mark.slow
def test_clean_5s_silence_returns_tyishina() -> None:
    """clean_5s.wav (silence) should transcribe to '(тишина)'."""
    path = FIXTURES_DIR / "clean_5s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")
    segments = transcriber.transcribe(audio, sample_rate=rate)
    transcript = " ".join(s.text for s in segments if s.text).strip() or TYISHINA
    assert transcript == TYISHINA


@pytest.mark.integration
@pytest.mark.slow
def test_clean_30s_silence_returns_tyishina() -> None:
    """clean_30s.wav (silence) should transcribe to '(тишина)'."""
    path = FIXTURES_DIR / "clean_30s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")
    segments = transcriber.transcribe(audio, sample_rate=rate)
    transcript = " ".join(s.text for s in segments if s.text).strip() or TYISHINA
    assert transcript == TYISHINA


@pytest.mark.integration
@pytest.mark.slow
def test_transcribe_returns_segments_with_fields() -> None:
    """Transcribe returns list of Segment with start, end, text, language, confidence."""
    path = FIXTURES_DIR / "silence_5s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")
    segments = transcriber.transcribe(audio, sample_rate=rate)
    for s in segments:
        assert hasattr(s, "start")
        assert hasattr(s, "end")
        assert hasattr(s, "text")
        assert hasattr(s, "language")
        assert hasattr(s, "confidence")
