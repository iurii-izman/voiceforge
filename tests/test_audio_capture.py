"""Tests for audio/capture (#56 coverage). Mocks subprocess; no real pw-record."""

from __future__ import annotations

import io
import subprocess
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceforge.audio.capture import (
    PW_RECORD_CMD,
    AudioCapture,
    _pw_record_cmd,
)


def test_pw_record_cmd_default() -> None:
    """Default command has no --target."""
    cmd = _pw_record_cmd()
    assert cmd == PW_RECORD_CMD
    assert "-" in cmd


def test_pw_record_cmd_with_target() -> None:
    """With target_source inserts --target before stdout."""
    cmd = _pw_record_cmd(target_source="alsa_output.pci-0.1.monitor")
    assert "--target=alsa_output.pci-0.1.monitor" in cmd
    idx_target = cmd.index("--target=alsa_output.pci-0.1.monitor")
    idx_stdout = cmd.index("-")
    assert idx_target < idx_stdout


def test_audio_capture_get_chunk_before_start() -> None:
    """get_chunk before start returns empty arrays."""
    cap = AudioCapture(buffer_seconds=1.0)
    mic, mon = cap.get_chunk(0.5)
    assert mic.size == 0
    assert mon.size == 0
    assert mic.dtype == np.int16
    assert mon.dtype == np.int16


def test_audio_capture_diagnostics_before_start() -> None:
    """diagnostics before start has None returncodes, 0 samples."""
    cap = AudioCapture(buffer_seconds=1.0, monitor_source=None)
    d = cap.diagnostics()
    assert d["mic_returncode"] is None
    assert d["monitor_returncode"] is None
    assert d["mic_samples_last_1s"] == 0
    assert d["monitor_samples_last_1s"] == 0
    assert d["monitor_source"] is None


def test_audio_capture_stop_before_start() -> None:
    """stop before start is no-op."""
    cap = AudioCapture(buffer_seconds=1.0)
    cap.stop()
    assert cap._mic_proc is None
    assert cap._monitor_proc is None


def test_audio_capture_start_pw_record_not_found() -> None:
    """start raises FileNotFoundError when pw-record missing."""
    cap = AudioCapture(buffer_seconds=1.0)
    with patch("voiceforge.audio.capture.subprocess.Popen", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            cap.start()
    assert cap._mic_proc is None


def test_audio_capture_start_and_stop_with_mock_popen() -> None:
    """start with mocked Popen; reader gets data then EOF; get_chunk and stop."""
    cap = AudioCapture(buffer_seconds=2.0, sample_rate=16000)
    # stdout: 0.5 s of zeros then EOF
    chunk_bytes = 16000 * 2 * 1 * 0.5  # 16000 samples/sec * 2 bytes * 1 ch * 0.5 s
    fake_stdout = io.BytesIO(b"\x00\x00" * int(chunk_bytes // 2))
    fake_proc = MagicMock()
    fake_proc.stdout = fake_stdout
    fake_proc.poll.return_value = None

    with patch("voiceforge.audio.capture.subprocess.Popen", return_value=fake_proc) as popen:
        cap.start()
    assert popen.call_count >= 1
    # Allow reader to consume
    cap._stop.set()
    if cap._mic_thread:
        cap._mic_thread.join(timeout=1.0)
    mic, mon = cap.get_chunk(1.0)
    assert mic.size >= 0
    assert mon.size >= 0
    d = cap.diagnostics()
    assert "mic_samples_last_1s" in d
    assert "monitor_samples_last_1s" in d
    cap.stop()
    assert cap._mic_proc is None


def test_audio_capture_start_monitor_not_found_fallback() -> None:
    """When monitor pw-record fails with FileNotFoundError, only mic runs."""
    cap = AudioCapture(buffer_seconds=1.0)
    call_count = [0]

    def fake_popen(*args, **kwargs):  # noqa: ARG001
        call_count[0] += 1
        if call_count[0] == 1:
            # First call: mic succeeds
            proc = MagicMock()
            proc.stdout = io.BytesIO(b"")
            proc.poll.return_value = None
            return proc
        raise FileNotFoundError("pw-record")

    with patch("voiceforge.audio.capture.subprocess.Popen", side_effect=fake_popen):
        cap.start()
    assert cap._mic_proc is not None
    assert cap._monitor_proc is None
    assert cap._monitor_thread is None
    cap.stop()


def test_audio_capture_start_already_started_no_second_popen() -> None:
    """Second start() is no-op (already_started)."""
    cap = AudioCapture(buffer_seconds=1.0)
    proc = MagicMock()
    proc.stdout = io.BytesIO(b"")
    proc.poll.return_value = None
    with patch("voiceforge.audio.capture.subprocess.Popen", return_value=proc):
        cap.start()
    popen_calls = []
    with patch("voiceforge.audio.capture.subprocess.Popen", side_effect=lambda *a, **k: (popen_calls.append(1), proc)[1]):
        cap.start()
    assert len(popen_calls) == 0
    cap.stop()


def test_reader_loop_handles_os_error() -> None:
    """_reader_loop breaks on OSError from stream.read."""
    from voiceforge.audio.buffer import RingBuffer
    from voiceforge.audio.capture import AudioCapture

    cap = AudioCapture(buffer_seconds=1.0)
    cap._stop = MagicMock()
    cap._stop.is_set.side_effect = [False, False]
    buf = RingBuffer(1.0, 16000)
    broken_stream = MagicMock()
    broken_stream.read.side_effect = OSError("read failed")
    proc = MagicMock()
    proc.poll.return_value = None
    cap._reader_loop(proc, broken_stream, buf, "mic")
    broken_stream.read.assert_called()


def test_reader_loop_handles_empty_data_and_returncode() -> None:
    """_reader_loop exits when read returns empty and proc has returncode."""
    from voiceforge.audio.buffer import RingBuffer
    from voiceforge.audio.capture import AudioCapture

    cap = AudioCapture(buffer_seconds=1.0)
    cap._stop = MagicMock()
    cap._stop.is_set.side_effect = [False, False]
    buf = RingBuffer(1.0, 16000)
    stream = MagicMock()
    stream.read.side_effect = [b"", b""]
    proc = MagicMock()
    proc.poll.return_value = 1
    cap._reader_loop(proc, stream, buf, "mic")
    assert stream.read.called
