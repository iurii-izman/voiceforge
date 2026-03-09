"""E14 (#137): Tests for Rich output (history table, cost table, status panel)."""

from __future__ import annotations


def test_render_sessions_table_rich_builds_table() -> None:
    """render_sessions_table_rich returns a Rich Table with expected columns."""
    from voiceforge.cli.history_helpers import render_sessions_table_rich

    class Session:
        id = 1
        started_at = "2025-03-09T10:00:00"
        duration_sec = 60.0
        speaker_count = 2
        summary_preview = "Summary text"

    table = render_sessions_table_rich([Session()])
    assert table is not None
    assert hasattr(table, "columns")
    assert len(table.columns) >= 4  # id, date, duration, speakers, summary


def test_history_list_result_rich_sessions_when_text(tmp_path) -> None:
    """history_list_result with output=text and use_rich=True returns rich_sessions."""
    from voiceforge.cli import history_helpers as hh
    from voiceforge.core.transcript_log import TranscriptLog

    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "hi"}],
            model="m",
        )
        kind, data = hh.history_list_result(log, 5, "text", use_rich=True)
        assert kind == "rich_sessions"
        assert isinstance(data, list)
        assert len(data) == 1
    finally:
        log.close()


def test_history_list_result_lines_when_lines_output(tmp_path) -> None:
    """history_list_result with output=lines returns lines (backward compat)."""
    from voiceforge.cli import history_helpers as hh
    from voiceforge.core.transcript_log import TranscriptLog

    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "hi"}],
            model="m",
        )
        kind, data = hh.history_list_result(log, 5, "lines")
        assert kind == "lines"
        assert isinstance(data, list)
        assert all(isinstance(x, str) for x in data)
    finally:
        log.close()


def test_error_code_enum_values() -> None:
    """ErrorCode enum has VF001-VF099 style values."""
    from voiceforge.core.contracts import ErrorCode

    assert ErrorCode.SESSION_NOT_FOUND.value == "VF001"
    assert ErrorCode.ANALYZE_FAILED.value == "VF002"
    assert ErrorCode.BUDGET_EXCEEDED.value == "VF010"
    assert ErrorCode.CALDAV_UPCOMING_FAILED.value == "VF020"
    assert ErrorCode.GENERIC.value == "VF099"
