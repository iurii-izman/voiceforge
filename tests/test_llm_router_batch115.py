"""Behavioral coverage batch for llm.router (#115)."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from voiceforge.llm import router
from voiceforge.llm.schemas import LiveSummaryOutput, MeetingAnalysis, StandupOutput, StatusUpdateResponse


def test_router_prompt_loaders_prefer_repo_prompts(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.load_prompt", lambda name: f"loaded:{name}")
    monkeypatch.setattr(
        "voiceforge.llm.router.load_template_prompts",
        lambda: {
            "standup": "repo standup",
            "sprint_review": "repo sprint",
            "one_on_one": "repo one",
            "brainstorm": "repo brain",
            "interview": "repo interview",
        },
    )

    assert router._system_prompt() == "loaded:analysis"
    assert router._template_prompts()["standup"] == "repo standup"
    assert router._live_summary_system() == "loaded:live_summary"
    assert router._status_update_system() == "loaded:status_update"


def test_router_try_ollama_faq_returns_meeting_analysis_for_faq() -> None:
    fake_local_llm = SimpleNamespace(
        is_available=lambda: True,
        classify=lambda transcript, model: "faq",
        simple_answer=lambda transcript, context, model: "Use the documented process.",
    )
    with patch.dict(sys.modules, {"voiceforge.llm.local_llm": fake_local_llm}):
        result = router._try_ollama_faq("How do we deploy?", "deployment docs", "llama3", MeetingAnalysis)

    assert result is not None
    analysis, cost = result
    assert analysis.answers == ["Use the documented process."]
    assert cost == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("classification", "answer"),
    [
        ("meeting", "ignored"),
        ("faq", ""),
    ],
)
def test_router_try_ollama_faq_returns_none_for_non_faq_or_empty_answer(classification: str, answer: str) -> None:
    fake_local_llm = SimpleNamespace(
        is_available=lambda: True,
        classify=lambda transcript, model: classification,
        simple_answer=lambda transcript, context, model: answer,
    )
    with patch.dict(sys.modules, {"voiceforge.llm.local_llm": fake_local_llm}):
        result = router._try_ollama_faq("question", "context", "llama3", MeetingAnalysis)

    assert result is None


def test_analyze_meeting_uses_template_prompt_and_complete_structured(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_local_llm = SimpleNamespace(DEFAULT_MODEL="llama3")
    monkeypatch.setattr("voiceforge.llm.router._template_schema", lambda template: (StandupOutput, "template system"))
    monkeypatch.setattr("voiceforge.llm.router._try_ollama_faq", lambda *args, **kwargs: None)

    def fake_complete_structured(prompt, response_model, model):
        captured["prompt"] = prompt
        captured["response_model"] = response_model
        captured["model"] = model
        return (StandupOutput(done=["closed"]), 0.25)

    monkeypatch.setattr("voiceforge.llm.router.complete_structured", fake_complete_structured)
    with patch.dict(sys.modules, {"voiceforge.llm.local_llm": fake_local_llm}):
        result, cost = router.analyze_meeting(
            "raw transcript",
            "rag ctx",
            model=router.MODEL_GPT4O_MINI,
            template="standup",
            transcript_pre_redacted="safe transcript",
        )

    assert isinstance(result, StandupOutput)
    assert result.done == ["closed"]
    assert cost == pytest.approx(0.25)
    assert captured["response_model"] is StandupOutput
    assert captured["model"] == router.MODEL_GPT4O_MINI
    prompt = captured["prompt"]
    assert isinstance(prompt, list)
    assert prompt[0]["content"] == "template system"
    assert prompt[1]["content"].endswith("safe transcript")


def test_analyze_meeting_falls_back_after_ollama_error(monkeypatch) -> None:
    fake_local_llm = SimpleNamespace(DEFAULT_MODEL="llama3")
    monkeypatch.setattr(
        "voiceforge.llm.router._try_ollama_faq",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("ollama boom")),
    )
    monkeypatch.setattr(
        "voiceforge.llm.router.complete_structured",
        lambda **kwargs: (MeetingAnalysis(answers=["fallback"]), 0.1),
    )

    with patch.dict(sys.modules, {"voiceforge.llm.local_llm": fake_local_llm}):
        result, cost = router.analyze_meeting("transcript", "ctx")

    assert result.answers == ["fallback"]
    assert cost == pytest.approx(0.1)


def test_router_stream_accumulate_and_parse_emits_callback_and_returns_empty_when_needed(monkeypatch) -> None:
    callback: list[str | None] = []
    monkeypatch.setattr(
        "voiceforge.llm.router.stream_completion",
        lambda prompt, model=None: iter(
            [
                '{"questions":[],"answers":["done"]',
                ',"recommendations":[],"next_directions":[],"action_items":[]}',
            ]
        ),
    )

    parsed, cost = router._stream_accumulate_and_parse([], router.MODEL_GPT4O_MINI, callback.append, MeetingAnalysis)
    assert parsed.answers == ["done"]
    assert cost == pytest.approx(0.0)
    assert callback == [
        '{"questions":[],"answers":["done"]',
        ',"recommendations":[],"next_directions":[],"action_items":[]}',
        None,
    ]

    monkeypatch.setattr("voiceforge.llm.router.stream_completion", lambda prompt, model=None: iter([]))
    empty, empty_cost = router._stream_accumulate_and_parse([], router.MODEL_GPT4O_MINI, None, MeetingAnalysis)
    assert empty == MeetingAnalysis()
    assert empty_cost == pytest.approx(0.0)


def test_router_stream_accumulate_and_parse_raises_for_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.stream_completion", lambda prompt, model=None: iter(["not-json"]))

    with pytest.raises(ValueError):
        router._stream_accumulate_and_parse([], router.MODEL_GPT4O_MINI, None, MeetingAnalysis)


def test_analyze_meeting_stream_uses_template_parser(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_local_llm = SimpleNamespace(DEFAULT_MODEL="llama3")
    monkeypatch.setattr("voiceforge.llm.router._template_schema", lambda template: (StandupOutput, "template prompt"))
    monkeypatch.setattr("voiceforge.llm.router._try_ollama_faq", lambda *args, **kwargs: None)

    def fake_stream_parse(prompt, model_id, stream_callback, response_model):
        captured["prompt"] = prompt
        captured["model_id"] = model_id
        captured["stream_callback"] = stream_callback
        captured["response_model"] = response_model
        return (StandupOutput(done=["streamed"]), 0.0)

    monkeypatch.setattr("voiceforge.llm.router._stream_accumulate_and_parse", fake_stream_parse)
    with patch.dict(sys.modules, {"voiceforge.llm.local_llm": fake_local_llm}):
        result, cost = router.analyze_meeting_stream(
            "raw transcript",
            "rag ctx",
            model=router.MODEL_GPT4O_MINI,
            template="standup",
            transcript_pre_redacted="safe transcript",
            stream_callback="cb",
        )

    assert result.done == ["streamed"]
    assert cost == pytest.approx(0.0)
    assert captured["model_id"] == router.MODEL_GPT4O_MINI
    assert captured["response_model"] is StandupOutput
    assert captured["stream_callback"] == "cb"
    prompt = captured["prompt"]
    assert isinstance(prompt, list)
    assert prompt[0]["content"] == "template prompt"


def test_analyze_live_summary_builds_prompt_for_non_claude_and_claude(monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr("voiceforge.llm.router._live_summary_system", lambda: "live system")
    monkeypatch.setattr("voiceforge.llm.router.redact", lambda transcript, mode: "redacted transcript")

    def fake_complete_structured(prompt, response_model, model):
        captured.append({"prompt": prompt, "response_model": response_model, "model": model})
        return (LiveSummaryOutput(key_points=["point"]), 0.05)

    monkeypatch.setattr("voiceforge.llm.router.complete_structured", fake_complete_structured)

    non_claude, _ = router.analyze_live_summary("raw transcript", "ctx", model=router.MODEL_GPT4O_MINI)
    claude, _ = router.analyze_live_summary(
        "raw transcript",
        "ctx",
        model=router.MODEL_CLAUDE_HAIKU,
        transcript_pre_redacted="safe transcript",
    )

    assert non_claude.key_points == ["point"]
    assert claude.key_points == ["point"]
    assert captured[0]["response_model"] is LiveSummaryOutput
    assert captured[0]["prompt"][0]["content"] == "live system"
    assert captured[0]["prompt"][1]["content"].endswith("redacted transcript")
    assert captured[1]["prompt"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert captured[1]["prompt"][1]["content"].endswith("safe transcript")


def test_update_action_item_statuses_builds_prompts_for_non_claude_and_claude(monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    action_items = [
        {"description": "Ship release", "assignee": "Iurii"},
        {"description": "Write docs"},
    ]
    monkeypatch.setattr("voiceforge.llm.router._status_update_system", lambda: "status system")
    monkeypatch.setattr("voiceforge.llm.router.redact", lambda transcript, mode: "")

    def fake_complete_structured(prompt, response_model, model):
        captured.append({"prompt": prompt, "response_model": response_model, "model": model})
        return (StatusUpdateResponse(updates=[]), 0.02)

    monkeypatch.setattr("voiceforge.llm.router.complete_structured", fake_complete_structured)

    response, cost = router.update_action_item_statuses(action_items, "raw follow-up", model=router.MODEL_GPT4O_MINI)
    assert response.updates == []
    assert cost == pytest.approx(0.02)
    non_claude_prompt = captured[0]["prompt"]
    assert non_claude_prompt[0]["content"] == "status system"
    assert "[0] Ship release (assignee: Iurii)" in non_claude_prompt[1]["content"]
    assert "[1] Write docs" in non_claude_prompt[1]["content"]
    assert "raw follow-up" in non_claude_prompt[1]["content"]

    router.update_action_item_statuses(action_items, "follow-up", model=router.MODEL_CLAUDE_HAIKU)
    claude_prompt = captured[1]["prompt"]
    assert claude_prompt[0]["content"][0]["cache_control"] == {"type": "ephemeral"}


def test_analysis_prompt_non_claude_uses_redacted_text(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.redact", lambda transcript, mode: "clean transcript")
    monkeypatch.setattr("voiceforge.llm.router._system_prompt", lambda: "analysis system")

    prompt = router._analysis_prompt("raw transcript", "ctx", model_id=router.MODEL_GPT4O_MINI)

    assert prompt == [
        {"role": "system", "content": "analysis system"},
        {"role": "user", "content": "Context (RAG):\nctx\n\nTranscript:\nclean transcript"},
    ]


def test_content_from_llm_response_warns_and_returns_empty_json_for_missing_message_content(monkeypatch) -> None:
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(router.log, "warning", lambda *args, **kwargs: warnings.append((args, kwargs)))
    raw = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))])

    content, raw_content = router._content_from_llm_response(raw, "test/model")

    assert content == "{}"
    assert raw_content == ""
    assert warnings


def test_complete_structured_cached_hit_logs_cache_hit(monkeypatch) -> None:
    cache_events: list[bool] = []
    monkeypatch.setattr("voiceforge.core.metrics.log_response_cache", lambda hit: cache_events.append(hit))
    monkeypatch.setattr("voiceforge.llm.cache.get", lambda *args, **kwargs: (MeetingAnalysis(answers=["cached"]), 0.3))

    cached = router._complete_structured_cached("cache-key", MeetingAnalysis, 60)

    assert cached == (MeetingAnalysis(answers=["cached"]), 0.3)
    assert cache_events == [True]


def test_complete_structured_check_budget_warns_when_near_limit(monkeypatch) -> None:
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 8.5)
    monkeypatch.setattr(router.log, "warning", lambda *args, **kwargs: warnings.append((args, kwargs)))

    router._complete_structured_check_budget(SimpleNamespace(daily_budget_limit_usd=10.0))

    assert warnings
    assert warnings[0][0][0] == "llm.budget_alert"


def test_complete_structured_finish_logs_cache_and_observability(monkeypatch) -> None:
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    infos: list[tuple[tuple[object, ...], dict[str, object]]] = []
    llm_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    cache_writes: list[tuple[object, ...]] = []
    obs_calls: list[tuple[object, ...]] = []

    monkeypatch.setattr(router.log, "warning", lambda *args, **kwargs: warnings.append((args, kwargs)))
    monkeypatch.setattr(router.log, "info", lambda *args, **kwargs: infos.append((args, kwargs)))
    monkeypatch.setattr("voiceforge.core.metrics.log_llm_call", lambda *args, **kwargs: llm_calls.append((args, kwargs)))
    monkeypatch.setattr("voiceforge.llm.cache.set", lambda *args: cache_writes.append(args))
    monkeypatch.setattr(
        "voiceforge.core.observability.record_llm_call",
        lambda *args, **kwargs: obs_calls.append((*args, kwargs.get("success"))),
    )
    monkeypatch.setattr("voiceforge.llm.router._content_from_llm_response", lambda raw, model: ("{}", ""))
    monkeypatch.setattr("voiceforge.llm.router._usage_and_cost_from_response", lambda raw, model: (11, 7, 2, 1, 0.5))

    parsed, cost = router._complete_structured_finish(
        MeetingAnalysis(),
        SimpleNamespace(),
        router.MODEL_GPT4O_MINI,
        MeetingAnalysis,
        "cache-key",
        60,
    )

    assert parsed == MeetingAnalysis()
    assert cost == pytest.approx(0.5)
    assert warnings and warnings[0][0][0] == "llm.empty_structured_response"
    assert infos and infos[0][0][0] == "llm.cache"
    assert llm_calls and llm_calls[0][0][0] == router.MODEL_GPT4O_MINI
    assert cache_writes and cache_writes[0][0] == "cache-key"
    assert obs_calls == [(router.MODEL_GPT4O_MINI, 0.5, True)]


def test_complete_structured_returns_cache_hit_before_imports(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.core.config.Settings", lambda: SimpleNamespace(response_cache_ttl_seconds=60))
    monkeypatch.setattr("voiceforge.llm.cache.cache_key", lambda prompt, model, schema_name: "cache-key")
    monkeypatch.setattr(
        "voiceforge.llm.router._complete_structured_cached",
        lambda key, response_model, ttl: (MeetingAnalysis(answers=["cached-hit"]), 0.9),
    )

    result, cost = router.complete_structured([{"role": "user", "content": "hi"}], MeetingAnalysis, model="test/model")

    assert result.answers == ["cached-hit"]
    assert cost == pytest.approx(0.9)


def test_complete_structured_success_and_failure_paths(monkeypatch) -> None:
    log_cache_events: list[bool] = []
    observed: list[tuple[object, ...]] = []
    finished: list[tuple[object, ...]] = []

    monkeypatch.setattr("voiceforge.core.config.Settings", lambda: SimpleNamespace(response_cache_ttl_seconds=0))
    monkeypatch.setattr("voiceforge.core.metrics.log_response_cache", lambda hit: log_cache_events.append(hit))
    monkeypatch.setattr("voiceforge.llm.router._complete_structured_check_budget", lambda cfg: None)
    monkeypatch.setattr("voiceforge.llm.router.set_env_keys_from_keyring", lambda: None)
    monkeypatch.setattr("voiceforge.llm.router.wrap_completion", lambda fn: fn)
    monkeypatch.setattr(
        "voiceforge.llm.router._complete_structured_finish",
        lambda parsed, raw_used, model_id, response_model, key, ttl: (
            finished.append((parsed, raw_used, model_id, key, ttl)) or (parsed, 0.42)
        ),
    )
    monkeypatch.setattr(
        "voiceforge.core.observability.record_llm_call",
        lambda *args, **kwargs: observed.append((*args, kwargs.get("success"))),
    )

    parsed = MeetingAnalysis(answers=["ok"])
    raw_used = SimpleNamespace(source="raw")

    class FakeClient:
        def __init__(self, *, should_fail: bool) -> None:
            self.should_fail = should_fail

        def create_with_completion(self, **kwargs):
            if self.should_fail:
                raise RuntimeError("boom")
            return (parsed, raw_used)

    fake_litellm = SimpleNamespace(completion=lambda **kwargs: None)

    with patch.dict(
        sys.modules,
        {
            "instructor": SimpleNamespace(from_litellm=lambda wrapped: FakeClient(should_fail=False)),
            "litellm": fake_litellm,
        },
    ):
        result, cost = router.complete_structured(
            [{"role": "user", "content": "hi"}], MeetingAnalysis, model=router.MODEL_GPT4O_MINI
        )

    assert result == parsed
    assert cost == pytest.approx(0.42)
    assert log_cache_events == [False]
    assert finished and finished[0][2] == router.MODEL_GPT4O_MINI

    with (
        patch.dict(
            sys.modules,
            {
                "instructor": SimpleNamespace(from_litellm=lambda wrapped: FakeClient(should_fail=True)),
                "litellm": fake_litellm,
            },
        ),
        pytest.raises(RuntimeError, match="boom"),
    ):
        router.complete_structured([{"role": "user", "content": "hi"}], MeetingAnalysis, model=router.MODEL_GPT4O_MINI)

    assert observed[-1] == (router.MODEL_GPT4O_MINI, 0.0, False)


def test_stream_completion_yields_only_non_empty_content(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.set_env_keys_from_keyring", lambda: None)
    monkeypatch.setattr("voiceforge.llm.router.wrap_completion", lambda fn: lambda **kwargs: iter(fn(**kwargs)))

    def fake_completion(**kwargs):
        return [
            SimpleNamespace(choices=[SimpleNamespace(delta={"content": "a"})]),
            SimpleNamespace(choices=[SimpleNamespace(delta={"content": ""})]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="b"))]),
        ]

    with patch.dict(sys.modules, {"litellm": SimpleNamespace(completion=fake_completion)}):
        chunks = list(router.stream_completion([{"role": "user", "content": "hi"}], model=router.MODEL_GPT4O_MINI))

    assert chunks == ["a", "b"]
