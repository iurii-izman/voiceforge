"""Tests for llm/schemas (ActionItem deadline coercion, CopilotFastCards KC6)."""

from __future__ import annotations

from datetime import date

from voiceforge.llm.schemas import ActionItem, CopilotDeepCards, CopilotFastCards


def test_action_item_deadline_valid_string_passes() -> None:
    """ActionItem deadline validator: valid date string is passed through (return v branch)."""
    ai = ActionItem(description="Task", assignee=None, deadline="2025-01-15")
    assert ai.deadline == date(2025, 1, 15)


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


def test_copilot_fast_cards_schema_kc6() -> None:
    """KC6 (#178): CopilotFastCards schema validates and defaults empty lists."""
    empty = CopilotFastCards()
    assert empty.answer == []
    assert empty.dos == []
    assert empty.donts == []
    assert empty.clarify == []
    assert empty.confidence == 0.0

    filled = CopilotFastCards(
        answer=["Say the price is $45K/year."],
        dos=["Mention SLA 99.9%"],
        donts=["Don't promise discounts"],
        clarify=["Which product tier?"],
        confidence=0.85,
    )
    assert len(filled.answer) == 1
    assert len(filled.dos) == 1
    assert len(filled.donts) == 1
    assert len(filled.clarify) == 1
    assert filled.confidence == 0.85


def test_copilot_deep_cards_schema_kc7() -> None:
    """KC7 (#179): CopilotDeepCards schema validates and defaults empty."""
    empty = CopilotDeepCards()
    assert empty.risks == []
    assert empty.strategy == ""
    assert empty.emotion is None

    filled = CopilotDeepCards(
        risks=["No discount without approval.", "SLA 99.9% only on Enterprise."],
        strategy="Steer to pricing page and offer a demo.",
        emotion="Client seems cautious; keep tone factual.",
    )
    assert len(filled.risks) == 2
    assert "pricing" in filled.strategy
    assert filled.emotion is not None
