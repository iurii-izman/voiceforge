"""Tests for core.metrics: get_cost_today, get_stats, get_stats_range, log_response_cache. #56"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

import voiceforge.core.metrics as metrics


def test_get_cost_today_empty(tmp_path, monkeypatch) -> None:
    """get_cost_today returns 0 when no data."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    assert metrics.get_cost_today() == 0.0


def test_log_llm_call_and_get_cost_today(tmp_path, monkeypatch) -> None:
    """log_llm_call inserts row; get_cost_today sums today's cost."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    metrics.log_llm_call("test/model", 10, 20, 0.05, success=True)
    assert metrics.get_cost_today() == pytest.approx(0.05)


def test_log_response_cache(tmp_path, monkeypatch) -> None:
    """log_response_cache writes to response_cache_log."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    metrics.log_response_cache(True)
    metrics.log_response_cache(False)
    db_path = tmp_path / "data" / "voiceforge" / "metrics.db"
    assert db_path.exists()
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT hit FROM response_cache_log ORDER BY timestamp").fetchall()
        assert [r[0] for r in rows] == [1, 0]
    finally:
        conn.close()


def test_get_stats_empty(tmp_path, monkeypatch) -> None:
    """get_stats returns structure with empty by_model/by_day when no data."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    out = metrics.get_stats(days=30)
    assert "by_model" in out
    assert "by_day" in out
    assert out["total_cost_usd"] == 0.0
    assert out["total_calls"] == 0
    assert out["response_cache_hits"] == 0
    assert out["response_cache_misses"] == 0


def test_get_stats_with_data(tmp_path, monkeypatch) -> None:
    """get_stats returns by_model and by_day when data exists."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    ts = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    metrics.log_llm_call("m1", 100, 50, 0.01, success=True)
    out = metrics.get_stats(days=7)
    assert out["total_calls"] >= 1
    assert out["total_cost_usd"] >= 0.01
    assert any(e.get("model") == "m1" for e in out["by_model"])


def test_get_stats_range(tmp_path, monkeypatch) -> None:
    """get_stats_range returns same structure for date range."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    from_date = date.today() - timedelta(days=5)
    to_date = date.today()
    out = metrics.get_stats_range(from_date, to_date)
    assert "by_model" in out
    assert "by_day" in out
    assert "total_cost_usd" in out
    assert "response_cache_hit_rate" in out


def test_unpack_llm_row_and_make_entry() -> None:
    """_unpack_llm_row and _make_by_model_entry handle cache columns."""
    row = ("model-x", 10, 20, 0.1, 100.0, 1, 5, 0)
    unpacked = metrics._unpack_llm_row(row, True, "test")
    assert unpacked is not None
    entry = metrics._make_by_model_entry(unpacked, True)
    assert entry["model"] == "model-x"
    assert entry["cost_usd"] == 0.1
    assert entry["cache_read_input_tokens"] == 5


def test_unpack_llm_row_without_cache_cols() -> None:
    """_unpack_llm_row works with 6-tuple (no cache columns)."""
    row = ("model-y", 5, 15, 0.05, 50.0, 2)
    unpacked = metrics._unpack_llm_row(row, False, "test")
    assert unpacked is not None
    entry = metrics._make_by_model_entry(unpacked, False)
    assert entry["model"] == "model-y"
    assert "cache_read_input_tokens" not in entry
