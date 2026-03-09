# E16 #139: Shared fixtures. Mock PipeWire (pw-record) for CI — no real audio.
"""Pytest fixtures. mock_pw_record_silence: fake pw-record subprocess returning silence PCM."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest


def raise_when_called(exc: BaseException):
    """Return a callable that raises exc when called. Replaces (x for x in ()).throw(exc) for Sonar S7500."""

    def _inner(*args: object, **kwargs: object) -> None:
        raise exc

    return _inner


@pytest.fixture
def mock_pw_record_silence():
    """Mock pw-record subprocess: stdout yields silence PCM (s16le 16kHz mono). Reusable in CI."""
    # 0.5s silence: 16000 samples/s * 2 bytes * 0.5s
    silence_bytes = b"\x00\x00" * (16000 * 1 * 1 // 2)
    fake_stdout = io.BytesIO(silence_bytes)
    fake_proc = MagicMock()
    fake_proc.stdout = fake_stdout
    fake_proc.poll.return_value = None

    with patch("voiceforge.audio.capture.subprocess.Popen", return_value=fake_proc) as popen:
        yield popen
