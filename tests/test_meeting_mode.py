"""Tests for one-shot meeting mode: voiceforge meeting (E2 #125)."""

from __future__ import annotations

import threading
import time

import numpy as np
from typer.testing import CliRunner

import voiceforge.main as main_mod

runner = CliRunner()


class _FakeCapture:
    """Minimal AudioCapture that returns empty chunks and obeys stop."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        # Empty: test fake (S1186).
        pass

    def start(self) -> None:
        # Empty: test fake (S1186).
        pass

    def stop(self) -> None:
        # Empty: test fake (S1186).
        pass

    def get_chunk(self, seconds: float) -> tuple[np.ndarray, np.ndarray]:
        arr = np.zeros(0, dtype=np.int16)
        return arr, arr


class _FakeCaptureWithAudio:
    """Capture fake that always has audio available for final snapshot persistence."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def get_chunk(self, seconds: float) -> tuple[np.ndarray, np.ndarray]:
        mic = np.ones(16000, dtype=np.int16)
        mon = np.zeros(0, dtype=np.int16)
        return mic, mon


def test_meeting_help_exposes_command() -> None:
    """Meeting command is in CLI and --help shows template, no-analyze, seconds."""
    result = runner.invoke(main_mod.app, ["meeting", "--help"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "One-shot meeting" in result.stdout or "meeting" in result.stdout
    assert "--template" in result.stdout
    assert "--no-analyze" in result.stdout
    assert "--seconds" in result.stdout


def test_meeting_unknown_template_exits_nonzero() -> None:
    """Meeting with unknown --template exits with error."""
    result = runner.invoke(main_mod.app, ["meeting", "--template", "unknown_template"])
    assert result.exit_code != 0
    assert "Unknown template" in result.stderr or "unknown_template" in result.stderr


def test_meeting_no_analyze_returns_without_pipeline(monkeypatch, tmp_path) -> None:
    """run_meeting with --no-analyze stops after capture; run_analyze_pipeline not called."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    monkeypatch.setattr("voiceforge.audio.capture.AudioCapture", _FakeCapture)

    handler_holder: list[object] = []

    def capture_signal(sig: int, h: object) -> None:
        handler_holder.append(h)

    monkeypatch.setattr("voiceforge.cli.meeting.signal.signal", capture_signal)

    pipeline_called: list[bool] = []

    def track_pipeline(*args: object, **kwargs: object) -> tuple[str, list, dict]:
        pipeline_called.append(True)
        return ("ok", [], {"model": "x", "cost_usd": 0.0})

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", track_pipeline)

    def run_in_thread() -> None:
        time.sleep(0.15)
        if handler_holder and callable(handler_holder[0]):
            handler_holder[0]()

    t = threading.Thread(target=run_in_thread, daemon=True)
    t.start()

    result = runner.invoke(main_mod.app, ["meeting", "--no-analyze"], catch_exceptions=False)
    t.join(timeout=1.0)

    assert result.exit_code == 0, result.stdout + result.stderr
    assert not pipeline_called, "run_analyze_pipeline should not be called when --no-analyze"


def test_meeting_analyze_on_exit_calls_pipeline(monkeypatch, tmp_path) -> None:
    """run_meeting without --no-analyze runs analyze on exit and echoes result."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    (tmp_path / "runtime" / "voiceforge").mkdir(parents=True, exist_ok=True)
    ring = tmp_path / "runtime" / "voiceforge" / "ring.raw"
    ring.write_bytes(b"\x00\x00" * 32000)

    monkeypatch.setattr("voiceforge.audio.capture.AudioCapture", _FakeCapture)

    handler_holder: list[object] = []

    def capture_signal(sig: int, h: object) -> None:
        handler_holder.append(h)

    monkeypatch.setattr("voiceforge.cli.meeting.signal.signal", capture_signal)

    def fake_pipeline(seconds: int, template: str | None = None) -> tuple[str, list, dict]:
        return (
            "Summary: test",
            [{"start_sec": 0, "end_sec": 1, "speaker": "S1", "text": "hi"}],
            {"model": "test", "cost_usd": 0.0},
        )

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", fake_pipeline)

    logged: dict[str, object] = {}

    class FakeLogDb:
        def log_session(self, **kwargs: object) -> int:
            logged.update(kwargs)
            return 99

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)

    def run_in_thread() -> None:
        time.sleep(0.15)
        if handler_holder and callable(handler_holder[0]):
            handler_holder[0]()

    t = threading.Thread(target=run_in_thread, daemon=True)
    t.start()

    result = runner.invoke(main_mod.app, ["meeting"], catch_exceptions=False)
    t.join(timeout=2.0)

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Summary: test" in result.stdout
    assert "session_id=99" in result.stdout or "99" in result.stdout
    assert logged.get("duration_sec") is not None


def test_meeting_final_flush_persists_ring_before_analyze(monkeypatch, tmp_path) -> None:
    """Meeting should persist a final ring snapshot so quick stop still analyzes without prior listen."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr("voiceforge.audio.capture.AudioCapture", _FakeCaptureWithAudio)

    handler_holder: list[object] = []

    def capture_signal(sig: int, h: object) -> None:
        handler_holder.append(h)

    monkeypatch.setattr("voiceforge.cli.meeting.signal.signal", capture_signal)

    observed_ring: dict[str, object] = {}

    def fake_pipeline(seconds: int, template: str | None = None) -> tuple[str, list, dict]:
        ring = tmp_path / "runtime" / "voiceforge" / "ring.raw"
        observed_ring["exists"] = ring.exists()
        observed_ring["size"] = ring.stat().st_size if ring.exists() else 0
        return ("Summary: flushed", [], {"model": "test", "cost_usd": 0.0})

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", fake_pipeline)

    class FakeLogDb:
        def log_session(self, **kwargs: object) -> int:
            return 1

        def close(self) -> None:
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)

    def run_in_thread() -> None:
        time.sleep(0.15)
        if handler_holder and callable(handler_holder[0]):
            handler_holder[0]()

    t = threading.Thread(target=run_in_thread, daemon=True)
    t.start()

    result = runner.invoke(main_mod.app, ["meeting"], catch_exceptions=False)
    t.join(timeout=2.0)

    assert result.exit_code == 0, result.stdout + result.stderr
    assert observed_ring.get("exists") is True
    assert int(observed_ring.get("size", 0)) > 0
    assert "Summary: flushed" in result.stdout
