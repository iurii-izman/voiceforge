from __future__ import annotations

import json

from typer.testing import CliRunner

from voiceforge.main import app

runner = CliRunner()


def _last_json_line(stdout: str) -> dict:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"No JSON payload found in output: {stdout}")


def test_status_json_contract(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    result = runner.invoke(app, ["status", "--output", "json"])
    assert result.exit_code == 0, result.stdout
    payload = _last_json_line(result.stdout)
    assert payload["ok"] is True
    assert payload["schema_version"] == "1.0"
    data = payload["data"]
    assert "ram" in data
    assert "cost_today_usd" in data
    assert "ollama_available" in data


def test_history_empty_json(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    result = runner.invoke(app, ["history", "--output", "json"])
    assert result.exit_code == 0, result.stdout
    payload = _last_json_line(result.stdout)
    assert payload["ok"] is True
    assert payload["data"] == {"sessions": []}
