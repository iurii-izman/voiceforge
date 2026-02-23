"""Block 4.2: Persistent transcript and analysis log — SQLite, FTS5 search. Block 11.7: migrations."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()

DB_NAME = "transcripts.db"
SCHEMA_VERSION_TARGET = 4  # Block 11.7: run migrations 001..004
MIGRATION_HASHES = {
    "001_initial.sql": "59b9076a9a928c7d2b43e0b63b14e16cf0a4a2ec1a9f00a400aaf57efbc315f5",
    "002_add_daily_reports.sql": "0cdbaa0a88a392d97539d5768cbf62bd98f58394cbd96476c77d846240763844",
    "003_add_period_reports.sql": "3b58a4ec71e9445e77e9d7189b6b4811f33045123cfb1a550f1d5656182d77de",
    "004_add_template.sql": "534b84d0d2c6602f7b32ff6fd3faddb8828dd0c7e628cbead279f7d342efd7a6",
}


def _db_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge" / DB_NAME


def _migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "migrations"


def _ensure_schema_version_row(conn: sqlite3.Connection) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")
        conn.commit()
        return 0
    return int(row[0])


def _migration_sql_file(migrations_dir: Path, version: int) -> Path | None:
    candidates = list(migrations_dir.glob(f"{version:03d}_*.sql"))
    if not candidates:
        return None
    return candidates[0]


def _backup_before_migration(db_path: Path) -> None:
    backup_path = Path(str(db_path) + ".bak")
    try:
        shutil.copy2(db_path, backup_path)
        log.info("migration.backup", path=str(backup_path))
    except Exception as e:
        log.warning("migration.backup_failed", path=str(backup_path), error=str(e))


def _validate_migration_sql(sql_file: Path, sql_text: str) -> None:
    expected_hash = MIGRATION_HASHES.get(sql_file.name)
    if not expected_hash:
        raise RuntimeError(f"Unknown migration file: {sql_file.name}")
    actual_hash = sha256(sql_text.encode("utf-8")).hexdigest()
    if actual_hash != expected_hash:
        raise RuntimeError(f"Migration checksum mismatch: {sql_file.name}")


def _apply_migration(conn: sqlite3.Connection, sql_file: Path, version: int) -> None:
    sql = sql_file.read_text()
    _validate_migration_sql(sql_file, sql)
    conn.executescript(sql)
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
        (f"{version:03d}_{sql_file.stem.split('_', 1)[-1]}", datetime.now(UTC).isoformat()),
    )
    conn.commit()
    log.info("migration.applied", file=sql_file.name)


def _run_migrations(conn: sqlite3.Connection, db_path: Path) -> None:
    """Block 11.7: apply migrations 001..TARGET; backup before first."""
    version = _ensure_schema_version_row(conn)
    if version >= SCHEMA_VERSION_TARGET:
        return
    migrations_dir = _migrations_dir()
    for n in range(version + 1, SCHEMA_VERSION_TARGET + 1):
        sql_file = _migration_sql_file(migrations_dir, n)
        if sql_file is None:
            log.warning("migration.missing", expected=n, dir=str(migrations_dir))
            continue
        if version == 0:
            _backup_before_migration(db_path)
        try:
            _apply_migration(conn, sql_file, n)
        except Exception as e:
            log.exception("migration.failed", file=sql_file.name, error=str(e))
            raise
        version = n


@dataclass
class SessionSummary:
    id: int
    started_at: str
    ended_at: str
    duration_sec: float
    segments_count: int


@dataclass
class SegmentRow:
    start_sec: float
    end_sec: float
    speaker: str
    text: str


@dataclass
class AnalysisRow:
    timestamp: str
    model: str
    questions: list[str]
    answers: list[str]
    recommendations: list[str]
    action_items: list[dict[str, Any]]
    cost_usd: float
    template: str | None = None


def _init_db(conn: sqlite3.Connection) -> None:
    """Ensure schema_version exists. Block 11.7: actual schema from migrations."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES ('001_initial', ?)",
        (datetime.now(UTC).isoformat(),),
    )
    conn.commit()


def _ensure_migrated(conn: sqlite3.Connection, db_path: Path) -> None:
    """Block 11.7: run migrations if schema_version < TARGET."""
    _run_migrations(conn, db_path)


def _resolve_duration_sec(segments: list[dict[str, Any]], duration_sec: float | None) -> float:
    if duration_sec is not None:
        return duration_sec
    if not segments:
        return 0.0
    max_end = max(s.get("end_sec", 0) or 0 for s in segments)
    min_start = min(s.get("start_sec", 0) or 0 for s in segments)
    return max_end - min_start


def _insert_segments(cursor: sqlite3.Cursor, session_id: int, segments: list[dict[str, Any]]) -> None:
    for segment in segments:
        cursor.execute(
            "INSERT INTO segments (session_id, start_sec, end_sec, speaker, text) VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                float(segment.get("start_sec", 0) or 0),
                float(segment.get("end_sec", 0) or 0),
                str(segment.get("speaker", "") or ""),
                str(segment.get("text", "") or ""),
            ),
        )


def _insert_analysis(
    cursor: sqlite3.Cursor,
    session_id: int,
    ended_at: datetime,
    model: str,
    questions: list[str] | None,
    answers: list[str] | None,
    recommendations: list[str] | None,
    action_items: list[dict[str, Any]] | None,
    cost_usd: float,
    template: str | None = None,
) -> None:
    cursor.execute(
        "INSERT INTO analyses (session_id, timestamp, model, questions, answers, "
        "recommendations, action_items, cost_usd, template) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id,
            ended_at.isoformat(),
            model,
            json.dumps(questions or []),
            json.dumps(answers or []),
            json.dumps(recommendations or []),
            json.dumps(action_items or []),
            cost_usd,
            template or "",
        ),
    )


class TranscriptLog:
    """Persistent log: sessions, segments, analyses. FTS5 search on segment text."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or _db_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            _init_db(self._conn)
            _ensure_migrated(self._conn, self.db_path)
        return self._conn

    def log_session(
        self,
        segments: list[dict[str, Any]],
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        duration_sec: float | None = None,
        model: str = "",
        questions: list[str] | None = None,
        answers: list[str] | None = None,
        recommendations: list[str] | None = None,
        action_items: list[dict[str, Any]] | None = None,
        cost_usd: float = 0.0,
        template: str | None = None,
    ) -> int:
        """Write one session (segments + analysis). Returns session_id."""
        started_at = started_at or datetime.now(UTC)
        ended_at = ended_at or datetime.now(UTC)
        duration_sec = _resolve_duration_sec(segments, duration_sec)
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (started_at, ended_at, duration_sec) VALUES (?, ?, ?)",
            (started_at.isoformat(), ended_at.isoformat(), duration_sec),
        )
        session_id = cursor.lastrowid or 0
        _insert_segments(cursor, session_id, segments)
        _insert_analysis(
            cursor, session_id, ended_at, model, questions, answers, recommendations, action_items, cost_usd, template
        )
        conn.commit()
        log.info("transcript_log.log_session", session_id=session_id, segments=len(segments))
        return session_id

    def get_sessions(self, last_n: int = 10) -> list[SessionSummary]:
        """Return last N sessions (newest first)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.id, s.started_at, s.ended_at, s.duration_sec,
                   (SELECT COUNT(*) FROM segments WHERE session_id = s.id) AS segments_count
            FROM sessions s
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (last_n,),
        )
        return [
            SessionSummary(
                id=row["id"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                duration_sec=row["duration_sec"],
                segments_count=row["segments_count"],
            )
            for row in cursor.fetchall()
        ]

    def get_sessions_for_date(self, day: date) -> list[SessionSummary]:
        """Return all sessions that started on the given date (local date string YYYY-MM-DD)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        day_str = day.isoformat()
        cursor.execute(
            """
            SELECT s.id, s.started_at, s.ended_at, s.duration_sec,
                   (SELECT COUNT(*) FROM segments WHERE session_id = s.id) AS segments_count
            FROM sessions s
            WHERE date(s.started_at) = ?
            ORDER BY s.started_at
            """,
            (day_str,),
        )
        return [
            SessionSummary(
                id=row["id"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                duration_sec=row["duration_sec"],
                segments_count=row["segments_count"],
            )
            for row in cursor.fetchall()
        ]

    def get_sessions_in_range(self, from_date: date, to_date: date) -> list[SessionSummary]:
        """Return all sessions that started between from_date and to_date (inclusive)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        from_str = from_date.isoformat()
        to_str = to_date.isoformat()
        cursor.execute(
            """
            SELECT s.id, s.started_at, s.ended_at, s.duration_sec,
                   (SELECT COUNT(*) FROM segments WHERE session_id = s.id) AS segments_count
            FROM sessions s
            WHERE date(s.started_at) >= ? AND date(s.started_at) <= ?
            ORDER BY s.started_at
            """,
            (from_str, to_str),
        )
        return [
            SessionSummary(
                id=row["id"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                duration_sec=row["duration_sec"],
                segments_count=row["segments_count"],
            )
            for row in cursor.fetchall()
        ]

    def get_period_text(self, from_date: date, to_date: date) -> str:
        """Concatenate segment texts from all sessions in the date range. Empty if none."""
        sessions = self.get_sessions_in_range(from_date, to_date)
        parts: list[str] = []
        for sess in sessions:
            detail = self.get_session_detail(sess.id)
            if not detail:
                continue
            segments, _ = detail
            if segments:
                parts.append(f"[Сессия {sess.id} {sess.started_at}]\n" + "\n".join(s.text for s in segments))
        return "\n\n".join(parts) if parts else ""

    def save_period_report(self, period_from: date, period_to: date, report_text: str) -> None:
        """Insert a period report (no dedup by range; each run adds a row)."""
        conn = self._get_conn()
        now = datetime.now(UTC).isoformat()
        conn.execute(
            """
            INSERT INTO period_reports (period_from, period_to, report_text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (period_from.isoformat(), period_to.isoformat(), report_text, now),
        )
        conn.commit()

    def get_period_report(self, period_from: date, period_to: date) -> str | None:
        """Return the latest period report text for the range, or None."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT report_text FROM period_reports
            WHERE period_from = ? AND period_to = ?
            ORDER BY id DESC LIMIT 1
            """,
            (period_from.isoformat(), period_to.isoformat()),
        )
        row = cursor.fetchone()
        return row["report_text"] if row else None

    def get_daily_transcript_text(self, day: date) -> str:
        """Concatenate segment texts from sessions on the given date. Returns empty if none."""
        sessions = self.get_sessions_for_date(day)
        parts: list[str] = []
        for sess in sessions:
            detail = self.get_session_detail(sess.id)
            if not detail:
                continue
            segments, _ = detail
            if segments:
                parts.append(f"[Сессия {sess.id} {sess.started_at}]\n" + "\n".join(s.text for s in segments))
        return "\n\n".join(parts) if parts else ""

    def save_daily_report(
        self,
        day: date,
        report_text: str | None = None,
        batch_id: str | None = None,
        status: str = "completed",
    ) -> None:
        """Insert or replace daily report row. status: pending, submitted, completed, failed."""
        conn = self._get_conn()
        day_str = day.isoformat()
        now = datetime.now(UTC).isoformat()
        conn.execute(
            """
            INSERT INTO daily_reports (date, report_text, batch_id, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                report_text = COALESCE(excluded.report_text, daily_reports.report_text),
                batch_id = COALESCE(excluded.batch_id, daily_reports.batch_id),
                status = excluded.status
            """,
            (day_str, report_text, batch_id, status, now),
        )
        conn.commit()

    def get_daily_report(self, day: date) -> tuple[str | None, str | None, str] | None:
        """Return (report_text, batch_id, status) for the date, or None."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT report_text, batch_id, status FROM daily_reports WHERE date = ?",
            (day.isoformat(),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return (row["report_text"], row["batch_id"], row["status"] or "pending")

    def get_session_meta(self, session_id: int) -> tuple[str, str, float] | None:
        """Return (started_at, ended_at, duration_sec) for session_id, or None if not found."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT started_at, ended_at, duration_sec FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return (row["started_at"], row["ended_at"], row["duration_sec"] or 0.0)

    def get_session_detail(self, session_id: int) -> tuple[list[SegmentRow], AnalysisRow | None] | None:
        """Return segments and analysis for session_id, or None if not found."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        if cursor.fetchone() is None:
            return None
        cursor.execute(
            "SELECT start_sec, end_sec, speaker, text FROM segments WHERE session_id = ? ORDER BY start_sec",
            (session_id,),
        )
        segments = [
            SegmentRow(
                start_sec=row["start_sec"],
                end_sec=row["end_sec"],
                speaker=row["speaker"],
                text=row["text"],
            )
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "SELECT timestamp, model, questions, answers, recommendations, action_items, cost_usd, template "
            "FROM analyses WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return (segments, None)
        try:
            template_val = row["template"] if row["template"] else None
        except (KeyError, TypeError):
            template_val = None
        analysis = AnalysisRow(
            timestamp=row["timestamp"],
            model=row["model"],
            questions=json.loads(row["questions"] or "[]"),
            answers=json.loads(row["answers"] or "[]"),
            recommendations=json.loads(row["recommendations"] or "[]"),
            action_items=json.loads(row["action_items"] or "[]"),
            cost_usd=row["cost_usd"] or 0.0,
            template=template_val,
        )
        return (segments, analysis)

    def search_transcripts(self, query: str, limit: int = 20) -> list[tuple[int, str, float, float, str]]:
        """FTS5 search on segment text. Returns (session_id, text, start_sec, end_sec, snippet)."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.session_id, s.text, s.start_sec, s.end_sec,
                   snippet(segments_fts, 0, '', '', '…', 32) AS snippet
            FROM segments_fts f
            JOIN segments s ON s.id = f.rowid
            WHERE segments_fts MATCH ?
            ORDER BY s.session_id DESC, s.start_sec
            LIMIT ?
            """,
            (query, limit),
        )
        return [(r["session_id"], r["text"], r["start_sec"], r["end_sec"], r["snippet"] or "") for r in cursor.fetchall()]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
