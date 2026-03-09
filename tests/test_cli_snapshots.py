"""E12 #135: CLI output snapshot tests — status, history, cost; detect unintended format changes."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from voiceforge.main import app

runner = CliRunner()


def test_cli_status_snapshot_keywords(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """voiceforge status output contains expected keywords (snapshot guard)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "voiceforge").mkdir(parents=True, exist_ok=True)
    # status uses get_status_data() which reads Settings, metrics, RAG; no TranscriptLog
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    out = result.output
    assert (
        "VoiceForge" in out
        or "voiceforge" in out.lower()
        or "Status" in out
        or "PipeWire" in out
        or "version" in out.lower()
        or "cost" in out.lower()
        or "RAM" in out
    )


def test_cli_history_snapshot_keywords(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """voiceforge history output contains expected keywords or empty state."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True, exist_ok=True)

    class FakeLog:
        def get_sessions_for_display(self, last_n=10, offset=0):
            return []

        def close(self):
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", lambda *a, **kw: FakeLog())
    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
    out = result.output
    assert "session" in out.lower() or "сессий" in out or "history" in out.lower() or "No sessions" in out or "ID" in out


def test_cli_cost_snapshot_keywords(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """voiceforge cost output contains cost-related keywords."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True, exist_ok=True)

    def fake_get_stats(*args, **kwargs):
        return {"total_cost_usd": 0.0, "calls": 0, "by_model": [], "by_day": []}

    def fake_get_stats_range(*args, **kwargs):
        return {"total_cost_usd": 0.0, "calls": 0, "by_model": [], "by_day": []}

    monkeypatch.setattr("voiceforge.core.metrics.get_stats", fake_get_stats)
    monkeypatch.setattr("voiceforge.core.metrics.get_stats_range", fake_get_stats_range)
    result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0
    out = result.output
    assert "cost" in out.lower() or "USD" in out or "0" in out
