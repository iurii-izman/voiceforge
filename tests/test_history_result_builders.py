"""Tests for history_helpers result builders (history_*_result); coverage #56."""

from __future__ import annotations

from datetime import UTC, date, datetime

from voiceforge.cli import history_helpers as hh
from voiceforge.core.transcript_log import TranscriptLog


def test_history_list_result_empty(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        kind, data = hh.history_list_result(log, 10, "json")
        assert kind == "json"
        assert data == {"sessions": []}
        kind2, lines = hh.history_list_result(log, 10, "lines")
        assert kind2 == "message"
        assert "no_sessions" in lines or "Нет" in lines
    finally:
        log.close()


def test_history_list_result_with_sessions(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "hi"}],
            model="m",
        )
        kind, data = hh.history_list_result(log, 5, "json")
        assert kind == "json"
        assert len(data["sessions"]) == 1
        kind2, lines = hh.history_list_result(log, 5, "lines")
        assert kind2 == "lines"
        assert len(lines) >= 3
    finally:
        log.close()


def test_history_session_detail_result_json_and_lines(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "S", "text": "detail"}],
            model="m",
        )
        kind, payload = hh.history_session_detail_result(log, 1, "json")
        assert kind == "json"
        assert payload["session_id"] == 1
        assert len(payload["segments"]) == 1
        kind2, lines = hh.history_session_detail_result(log, 1, "lines")
        assert kind2 == "lines"
        assert any("detail" in ln for ln in lines)
        kind3, md = hh.history_session_detail_result(log, 1, "md")
        assert kind3 == "md"
        assert "# Сессия 1" in md
    finally:
        log.close()


def test_history_session_detail_result_not_found(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        kind, msg = hh.history_session_detail_result(log, 99999, "lines")
        assert kind == "error"
        assert "99999" in msg
    finally:
        log.close()


def test_history_action_items_result_empty(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        kind, data = hh.history_action_items_result(log, "json")
        assert kind == "json"
        assert data["action_items"] == []
        kind2, _ = hh.history_action_items_result(log, "lines")
        assert kind2 == "message"
    finally:
        log.close()


def test_history_action_items_result_with_items(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "t"}],
            action_items=[{"description": "Task one", "assignee": "dev"}],
        )
        kind, data = hh.history_action_items_result(log, "json")
        assert kind == "json"
        assert len(data["action_items"]) >= 1
        kind2, lines = hh.history_action_items_result(log, "lines")
        assert kind2 == "lines"
        assert any("Task one" in ln for ln in lines)
    finally:
        log.close()


def test_history_search_result_empty(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        kind, data = hh.history_search_result(log, "nonexistent", "json")
        assert kind == "json"
        assert data["hits"] == []
        kind2, _ = hh.history_search_result(log, "x", "lines")
        assert kind2 == "message"
    finally:
        log.close()


def test_history_search_result_with_hits(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "needle in hay"}],
        )
        kind, data = hh.history_search_result(log, "needle", "json")
        assert kind == "json"
        assert len(data["hits"]) >= 1
        kind2, _ = hh.history_search_result(log, "needle", "lines")
        assert kind2 == "lines"
    finally:
        log.close()


def test_history_date_range_result_by_date(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        today = date.today()
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "x"}],
            started_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
            ended_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC),
        )
        kind, data = hh.history_date_range_result(log, today.isoformat(), None, None, "json")
        assert kind == "json"
        assert len(data["sessions"]) >= 1
    finally:
        log.close()


def test_history_date_range_result_error_date_or_range(tmp_path) -> None:
    log = TranscriptLog(db_path=tmp_path / "e.db")
    try:
        kind, key = hh.history_date_range_result(log, "2025-01-15", "2025-01-01", "2025-01-31", "lines")
        assert kind == "error"
        assert "date_or_range" in key or "date" in str(key).lower()
    finally:
        log.close()
