"""W8: Settings field validators (ollama_model, ring_seconds, pyannote_restart_hours)."""

from __future__ import annotations

import pytest


def test_settings_defaults_load() -> None:
    """Default Settings load without error."""
    from voiceforge.core.config import Settings

    cfg = Settings()
    assert cfg.ollama_model == "phi3:mini"
    assert cfg.ring_seconds == 300.0
    assert cfg.pyannote_restart_hours == 2


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
