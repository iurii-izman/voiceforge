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


def test_cli_service_install_uninstall_smoke(monkeypatch, tmp_path) -> None:
    service_src = tmp_path / "voiceforge.service"
    service_src.write_text("[Unit]\nDescription=voiceforge test service\n")

    monkeypatch.setenv("VOICEFORGE_SERVICE_FILE", str(service_src))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    calls: list[list[str]] = []

    def fake_subprocess_run(cmd: list[str], check: bool = True) -> types.SimpleNamespace:
        calls.append(cmd)
        assert check is True
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(main_mod.subprocess, "run", fake_subprocess_run)

    install_result = runner.invoke(main_mod.app, ["install-service"])
    assert install_result.exit_code == 0, install_result.stdout
    installed = tmp_path / "config" / "systemd" / "user" / "voiceforge.service"
    assert installed.exists()

    uninstall_result = runner.invoke(main_mod.app, ["uninstall-service"])
    assert uninstall_result.exit_code == 0, uninstall_result.stdout

    assert calls == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", "voiceforge.service"],
        ["systemctl", "--user", "disable", "--now", "voiceforge.service"],
    ]


def test_cli_index_watch_smoke_with_mocks(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "note.txt").write_text("hello world")
    (kb_dir / "readme.md").write_text("# title")

    records: dict[str, object] = {
        "indexer_init": [],
        "add_file": [],
        "prune_args": None,
        "watcher_init": None,
        "watch_run": False,
        "watch_stop": False,
    }

    class _FakeKnowledgeIndexer:
        def __init__(self, db_path: str) -> None:
            records["indexer_init"].append(db_path)  # type: ignore[union-attr]

        def add_file(self, path) -> int:
            records["add_file"].append(str(path))  # type: ignore[union-attr]
            return 2

        def prune_sources_not_in(self, keep_sources: set[str], only_under_prefix: str | None = None) -> int:
            records["prune_args"] = (keep_sources, only_under_prefix)
            return 1

        def close(self) -> None:
            return None

    class _FakeKBWatcher:
        def __init__(self, watch_dir, db_path) -> None:
            records["watcher_init"] = (str(watch_dir), str(db_path))

        def run(self) -> None:
            records["watch_run"] = True

        def stop(self) -> None:
            records["watch_stop"] = True

    fake_indexer_module = types.ModuleType("voiceforge.rag.indexer")
    fake_indexer_module.KnowledgeIndexer = _FakeKnowledgeIndexer
    monkeypatch.setitem(sys.modules, "voiceforge.rag.indexer", fake_indexer_module)

    fake_watcher_module = types.ModuleType("voiceforge.rag.watcher")
    fake_watcher_module.KBWatcher = _FakeKBWatcher
    monkeypatch.setitem(sys.modules, "voiceforge.rag.watcher", fake_watcher_module)

    index_file_result = runner.invoke(main_mod.app, ["index", str(kb_dir / "note.txt")])
    assert index_file_result.exit_code == 0, index_file_result.stdout
    assert "Добавлено чанков: 2" in index_file_result.stdout

    index_dir_result = runner.invoke(main_mod.app, ["index", str(kb_dir)])
    assert index_dir_result.exit_code == 0, index_dir_result.stdout
    assert "Удалено чанков (файлы удалены): 1" in index_dir_result.stdout
    assert "Добавлено чанков: 4" in index_dir_result.stdout

    watch_result = runner.invoke(main_mod.app, ["watch", str(kb_dir)])
    assert watch_result.exit_code == 0, watch_result.stdout
    assert "VoiceForge watch:" in watch_result.stdout

    assert records["watch_run"] is True
    assert records["watcher_init"] is not None
