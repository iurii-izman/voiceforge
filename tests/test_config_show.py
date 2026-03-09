"""E14 (#137): Tests for voiceforge config show and get_effective_config_and_overrides."""

from __future__ import annotations

import json


def test_get_effective_config_and_overrides_returns_dict_and_set() -> None:
    """get_effective_config_and_overrides returns (config_dict, overridden_keys)."""
    from voiceforge.core.config import get_effective_config_and_overrides

    config_dict, overridden = get_effective_config_and_overrides()
    assert isinstance(config_dict, dict)
    assert isinstance(overridden, set)
    assert "model_size" in config_dict
    assert "default_llm" in config_dict
    assert "budget_limit_usd" in config_dict


def test_config_show_json_invocation(tmp_path, monkeypatch) -> None:
    """voiceforge config show --json outputs valid JSON with config and overridden."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    from typer.testing import CliRunner

    from voiceforge.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["config", "show", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "config" in data
    assert "overridden" in data
    assert isinstance(data["overridden"], list)
    assert "model_size" in data["config"]


def test_config_show_text_invocation(tmp_path, monkeypatch) -> None:
    """voiceforge config show (no --json) prints table (no crash)."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    from typer.testing import CliRunner

    from voiceforge.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "model_size" in result.output or "key" in result.output.lower()
