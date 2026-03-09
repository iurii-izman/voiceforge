"""E12 #135: Mock-only tests for stt.diarizer to allow removing from coverage omit."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceforge.stt.diarizer import WINDOW_SEC, Diarizer, DiarSegment


@pytest.fixture
def mock_pipeline():
    """Fake pyannote Pipeline that returns one segment per window."""
    pipe = MagicMock()
    # pyannote returns iterable of (segment, _, label); segment has .start, .end
    seg = MagicMock()
    seg.start = 0.0
    seg.end = min(5.0, WINDOW_SEC)
    pipe.return_value.itertracks = lambda yield_label: [(seg, None, "SPEAKER_00")]
    return pipe


def test_diarizer_diarize_returns_segments_with_mock_pipeline(mock_pipeline) -> None:
    """Diarizer.diarize returns list of DiarSegment when Pipeline is mocked."""
    with patch("voiceforge.stt.diarizer.Pipeline") as p:
        p.from_pretrained.return_value = mock_pipeline
        with patch("voiceforge.stt.diarizer.psutil") as psutil_mod:
            psutil_mod.Process.return_value.memory_info.return_value.rss = 1024 * 1024  # 1 MB
            d = Diarizer(auth_token="test-token")
            # Short audio: 1s at 16kHz
            audio = np.zeros(16000, dtype=np.float32)
            out = d.diarize(audio, sample_rate=16000)
    assert isinstance(out, list)
    assert all(isinstance(s, DiarSegment) for s in out)
    assert all(hasattr(s, "start") and hasattr(s, "end") and hasattr(s, "speaker") for s in out)


def test_diarizer_diarize_accepts_int16(mock_pipeline) -> None:
    """Diarizer.diarize accepts int16 audio (converts to float32)."""
    with patch("voiceforge.stt.diarizer.Pipeline") as p:
        p.from_pretrained.return_value = mock_pipeline
        with patch("voiceforge.stt.diarizer.psutil") as psutil_mod:
            psutil_mod.Process.return_value.memory_info.return_value.rss = 1024 * 1024
            d = Diarizer(auth_token="x")
            audio = np.zeros(16000, dtype=np.int16)
            out = d.diarize(audio, sample_rate=16000)
    assert isinstance(out, list)
