"""Tests for action-items export (E11 #134): markdown, csv, clipboard."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_action_items_markdown_empty() -> None:
    """_action_items_markdown returns empty string for no items."""
    from voiceforge.cli.history_helpers import _action_items_markdown

    assert _action_items_markdown([]) == ""


def test_action_items_markdown_one_item() -> None:
    """_action_items_markdown produces checklist with session id."""
    from voiceforge.cli.history_helpers import _action_items_markdown

    row = SimpleNamespace(
        session_id=42,
        idx_in_analysis=0,
        description="Review PR",
        assignee="Alice",
        deadline="2025-03-15",
        status="open",
    )
    out = _action_items_markdown([row])
    assert "# Action items" in out
    assert "- [ ]" in out
    assert "Review PR" in out
    assert "session #42" in out
    assert "Alice" in out
    assert "2025-03-15" in out


def test_action_items_markdown_done_status() -> None:
    """_action_items_markdown uses [x] for done/completed status."""
    from voiceforge.cli.history_helpers import _action_items_markdown

    row = SimpleNamespace(
        session_id=1,
        idx_in_analysis=0,
        description="Done task",
        assignee="",
        deadline="",
        status="done",
    )
    out = _action_items_markdown([row])
    assert "- [x]" in out
    assert "Done task" in out


def test_action_items_csv_empty() -> None:
    """_action_items_csv returns header only when no items."""
    from voiceforge.cli.history_helpers import _action_items_csv

    out = _action_items_csv([])
    assert "session_id" in out
    assert "description" in out
    assert "status" in out


def test_action_items_csv_one_row() -> None:
    """_action_items_csv produces valid CSV with one data row."""
    from voiceforge.cli.history_helpers import _action_items_csv

    row = SimpleNamespace(
        session_id=10,
        idx_in_analysis=1,
        description="Follow up",
        assignee="Bob",
        deadline="",
        status="pending",
    )
    out = _action_items_csv([row])
    assert "session_id" in out
    assert "10" in out
    assert "Follow up" in out
    assert "pending" in out


def test_action_items_export_command_markdown(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """voiceforge action-items export --format markdown writes markdown to file or stdout."""
    from voiceforge.core.transcript_log import ActionItemRow
    from voiceforge.main import action_items_export

    rows = [
        ActionItemRow(
            session_id=1,
            idx_in_analysis=0,
            description="Task one",
            assignee="",
            deadline="",
            status="open",
        ),
    ]
    echoed: list[str] = []

    def fake_get_action_items(self, limit: int = 100):
        return rows

    def fake_echo(msg: str, **kwargs) -> None:
        echoed.append(str(msg))

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog.get_action_items", fake_get_action_items)
    monkeypatch.setattr("typer.echo", fake_echo)
    out_path = tmp_path / "items.md"
    action_items_export(format="markdown", output=out_path, limit=100)
    assert out_path.read_text(encoding="utf-8").startswith("# Action items")
    assert "Task one" in out_path.read_text(encoding="utf-8")


def test_action_items_export_command_csv(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """voiceforge action-items export --format csv writes CSV."""
    from voiceforge.core.transcript_log import ActionItemRow
    from voiceforge.main import action_items_export

    rows = [
        ActionItemRow(
            session_id=2,
            idx_in_analysis=0,
            description="CSV task",
            assignee="",
            deadline="",
            status="done",
        ),
    ]
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog.get_action_items", lambda self, limit=100: rows)
    out_path = tmp_path / "items.csv"
    action_items_export(format="csv", output=out_path, limit=100)
    content = out_path.read_text(encoding="utf-8")
    assert "session_id" in content
    assert "CSV task" in content
    assert "done" in content


def test_action_items_export_no_items_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """action-items export with no items echoes message and exits 0."""
    from voiceforge.main import action_items_export

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog.get_action_items", lambda self, limit=100: [])
    with pytest.raises(SystemExit) as exc_info:
        action_items_export(format="markdown", output=None, limit=100)
    assert exc_info.value.code == 0
