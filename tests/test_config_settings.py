"""W8: Settings field validators (ollama_model, ring_seconds, pyannote_restart_hours)."""

from __future__ import annotations

import pytest


def test_settings_defaults_load() -> None:
    """Default Settings load without error."""
    from voiceforge.core.config import Settings

    cfg = Settings()
    assert cfg.ollama_model == "phi3:mini"
    assert cfg.ring_seconds == pytest.approx(300.0)
    assert cfg.pyannote_restart_hours == 2
    assert cfg.live_summary_interval_sec == 90
    assert cfg.daily_budget_limit_usd == pytest.approx(75.0 / 30.0)
    assert cfg.calendar_context_enabled is False


def test_settings_ollama_model_empty_raises() -> None:
    """Empty ollama_model raises ValueError."""
    from voiceforge.core.config import Settings

    with pytest.raises(ValueError, match="ollama_model must be non-empty"):
        Settings(ollama_model="")


def test_settings_ring_seconds_non_positive_raises() -> None:
    """Non-positive ring_seconds raises ValueError."""
    from voiceforge.core.config import Settings

    with pytest.raises(ValueError, match="ring_seconds must be positive"):
        Settings(ring_seconds=0)
    with pytest.raises(ValueError, match="ring_seconds must be positive"):
        Settings(ring_seconds=-1)


def test_settings_pyannote_restart_hours_below_one_raises() -> None:
    """pyannote_restart_hours < 1 raises ValueError."""
    from voiceforge.core.config import Settings

    with pytest.raises(ValueError, match="pyannote_restart_hours must be >= 1"):
        Settings(pyannote_restart_hours=0)


def test_settings_live_summary_interval_below_one_raises() -> None:
    """live_summary_interval_sec < 1 raises ValueError."""
    from voiceforge.core.config import Settings

    with pytest.raises(ValueError, match="live_summary_interval_sec must be >= 1"):
        Settings(live_summary_interval_sec=0)


def test_settings_daily_budget_limit_default_from_monthly() -> None:
    """daily_budget_limit_usd defaults to budget_limit_usd/30 when not set (#38)."""
    from voiceforge.core.config import Settings

    cfg = Settings()
    assert cfg.daily_budget_limit_usd == pytest.approx(75.0 / 30.0)
    cfg_custom = Settings(budget_limit_usd=60.0)
    assert cfg_custom.daily_budget_limit_usd == pytest.approx(2.0)


def test_settings_daily_budget_limit_negative_raises() -> None:
    """daily_budget_limit_usd < 0 raises ValueError (#38)."""
    from voiceforge.core.config import Settings

    with pytest.raises(ValueError, match="daily_budget_limit_usd must be >= 0"):
        Settings(daily_budget_limit_usd=-1.0)


def test_config_get_data_dir_and_paths(monkeypatch, tmp_path) -> None:
    """get_data_dir, get_ring_file_path, get_rag_db_path respect env and defaults (#56)."""
    from voiceforge.core.config import Settings

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    cfg = Settings()
    data_dir = cfg.get_data_dir()
    assert "voiceforge" in data_dir
    assert str(tmp_path / "data") in data_dir
    ring_path = cfg.get_ring_file_path()
    assert "ring" in ring_path or "voiceforge" in ring_path
    rag_path = cfg.get_rag_db_path()
    assert "rag" in rag_path
    assert data_dir in rag_path
