"""E10 (#133): History human-friendly output and search highlight."""

from __future__ import annotations

from voiceforge.cli import history_helpers as hh
from voiceforge.core.transcript_log import TranscriptLog


def test_history_list_default_human_friendly_has_columns(tmp_path) -> None:
    """Default list output (text) includes date, duration, speakers, summary columns."""
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "hello"}],
            model="m",
        )
        kind, lines = hh.history_list_result(log, 5, "text")
        assert kind == "lines"
        assert isinstance(lines, list)
        assert len(lines) >= 3
        header = lines[0]
        assert "date" in header.lower()
        assert "duration" in header.lower()
        assert "speakers" in header.lower()
        assert "summary" in header.lower()
    finally:
        log.close()


def test_history_list_json_unchanged(tmp_path) -> None:
    """--json still returns raw sessions payload."""
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 1, "speaker": "S", "text": "x"}],
            model="m",
        )
        kind, data = hh.history_list_result(log, 5, "json")
        assert kind == "json"
        assert "sessions" in data
        assert len(data["sessions"]) == 1
    finally:
        log.close()


def test_highlight_search_term() -> None:
    """Search term is wrapped in ANSI bold in snippet."""
    out = hh.highlight_search_term("some foo and bar", "foo")
    assert "\033[1m" in out
    assert "foo" in out
    assert "\033[0m" in out


def test_highlight_search_term_case_insensitive() -> None:
    """Highlight is case-insensitive."""
    out = hh.highlight_search_term("Some FOO here", "foo")
    assert "\033[1m" in out


def test_highlight_search_term_empty_term_returns_unchanged() -> None:
    """Empty term returns snippet unchanged."""
    assert hh.highlight_search_term("hello world", "") == "hello world"


def test_render_sessions_table_lines_human(tmp_path) -> None:
    """Human table has id, date, duration, speakers, summary."""
    log = TranscriptLog(db_path=tmp_path / "h.db")
    try:
        log.log_session(
            [{"start_sec": 0, "end_sec": 2, "speaker": "Alice", "text": "Hi"}],
            model="m",
        )
        display = log.get_sessions_for_display(last_n=5)
        assert len(display) == 1
        lines = hh.render_sessions_table_lines_human(display)
        assert "id" in lines[0].lower()
        assert "1" in lines[2] or "1 " in "".join(lines)
    finally:
        log.close()
