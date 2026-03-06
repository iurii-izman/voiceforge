"""Tests for core.transcript_log: TranscriptLog API beyond migrations (#56)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from voiceforge.core.transcript_log import TranscriptLog


def test_log_session_returns_id(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    sid = log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "hi"}],
        model="test",
        questions=["q1"],
        answers=["a1"],
        action_items=[{"description": "task", "assignee": "me"}],
    )
    assert sid == 1
    log.close()


def test_get_sessions_and_session_detail(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 2, "speaker": "B", "text": "hello world"}],
        model="m",
    )
    sessions = log.get_sessions(last_n=5)
    assert len(sessions) == 1
    assert sessions[0].segments_count == 1
    detail = log.get_session_detail(sessions[0].id)
    assert detail is not None
    segments, analysis = detail
    assert len(segments) == 1
    assert segments[0].text == "hello world"
    assert analysis is not None
    assert analysis.model == "m"
    log.close()


def test_get_session_meta(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    started = datetime.now(UTC)
    ended = started + timedelta(seconds=10)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "X", "text": "x"}],
        started_at=started,
        ended_at=ended,
    )
    meta = log.get_session_meta(1)
    assert meta is not None
    assert meta[2] == pytest.approx(1.0)  # duration_sec
    log.close()


def test_get_sessions_for_date(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    today = date.today()
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "a"}],
        started_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
        ended_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
    )
    for_date = log.get_sessions_for_date(today)
    assert len(for_date) == 1
    log.close()


def test_get_sessions_in_range(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "a"}],
    )
    from_d = date.today() - timedelta(days=1)
    to_d = date.today() + timedelta(days=1)
    in_range = log.get_sessions_in_range(from_d, to_d)
    assert len(in_range) >= 1
    log.close()


def test_get_period_text(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "period"}],
    )
    from_d = date.today() - timedelta(days=1)
    to_d = date.today() + timedelta(days=1)
    text = log.get_period_text(from_d, to_d)
    assert "period" in text
    log.close()


def test_save_and_get_period_report(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    from_d = date(2025, 1, 1)
    to_d = date(2025, 1, 7)
    log.save_period_report(from_d, to_d, "Weekly report")
    out = log.get_period_report(from_d, to_d)
    assert out == "Weekly report"
    log.close()


def test_save_and_get_daily_report(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    day = date(2025, 3, 1)
    log.save_daily_report(day, report_text="Done", status="completed")
    out = log.get_daily_report(day)
    assert out is not None
    assert out[0] == "Done"
    assert out[2] == "completed"
    log.close()


def test_get_daily_transcript_text(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    today = date.today()
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "daily"}],
        started_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
        ended_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
    )
    text = log.get_daily_transcript_text(today)
    assert "daily" in text
    log.close()


def test_get_action_items(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "t"}],
        action_items=[
            {"description": "Do it", "assignee": "dev", "deadline": "2025-04-01"},
        ],
    )
    items = log.get_action_items(limit=10)
    assert len(items) >= 1
    assert any(ai.description == "Do it" for ai in items)
    log.close()


def test_search_transcripts(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "unique searchable word"}],
    )
    results = log.search_transcripts("searchable", limit=5)
    assert len(results) >= 1
    assert any("searchable" in r[1] for r in results)
    log.close()


def test_get_session_detail_nonexistent(tmp_path: Path) -> None:
    log = TranscriptLog(db_path=tmp_path / "t.db")
    assert log.get_session_detail(99999) is None
    log.close()


def test_get_session_meta_nonexistent(tmp_path: Path) -> None:
    log = TranscriptLog(db_path=tmp_path / "t.db")
    assert log.get_session_meta(99999) is None
    log.close()
