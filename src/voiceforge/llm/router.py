"""LiteLLM router with fallback; structured output via Instructor.
Budget $75/mo. Block 5.1: prompt caching for Claude."""

from __future__ import annotations

from typing import Any, TypeVar

import structlog
from pydantic import BaseModel

from voiceforge.core.secrets import set_env_keys_from_keyring
from voiceforge.llm.pii_filter import redact

log = structlog.get_logger()
TModel = TypeVar("TModel", bound=BaseModel)

# Anthropic: Opus 4.6 $5/$25, Sonnet 4.6 $3/$15, Haiku 4.5 $1/$5 (per MTok in/out)
MODEL_CLAUDE_OPUS = "anthropic/claude-opus-4-6"
MODEL_CLAUDE_SONNET = "anthropic/claude-sonnet-4-6"
MODEL_CLAUDE_HAIKU = "anthropic/claude-haiku-4-5"
MODEL_GPT4O_MINI = "openai/gpt-4o-mini"
MODEL_GEMINI_FLASH = "gemini/gemini-2.0-flash"

DEFAULT_MODEL = MODEL_CLAUDE_HAIKU
FALLBACK_MODELS = [MODEL_GPT4O_MINI, MODEL_GEMINI_FLASH, MODEL_CLAUDE_SONNET]

# System prompt for meeting analysis (~500 tokens). Cached for Claude (ephemeral) ~90% discount.
SYSTEM_PROMPT = """You are a meeting analyst. Your task is to analyze transcripts of meetings or
calls and produce structured output.

## Output structure
- **questions**: List of questions that were raised or left open in the meeting.
- **answers**: List of answers, conclusions, or agreed facts stated in the meeting.
- **recommendations**: List of recommendations or suggestions made.
- **next_directions**: List of next steps or follow-ups mentioned.
- **action_items**: List of concrete action items. Each has: description (what to do),
  assignee (who is responsible, or null if unknown), deadline (date or null if unknown).

## Rules
- Write in the same language as the transcript (e.g. Russian if the meeting was in Russian).
- Be concise: 3–7 items per list when possible.
- For action items, infer assignee and deadline only when clearly stated; otherwise use null.
- Do not invent content that is not present in the transcript.
- Output only valid JSON matching the schema (questions, answers, recommendations,
  next_directions, action_items)."""


def _is_claude_model(model_id: str) -> bool:
    """True if model is Anthropic Claude (prompt caching supported)."""
    return "anthropic/" in model_id and "claude" in model_id.lower()


def analyze_meeting(
    transcript: str,
    context: str = "",
    *,
    model: str | None = None,
    template: str | None = None,
    transcript_pre_redacted: str | None = None,
) -> tuple[Any, float]:
    """Return (MeetingAnalysis, cost_usd).
    Block 10.2: transcript_pre_redacted skips in-call redact (use when PII already done in pipeline)."""
    from voiceforge.llm.schemas import MeetingAnalysis

    _ = template

    model_id = model or DEFAULT_MODEL
    try:
        from voiceforge.llm.local_llm import classify, is_available, simple_answer

        if is_available():
            kind = classify(transcript)
            if kind == "faq":
                answer = simple_answer(transcript, context)
                if answer:
                    stub = MeetingAnalysis(
                        questions=[],
                        answers=[answer],
                        recommendations=[],
                        next_directions=[],
                        action_items=[],
                    )
                    log.info("llm.ollama_faq", used=True)
                    return (stub, 0.0)
    except ImportError:
        pass
    except Exception as e:
        log.warning("llm.ollama_fallback_failed", error=str(e))
    result, cost = complete_structured(
        prompt=_analysis_prompt(
            transcript,
            context,
            model_id=model_id,
            transcript_pre_redacted=transcript_pre_redacted,
        ),
        response_model=MeetingAnalysis,
        model=model_id,
    )
    return (result, cost)


def _analysis_prompt(
    transcript: str,
    context: str,
    model_id: str = "",
    transcript_pre_redacted: str | None = None,
) -> list[dict[str, Any]]:
    """Build messages for completion. For Claude: system content with cache_control (ephemeral)."""
    text_for_llm = transcript_pre_redacted if transcript_pre_redacted is not None else redact(transcript)
    user_content = f"Context (RAG):\n{context}\n\nTranscript:\n{text_for_llm}"
    if _is_claude_model(model_id):
        return [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
                ],
            },
            {"role": "user", "content": user_content},
        ]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def complete_structured(
    prompt: list[dict[str, Any]],
    response_model: type[TModel],
    model: str | None = None,
) -> tuple[TModel, float]:
    """Call LLM with fallbacks; return (validated Pydantic model, cost_usd)."""
    from voiceforge.core.metrics import log_llm_call, log_response_cache

    query = (prompt[-1].get("content") or "") if prompt else ""
    log_response_cache(False)

    set_env_keys_from_keyring()
    try:
        from litellm import completion, completion_cost
    except ImportError as e:
        raise ImportError("Install [llm] extras: uv sync --extra llm") from e

    model_id = model or DEFAULT_MODEL
    fallbacks = [m for m in FALLBACK_MODELS if m != model_id][:3]
    raw = completion(
        model=model_id,
        messages=prompt,
        fallbacks=fallbacks if fallbacks else None,
        max_tokens=1024,
        response_format=response_model,
    )
    choices = getattr(raw, "choices", None) or []
    if not choices:
        raise RuntimeError("LLM returned empty choices")
    first = choices[0]
    message = getattr(first, "message", None)
    raw_content = (getattr(message, "content", None) or "") if message is not None else ""
    if not raw_content.strip():
        log.warning("llm.empty_response", model=model_id)
    content = raw_content or "{}"
    parsed = response_model.model_validate_json(content)
    # Detect all-empty structured response (LLM returned nothing useful)
    model_fields = getattr(response_model, "model_fields", None)
    if isinstance(model_fields, dict):
        all_empty = all(not getattr(parsed, field_name, None) for field_name in model_fields)
        if all_empty and not raw_content.strip():
            log.warning("llm.empty_structured_response", model=model_id)
    u = getattr(raw, "usage", None)
    inp = (getattr(u, "input_tokens", None) or getattr(u, "prompt_tokens", None) or 0) if u else 0
    out = (getattr(u, "output_tokens", None) or getattr(u, "completion_tokens", None) or 0) if u else 0
    cache_read = 0
    cache_creation = 0
    if u:
        details = getattr(u, "prompt_tokens_details", None)
        if details is not None:
            cache_read = int(getattr(details, "cached_tokens", 0) or 0)
        cache_creation = int(getattr(u, "cache_creation_input_tokens", 0) or 0)
    try:
        cost = float(completion_cost(completion_response=raw, model=model_id) or 0)
    except Exception as e:
        log.warning("llm.cost_calculation_failed", error=str(e), model=model_id)
        cost = 0.0
        if hasattr(raw, "_hidden_params") and isinstance(raw._hidden_params, dict):
            cost = float(raw._hidden_params.get("response_cost") or 0)
    if cache_read > 0 or cache_creation > 0:
        log.info(
            "llm.cache",
            model=model_id,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_creation,
        )
    log_llm_call(
        model_id,
        inp,
        out,
        cost,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_creation,
    )
    _ = query
    return (parsed, cost)
