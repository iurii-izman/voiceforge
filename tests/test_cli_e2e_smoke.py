from __future__ import annotations

import json
import sys
import types

import numpy as np
from typer.testing import CliRunner

import voiceforge.main as main_mod

runner = CliRunner()


def _last_json_line(stdout: str) -> dict:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"No JSON payload found in output: {stdout}")


class _FakeAudioCapture:
    def __init__(self, sample_rate: int, buffer_seconds: float, monitor_source: str | None) -> None:
        self.sample_rate = sample_rate
        self.buffer_seconds = buffer_seconds
        self.monitor_source = monitor_source

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def get_chunk(self, seconds: float) -> tuple[np.ndarray, np.ndarray]:
        data = np.zeros(int(max(16, seconds)), dtype=np.int16)
        return data, data


def test_cli_pipeline_listen_analyze_history(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    fake_capture_module = types.ModuleType("voiceforge.audio.capture")
    fake_capture_module.AudioCapture = _FakeAudioCapture
    monkeypatch.setitem(sys.modules, "voiceforge.audio.capture", fake_capture_module)

    ticks = iter([0.0, 2.0])
    monkeypatch.setattr(main_mod.time, "monotonic", lambda: next(ticks, 2.0))
    monkeypatch.setattr(main_mod.time, "sleep", lambda _seconds: None)

    listen_result = runner.invoke(main_mod.app, ["listen", "--duration", "1"])
    assert listen_result.exit_code == 0, listen_result.stdout

    def fake_pipeline(seconds: int) -> tuple[str, list[dict[str, object]], dict[str, object]]:
        return (
            f"analysis-ok-{seconds}",
            [{"start_sec": 0.0, "end_sec": 1.0, "speaker": "S1", "text": "hello"}],
            {
                "model": "anthropic/claude-haiku-4-5",
                "questions": ["q1"],
                "answers": ["a1"],
                "recommendations": ["r1"],
                "action_items": [{"description": "do x", "assignee": "A"}],
                "cost_usd": 0.0,
            },
        )

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", fake_pipeline)

    analyze_result = runner.invoke(main_mod.app, ["analyze", "--seconds", "15", "--output", "json"])
    assert analyze_result.exit_code == 0, analyze_result.stdout
    analyze_payload = _last_json_line(analyze_result.stdout)
    assert analyze_payload["ok"] is True
    session_id = analyze_payload["data"]["session_id"]
    assert isinstance(session_id, int)

    history_result = runner.invoke(main_mod.app, ["history", "--last", "10", "--output", "json"])
    assert history_result.exit_code == 0, history_result.stdout
    history_payload = _last_json_line(history_result.stdout)
    sessions = history_payload["data"]["sessions"]
    assert sessions
    assert sessions[0]["id"] == session_id

    detail_result = runner.invoke(main_mod.app, ["history", "--id", str(session_id), "--output", "json"])
    assert detail_result.exit_code == 0, detail_result.stdout
    detail_payload = _last_json_line(detail_result.stdout)
    assert detail_payload["ok"] is True
    assert detail_payload["data"]["session_id"] == session_id
    assert detail_payload["data"]["segments"]
