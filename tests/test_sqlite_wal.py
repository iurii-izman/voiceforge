"""E18 (#141): SQLite WAL mode for transcript_log — concurrent reads (daemon + CLI + web)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from voiceforge.core.transcript_log import TranscriptLog


def test_transcript_log_uses_wal_mode(tmp_path: Path) -> None:
    """TranscriptLog enables WAL and NORMAL synchronous on first connection."""
    db = tmp_path / "transcripts.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "x"}],
        model="test",
    )
    log.close()

    conn = sqlite3.connect(str(db))
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0].upper()
        assert mode == "WAL", f"expected WAL, got {mode}"
        # synchronous is per-connection; TranscriptLog sets NORMAL on its connection
    finally:
        conn.close()


def test_transcript_log_wal_allows_concurrent_read(tmp_path: Path) -> None:
    """With WAL, second connection can read while first holds the db (no 'database is locked')."""
    db = tmp_path / "transcripts.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "y"}],
        model="test",
    )
    # Keep connection open (do not close)
    sessions = log.get_sessions(last_n=5)
    assert len(sessions) >= 1
    # Second connection can read
    conn2 = sqlite3.connect(str(db))
    try:
        row = conn2.execute("SELECT COUNT(*) FROM sessions").fetchone()
        assert row[0] >= 1
    finally:
        conn2.close()
    log.close()
