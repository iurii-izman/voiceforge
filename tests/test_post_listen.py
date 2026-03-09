"""Tests for post-listen auto-analyze and prompt (E9 #132)."""

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


def test_listen_help_exposes_auto_analyze() -> None:
    """Listen --help shows --auto-analyze flag."""
    result = runner.invoke(main_mod.app, ["listen", "--help"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "--auto-analyze" in result.stdout or "auto-analyze" in result.stdout


def test_listen_auto_analyze_runs_pipeline_on_stop(monkeypatch, tmp_path) -> None:
    """With --auto-analyze, on Ctrl+C analyze is run on full buffer without prompting."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    (tmp_path / "runtime" / "voiceforge").mkdir(parents=True, exist_ok=True)
    ring_path = tmp_path / "runtime" / "voiceforge" / "ring.raw"
    ring_path.write_bytes(b"\x00\x00" * 32000)

    monkeypatch.setattr("voiceforge.audio.capture.AudioCapture", _FakeCapture)

    handler_holder: list[object] = []

    def capture_signal(sig: int, h: object) -> None:
        handler_holder.append(h)

    monkeypatch.setattr("voiceforge.main.signal.signal", capture_signal)

    pipeline_called: list[tuple[int, str | None]] = []

    def track_pipeline(seconds: int, template: str | None = None, dry_run: bool = False) -> tuple[str, list, dict]:
        pipeline_called.append((seconds, template))
        return ("ok", [], {"model": "x", "cost_usd": 0.0})

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", track_pipeline)

    def run_in_thread() -> None:
        time.sleep(0.2)
        if handler_holder and callable(handler_holder[0]):
            handler_holder[0]()

    t = threading.Thread(target=run_in_thread, daemon=True)
    t.start()

    result = runner.invoke(main_mod.app, ["listen", "--auto-analyze"], catch_exceptions=False, input="")
    t.join(timeout=2.0)

    assert result.exit_code == 0, result.stdout + result.stderr
    assert len(pipeline_called) == 1, "run_analyze_pipeline should be called once"
    assert pipeline_called[0][1] is None, "template should be None for listen post-analyze"
    assert "ok" in result.stdout or "session_id=" in result.stdout
