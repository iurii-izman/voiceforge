"""Tests for llm/schemas (ActionItem deadline coercion and related)."""

from __future__ import annotations

from voiceforge.llm.schemas import ActionItem


def test_action_item_deadline_coerce_none_and_unknown() -> None:
    """ActionItem deadline validator: None, empty string, and <UNKNOWN> become None."""
    ai = ActionItem(description="Task", assignee=None, deadline=None)
    assert ai.deadline is None

    ai2 = ActionItem(description="Task", assignee=None, deadline="")
    assert ai2.deadline is None

    ai3 = ActionItem(description="Task", assignee=None, deadline="  ")
    assert ai3.deadline is None

    ai4 = ActionItem(description="Task", assignee=None, deadline="<UNKNOWN>")
    assert ai4.deadline is None

    ai5 = ActionItem(description="Task", assignee=None, deadline="   <UNKNOWN>   ")
    assert ai5.deadline is None
