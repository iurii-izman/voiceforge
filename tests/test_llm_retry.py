"""Tests for Instructor retry in complete_structured (#33)."""

from __future__ import annotations

from unittest.mock import patch

from voiceforge.llm.schemas import StandupOutput


def test_complete_structured_uses_instructor_with_max_retries() -> None:
    """complete_structured uses instructor.from_litellm and create_with_completion(max_retries=3) (#33)."""
    from types import SimpleNamespace

    from voiceforge.llm.router import complete_structured

    msg = SimpleNamespace(content='{"done":["Did X"],"planned":["Do Y"],"blockers":[]}', refusal=None, tool_calls=None)
    choice = SimpleNamespace(message=msg, finish_reason="stop")
    fake_raw = SimpleNamespace(
        choices=[choice],
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
            prompt_tokens=10,
            completion_tokens=20,
            prompt_tokens_details=None,
            cache_creation_input_tokens=0,
        ),
        _hidden_params={"response_cost": 0.001},
    )
    with patch("instructor.from_litellm") as mock_from_litellm:
        mock_client = mock_from_litellm.return_value
        mock_client.create_with_completion.return_value = (
            StandupOutput(done=["Did X"], planned=["Do Y"], blockers=[]),
            fake_raw,
        )
        prompt = [{"role": "user", "content": "Standup."}]
        parsed, cost = complete_structured(
            prompt,
            response_model=StandupOutput,
            model="anthropic/claude-haiku-4-5",
        )
    assert isinstance(parsed, StandupOutput)
    assert parsed.done == ["Did X"]
    assert cost >= 0
    mock_client.create_with_completion.assert_called_once()
    call_kw = mock_client.create_with_completion.call_args[1]
    assert call_kw.get("max_retries") == 3
    assert call_kw.get("response_model") is StandupOutput
