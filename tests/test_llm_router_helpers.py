"""Unit tests for llm.router helpers: _content_from_llm_response, _usage_and_cost_from_response, _is_claude_model. #56"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from voiceforge.llm import router


def test_is_claude_model() -> None:
    """_is_claude_model identifies Anthropic Claude models."""
    assert router._is_claude_model("anthropic/claude-haiku-4-5") is True
    assert router._is_claude_model("anthropic/claude-sonnet-4-6") is True
    assert router._is_claude_model("openai/gpt-4o-mini") is False
    assert router._is_claude_model("gemini/gemini-2.0-flash") is False


def test_content_from_llm_response() -> None:
    """_content_from_llm_response extracts content from completion response."""
    msg = SimpleNamespace(content='{"done":["x"]}', refusal=None, tool_calls=None)
    choice = SimpleNamespace(message=msg, finish_reason="stop")
    raw = SimpleNamespace(choices=[choice])
    content, raw_content = router._content_from_llm_response(raw, "test/model")
    assert content == '{"done":["x"]}'
    assert raw_content == '{"done":["x"]}'


def test_content_from_llm_response_empty_choices_raises() -> None:
    """_content_from_llm_response raises when choices is empty."""
    raw = SimpleNamespace(choices=[])
    with pytest.raises(RuntimeError, match="empty choices"):
        router._content_from_llm_response(raw, "test/model")


def test_usage_and_cost_from_response() -> None:
    """_usage_and_cost_from_response extracts usage and cost (mocked completion_cost)."""
    pytest.importorskip("litellm")
    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=20,
        prompt_tokens=10,
        completion_tokens=20,
        prompt_tokens_details=None,
        cache_creation_input_tokens=0,
    )
    raw = SimpleNamespace(usage=usage)
    with patch("litellm.completion_cost", return_value=0.001):
        inp, out, cache_read, cache_cre, cost = router._usage_and_cost_from_response(raw, "m1")
    assert inp == 10
    assert out == 20
    assert cache_read == 0
    assert cache_cre == 0
    assert cost == 0.001


def test_usage_and_cost_from_response_fallback_cost() -> None:
    """When completion_cost fails, cost from _hidden_params is used if present."""
    pytest.importorskip("litellm")
    usage = SimpleNamespace(
        input_tokens=5,
        output_tokens=10,
        prompt_tokens=5,
        completion_tokens=10,
        prompt_tokens_details=None,
        cache_creation_input_tokens=0,
    )
    raw = SimpleNamespace(usage=usage, _hidden_params={"response_cost": 0.002})
    with patch("litellm.completion_cost", side_effect=Exception("no cost")):
        inp, out, _cr, _cc, cost = router._usage_and_cost_from_response(raw, "m1")
    assert cost == 0.002
    assert inp == 5
    assert out == 10
