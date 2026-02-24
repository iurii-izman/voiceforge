"""LLM call metrics: structlog + SQLite (llm_calls). Budget limit from Settings when needed."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import structlog

log = structlog.get_logger()

TABLE_DDL = """
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    latency_ms INTEGER NOT NULL,
    success INTEGER NOT NULL,
    cache_read_input_tokens INTEGER,
    cache_creation_input_tokens INTEGER
);
"""

_init_done_paths: set[str] = set()
_init_lock = threading.Lock()


def _metrics_db_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge" / "metrics.db"


def _cost_file_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge" / "cost_daily.json"


def _run_migrations(conn: sqlite3.Connection) -> None:
    """One-time schema bootstrap and migrations. Idempotent DDL."""
    conn.execute(TABLE_DDL)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
    """)
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES ('001_initial', ?)",
        (datetime.now(UTC).isoformat(),),
    )
    conn.commit()
    # Keep SQL static here to avoid injection-prone string formatting patterns.
    for alter_sql in (
        "ALTER TABLE llm_calls ADD COLUMN cache_read_input_tokens INTEGER",
        "ALTER TABLE llm_calls ADD COLUMN cache_creation_input_tokens INTEGER",
    ):
        try:
            conn.execute(alter_sql)
            conn.commit()
        except sqlite3.OperationalError:
            conn.rollback()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS response_cache_log (
                timestamp TEXT NOT NULL,
                hit INTEGER NOT NULL
            );
        """)
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()
    try:
        n = conn.execute("SELECT COUNT(*) FROM llm_calls").fetchone()[0]
        if n == 0:
            _migrate_cost_daily_if_exists(conn)
    except sqlite3.OperationalError:
        conn.rollback()


def _get_conn() -> sqlite3.Connection:
    path = _metrics_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db_str = str(path)
    conn = sqlite3.connect(db_str)
    if db_str not in _init_done_paths:
        with _init_lock:
            if db_str not in _init_done_paths:
                _run_migrations(conn)
                _init_done_paths.add(db_str)
    return conn


def log_response_cache(hit: bool) -> None:
    """Log response cache hit (True) or miss (False). Block 5.3."""
    log.info("llm.response_cache", hit=hit)
    conn = _get_conn()
    try:
        ts = datetime.now(UTC).isoformat()
        conn.execute("INSERT INTO response_cache_log (timestamp, hit) VALUES (?, ?)", (ts, 1 if hit else 0))
        conn.commit()
    finally:
        conn.close()


def _migrate_cost_daily_if_exists(conn: sqlite3.Connection) -> None:
    path = _cost_file_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return
    cursor = conn.cursor()
    for day_str, cost in data.items():
        if not isinstance(cost, int | float) or cost <= 0:
            continue
        try:
            ts = datetime.fromisoformat(day_str).replace(tzinfo=UTC).isoformat()
        except (ValueError, TypeError):
            ts = day_str + "T12:00:00+00:00"
        cursor.execute(
            "INSERT INTO llm_calls(timestamp, model, input_tokens, output_tokens, "
            "cost_usd, latency_ms, success) VALUES (?, 'migrated', 0, 0, ?, 0, 1)",
            (ts, float(cost)),
        )
    conn.commit()


def get_cost_today() -> float:
    """Return total LLM cost for today from SQLite (source of truth).
    Uses UTC date to match stored UTC timestamps — avoids the midnight gap bug."""
    conn = _get_conn()
    try:
        today = datetime.now(UTC).date().isoformat()
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_calls WHERE date(timestamp) = ? AND success = 1",
            (today,),
        ).fetchone()
        return float(row[0] or 0.0)
    except sqlite3.OperationalError:
        return 0.0
    finally:
        conn.close()


def log_llm_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    latency_ms: int = 0,
    success: bool = True,
    *,
    cache_read_input_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
) -> None:
    """Log one LLM completion to structlog and SQLite. Block 5.1: cache metrics for Claude."""
    log.info(
        "llm.call",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(cost_usd, 6),
        cache_read_input_tokens=cache_read_input_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
    )
    if cost_usd > 0.1:
        log.warning("llm.cost_chunk", model=model, cost_usd=round(cost_usd, 4))
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        ts = datetime.now(UTC).isoformat()
        cursor.execute(
            "INSERT INTO llm_calls(timestamp, model, input_tokens, output_tokens, "
            "cost_usd, latency_ms, success, cache_read_input_tokens, cache_creation_input_tokens) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ts,
                model,
                input_tokens,
                output_tokens,
                cost_usd,
                latency_ms,
                1 if success else 0,
                cache_read_input_tokens,
                cache_creation_input_tokens,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _aggregate_by_model_rows(
    rows: list, cache_cols: bool, log_key: str = "get_stats_row"
) -> tuple[list[dict], float, int, list[float]]:
    """Build by_model list and aggregates from GROUP BY model query rows."""
    by_model: list[dict] = []
    total_cost = 0.0
    total_calls = 0
    latencies: list[float] = []
    for row in rows:
        try:
            if cache_cols:
                model, inp, out, cost, avg_lat, cnt, cache_read, cache_cre = row
            else:
                model, inp, out, cost, avg_lat, cnt = row
                cache_read = cache_cre = 0
        except (ValueError, TypeError) as e:
            log.warning("metrics.%s_unpack_failed", log_key, error=str(e))
            continue
        total_cost += cost or 0
        total_calls += cnt or 0
        if avg_lat is not None:
            latencies.append(avg_lat)
        entry = {
            "model": model or "",
            "input_tokens": inp or 0,
            "output_tokens": out or 0,
            "cost_usd": cost or 0,
            "avg_latency_ms": avg_lat,
            "calls": cnt or 0,
        }
        if cache_cols:
            entry["cache_read_input_tokens"] = cache_read or 0
            entry["cache_creation_input_tokens"] = cache_cre or 0
        by_model.append(entry)
    return by_model, total_cost, total_calls, latencies


def _fetch_cache_stats_since(cursor: sqlite3.Cursor, since: str) -> tuple[int, int]:
    try:
        cursor.execute(
            "SELECT SUM(hit), COUNT(*) FROM response_cache_log WHERE timestamp >= ?",
            (since,),
        )
        row = cursor.fetchone()
        if row and row[1]:
            hits = row[0] or 0
            return (hits, (row[1] or 0) - hits)
    except sqlite3.OperationalError:
        pass
    return 0, 0


def _fetch_cache_stats_range(cursor: sqlite3.Cursor, from_ts: str, to_ts: str) -> tuple[int, int]:
    try:
        cursor.execute(
            "SELECT SUM(hit), COUNT(*) FROM response_cache_log WHERE date(timestamp) >= ? AND date(timestamp) <= ?",
            (from_ts, to_ts),
        )
        row = cursor.fetchone()
        if row and row[1]:
            hits = row[0] or 0
            return (hits, (row[1] or 0) - hits)
    except sqlite3.OperationalError:
        pass
    return 0, 0


def _build_stats_result(
    by_model: list[dict],
    by_day: list[dict],
    total_cost: float,
    total_calls: int,
    latencies: list[float],
    cache_hits: int,
    cache_misses: int,
) -> dict:
    total_cache = cache_hits + cache_misses
    return {
        "by_model": by_model,
        "by_day": by_day,
        "total_cost_usd": total_cost,
        "total_calls": total_calls,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "response_cache_hits": cache_hits,
        "response_cache_misses": cache_misses,
        "response_cache_hit_rate": cache_hits / total_cache if total_cache else None,
    }


def get_stats(days: int = 30) -> dict:
    """Return aggregates for the last N days: by model, avg latency, total cost."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        try:
            cursor.execute(
                "SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd), "
                "AVG(latency_ms), COUNT(*), SUM(COALESCE(cache_read_input_tokens, 0)), "
                "SUM(COALESCE(cache_creation_input_tokens, 0)) FROM llm_calls "
                "WHERE timestamp >= ? AND success = 1 GROUP BY model",
                (since,),
            )
            cache_cols = True
        except sqlite3.OperationalError:
            cursor.execute(
                "SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd), "
                "AVG(latency_ms), COUNT(*) FROM llm_calls WHERE timestamp >= ? AND success = 1 "
                "GROUP BY model",
                (since,),
            )
            cache_cols = False
        by_model, total_cost, total_calls, latencies = _aggregate_by_model_rows(cursor.fetchall(), cache_cols, "get_stats_row")
        cursor.execute(
            "SELECT date(timestamp) as d, SUM(cost_usd), COUNT(*) FROM llm_calls "
            "WHERE timestamp >= ? AND success = 1 GROUP BY d ORDER BY d",
            (since,),
        )
        by_day = [{"date": r[0], "cost_usd": r[1] or 0, "calls": r[2] or 0} for r in cursor.fetchall()]
        cache_hits, cache_misses = _fetch_cache_stats_since(cursor, since)
        return _build_stats_result(by_model, by_day, total_cost, total_calls, latencies, cache_hits, cache_misses)
    finally:
        conn.close()


def get_stats_range(from_date: date, to_date: date) -> dict:
    """Return same structure as get_stats but for date range (inclusive). Block 11.5 analytics."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        from_ts = from_date.isoformat()
        to_ts = to_date.isoformat()
        try:
            cursor.execute(
                "SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd), "
                "AVG(latency_ms), COUNT(*), SUM(COALESCE(cache_read_input_tokens, 0)), "
                "SUM(COALESCE(cache_creation_input_tokens, 0)) FROM llm_calls "
                "WHERE date(timestamp) >= ? AND date(timestamp) <= ? AND success = 1 GROUP BY model",
                (from_ts, to_ts),
            )
            cache_cols = True
        except sqlite3.OperationalError:
            cursor.execute(
                "SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd), "
                "AVG(latency_ms), COUNT(*) FROM llm_calls "
                "WHERE date(timestamp) >= ? AND date(timestamp) <= ? AND success = 1 GROUP BY model",
                (from_ts, to_ts),
            )
            cache_cols = False
        by_model, total_cost, total_calls, latencies = _aggregate_by_model_rows(
            cursor.fetchall(), cache_cols, "get_stats_range_row"
        )
        cursor.execute(
            "SELECT date(timestamp) as d, SUM(cost_usd), COUNT(*) FROM llm_calls "
            "WHERE date(timestamp) >= ? AND date(timestamp) <= ? AND success = 1 GROUP BY d ORDER BY d",
            (from_ts, to_ts),
        )
        by_day = [{"date": r[0], "cost_usd": r[1] or 0, "calls": r[2] or 0} for r in cursor.fetchall()]
        cache_hits, cache_misses = _fetch_cache_stats_range(cursor, from_ts, to_ts)
        return _build_stats_result(by_model, by_day, total_cost, total_calls, latencies, cache_hits, cache_misses)
    finally:
        conn.close()
