from __future__ import annotations

import contextlib
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import voiceforge.core.metrics as metrics
from voiceforge.core.transcript_log import SCHEMA_VERSION_TARGET, TranscriptLog


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name = ? AND type IN ('table', 'view') LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def test_transcript_migrations_on_clean_db(tmp_path) -> None:
    db_path = tmp_path / "transcripts.db"
    log_db = TranscriptLog(db_path=db_path)
    assert log_db.get_sessions() == []
    log_db.close()

    conn = sqlite3.connect(db_path)
    try:
        version = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        assert version is not None
        assert int(version[0]) == SCHEMA_VERSION_TARGET
        for table in (
            "sessions",
            "segments",
            "analyses",
            "segments_fts",
            "daily_reports",
            "period_reports",
            "action_items",
        ):
            assert _table_exists(conn, table), table
    finally:
        conn.close()


def test_transcript_migrations_on_existing_db(tmp_path) -> None:
    db_path = tmp_path / "transcripts.db"
    log_db = TranscriptLog(db_path=db_path)
    _ = log_db.get_sessions()
    log_db.close()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS daily_reports")
        conn.execute("DROP TABLE IF EXISTS period_reports")
        # Roll back analyses to post-001 state: remove column added in 004 so re-run can add it again
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE analyses DROP COLUMN template")
        conn.execute("UPDATE schema_version SET version = 1")
        conn.commit()
    finally:
        conn.close()

    log_db = TranscriptLog(db_path=db_path)
    _ = log_db.get_sessions()
    log_db.close()

    conn = sqlite3.connect(db_path)
    try:
        version = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        assert version is not None
        assert int(version[0]) == SCHEMA_VERSION_TARGET
        assert _table_exists(conn, "daily_reports")
        assert _table_exists(conn, "period_reports")
        assert _table_exists(conn, "action_items")
    finally:
        conn.close()


def test_retention_purge_removes_old_sessions(tmp_path) -> None:
    """Sessions with started_at before cutoff are removed by purge_before (#43)."""
    db_path = tmp_path / "transcripts.db"
    log_db = TranscriptLog(db_path=db_path)
    now = datetime.now(UTC)
    old_start = now - timedelta(days=100)
    recent_start = now - timedelta(days=50)
    log_db.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "old"}],
        started_at=old_start,
        ended_at=old_start,
    )
    log_db.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "B", "text": "recent"}],
        started_at=recent_start,
        ended_at=recent_start,
    )
    assert len(log_db.get_sessions()) == 2
    cutoff = date.today() - timedelta(days=90)
    n = log_db.purge_before(cutoff)
    assert n == 1
    sessions = log_db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0].started_at == recent_start.isoformat()
    log_db.close()


def test_metrics_migrations_on_clean_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    metrics._init_done_paths.clear()
    metrics.log_llm_call("anthropic/claude-haiku-4-5", 10, 20, 0.0001, success=True)

    db_path = Path(tmp_path / "data" / "voiceforge" / "metrics.db")
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        assert _table_exists(conn, "llm_calls")
        assert _table_exists(conn, "response_cache_log")
        assert _table_exists(conn, "schema_migrations")
        cols = {row[1] for row in conn.execute("PRAGMA table_info(llm_calls)").fetchall()}
        assert "cache_read_input_tokens" in cols
        assert "cache_creation_input_tokens" in cols
    finally:
        conn.close()


def test_metrics_migrations_on_existing_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    db_path = Path(tmp_path / "data" / "voiceforge" / "metrics.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                latency_ms INTEGER NOT NULL,
                success INTEGER NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    metrics._init_done_paths.clear()
    _ = metrics.get_cost_today()

    conn = sqlite3.connect(db_path)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(llm_calls)").fetchall()}
        assert "cache_read_input_tokens" in cols
        assert "cache_creation_input_tokens" in cols
        assert _table_exists(conn, "response_cache_log")
        assert _table_exists(conn, "schema_migrations")
    finally:
        conn.close()
