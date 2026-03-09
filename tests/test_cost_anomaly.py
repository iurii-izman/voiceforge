"""Tests for observability cost anomaly and data dir free. E15 #138."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import voiceforge.core.observability as obs


def test_update_cost_anomaly_no_anomaly(monkeypatch: pytest.MonkeyPatch) -> None:
    """When today <= multiplier × 7-day avg, llm_cost_anomaly is 0."""
    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 1.0)
    monkeypatch.setattr("voiceforge.core.metrics.get_stats", lambda days: {"total_cost_usd": 7.0})
    settings = MagicMock()
    settings.cost_anomaly_multiplier = 2.0
    monkeypatch.setattr("voiceforge.core.config.Settings", lambda: settings)

    obs.update_cost_anomaly()
    # avg_7 = 1.0, threshold = 2.0, today = 1.0 -> no anomaly
    assert obs.llm_cost_anomaly._value.get() == pytest.approx(0.0)


def test_update_cost_anomaly_detects_anomaly(monkeypatch: pytest.MonkeyPatch) -> None:
    """When today > multiplier × 7-day avg, llm_cost_anomaly is 1."""
    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 10.0)
    monkeypatch.setattr("voiceforge.core.metrics.get_stats", lambda days: {"total_cost_usd": 7.0})
    settings = MagicMock()
    settings.cost_anomaly_multiplier = 2.0
    monkeypatch.setattr("voiceforge.core.config.Settings", lambda: settings)

    obs.update_cost_anomaly()
    # avg_7 = 1.0, threshold = 2.0, today = 10.0 -> anomaly
    assert obs.llm_cost_anomaly._value.get() == pytest.approx(1.0)


def test_update_cost_anomaly_zero_avg_no_anomaly(monkeypatch: pytest.MonkeyPatch) -> None:
    """When 7-day avg is 0, no anomaly (avoid div by zero)."""
    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 5.0)
    monkeypatch.setattr("voiceforge.core.metrics.get_stats", lambda days: {"total_cost_usd": 0.0})
    settings = MagicMock()
    settings.cost_anomaly_multiplier = 2.0
    monkeypatch.setattr("voiceforge.core.config.Settings", lambda: settings)

    obs.update_cost_anomaly()
    assert obs.llm_cost_anomaly._value.get() == pytest.approx(0.0)


def test_update_data_dir_free_bytes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """update_data_dir_free_bytes sets gauge to positive when dir exists."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True)
    obs.update_data_dir_free_bytes()
    assert obs.data_dir_free_bytes._value.get() >= 0.0
