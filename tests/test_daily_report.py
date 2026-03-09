"""E10 (#133): Daily digest and daily-report command."""

from __future__ import annotations

from datetime import date

import pytest

from voiceforge.cli.digest import (
    DailyDigest,
    build_daily_digest,
    format_daily_digest_text,
)
from voiceforge.core.transcript_log import TranscriptLog


def test_build_daily_digest_empty(tmp_path) -> None:
    """Empty DB yields digest with no sessions and zero cost."""
    log = TranscriptLog(db_path=tmp_path / "d.db")
    try:
        day = date.today()
        digest = build_daily_digest(log, day)
        assert digest.day == day
        assert digest.session_ids == []
        assert digest.session_summaries == []
        assert digest.action_items == []
        assert digest.total_cost_usd == pytest.approx(0.0)
    finally:
        log.close()


def test_build_daily_digest_one_session(tmp_path) -> None:
    """One session on today yields one session and optional action items."""
    log = TranscriptLog(db_path=tmp_path / "d.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 10, "speaker": "A", "text": "meeting"}],
            model="m",
            action_items=[{"description": "Follow up", "assignee": "Bob"}],
        )
        day = date.today()
        digest = build_daily_digest(log, day)
        assert len(digest.session_ids) == 1
        assert digest.session_ids[0] == 1
        assert len(digest.session_summaries) == 1
        assert len(digest.action_items) >= 1
    finally:
        log.close()


def test_format_daily_digest_text() -> None:
    """Formatted text contains date, sessions section, action items."""
    digest = DailyDigest(
        day=date(2025, 3, 9),
        session_ids=[1],
        session_summaries=[(1, "2025-03-09T10:00:00", 120.0)],
        action_items=[{"session_id": 1, "description": "Task", "assignee": "Alice", "status": "open"}],
        total_cost_usd=0.05,
    )
    text = format_daily_digest_text(digest)
    assert "2025-03-09" in text
    assert "Session 1" in text or "1" in text
    assert "0.05" in text or "cost" in text.lower()
    assert "Task" in text
    assert "Action items" in text or "action" in text.lower()


def test_daily_report_cli_empty() -> None:
    """daily-report with no sessions prints structured output."""
    from typer.testing import CliRunner

    from voiceforge.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["daily-report"])
    assert result.exit_code == 0
    assert "Daily digest" in result.output or "digest" in result.output.lower()
    assert "Sessions:" in result.output or "sessions" in result.output.lower()
