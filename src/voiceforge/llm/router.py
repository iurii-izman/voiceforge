"""LiteLLM router with fallback; structured output via Instructor.
Budget $75/mo. Block 5.1: prompt caching for Claude."""

from __future__ import annotations

from typing import Any, TypeVar

import structlog
from pydantic import BaseModel

from voiceforge.core.contracts import BudgetExceeded
from voiceforge.core.secrets import set_env_keys_from_keyring
from voiceforge.llm.pii_filter import redact
from voiceforge.llm.prompt_loader import load_prompt, load_template_prompts

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

# Fallback prompts (used when prompts/ files are missing). C1 (#41): prefer prompt_loader.
_SYSTEM_PROMPT_FALLBACK = """You are a meeting analyst. Your task is to analyze transcripts of meetings or
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

_TEMPLATE_PROMPTS_FALLBACK = {
    "standup": """You are a standup meeting analyst. Extract from the transcript:
- done: what was done since last standup
- planned: what is planned next
- blockers: blockers or impediments
Write in the same language as the transcript. Be concise. Output only valid JSON matching the schema.""",
    "sprint_review": """You are a sprint review analyst. Extract from the transcript:
- demos: what was demoed
- metrics: metrics or KPIs mentioned
- feedback: feedback from stakeholders
Write in the same language as the transcript. Be concise. Output only valid JSON matching the schema.""",
    "one_on_one": """You are a 1:1 meeting analyst. Extract from the transcript:
- mood: how the person is feeling (short)
- growth: growth or development topics
- blockers: blockers or concerns
- action_items: action items agreed (description, assignee, deadline when stated)
Write in the same language as the transcript. Be concise. Output only valid JSON matching the schema.""",
    "brainstorm": """You are a brainstorm session analyst. Extract from the transcript:
- ideas: ideas proposed
- voting: votes or preferences expressed
- next_steps: next steps agreed
Write in the same language as the transcript. Be concise. Output only valid JSON matching the schema.""",
    "interview": """You are an interview analyst. Extract from the transcript:
- questions_asked: questions asked to the candidate
- assessment: assessment or evaluation points
- decision: hire / no hire / follow-up (or empty if not decided)
Write in the same language as the transcript. Be concise. Output only valid JSON matching the schema.""",
}


def _system_prompt() -> str:
    """System prompt for meeting analysis (from prompts/analysis.txt or fallback)."""
    return load_prompt("analysis") or _SYSTEM_PROMPT_FALLBACK


def _template_prompts() -> dict[str, str]:
    """Template prompts (from prompts/template_*.txt or fallback)."""
    return load_template_prompts() or _TEMPLATE_PROMPTS_FALLBACK


def _is_claude_model(model_id: str) -> bool:
    """True if model is Anthropic Claude (prompt caching supported)."""
    return "anthropic/" in model_id and "claude" in model_id.lower()


def _template_schema(template: str):
    """Return response model and system prompt for template, or (None, None)."""
    from voiceforge.llm.schemas import (
        BrainstormOutput,
        InterviewOutput,
        OneOnOneOutput,
        SprintReviewOutput,
        StandupOutput,
    )

    prompts = _template_prompts()
    schemas = {
        "standup": (StandupOutput, prompts["standup"]),
        "sprint_review": (SprintReviewOutput, prompts["sprint_review"]),
        "one_on_one": (OneOnOneOutput, prompts["one_on_one"]),
        "brainstorm": (BrainstormOutput, prompts["brainstorm"]),
        "interview": (InterviewOutput, prompts["interview"]),
    }
    return schemas.get(template, (None, None))


def _try_ollama_faq(
    transcript: str,
    context: str,
    local_model: str,
    response_model: type[Any],
) -> tuple[Any, float] | None:
    """If Ollama is available and transcript is FAQ, return (MeetingAnalysis stub, 0.0); else None."""
    try:
        from voiceforge.llm.local_llm import classify, is_available, simple_answer
        from voiceforge.llm.schemas import MeetingAnalysis
    except ImportError:
        return None
    if not is_available() or response_model is not MeetingAnalysis:
        return None
    kind = classify(transcript, model=local_model)
    if kind != "faq":
        return None
    answer = simple_answer(transcript, context, model=local_model)
    if not answer:
        return None
    log.info("llm.ollama_faq", used=True)
    return (
        MeetingAnalysis(
            questions=[],
            answers=[answer],
            recommendations=[],
            next_directions=[],
            action_items=[],
        ),
        0.0,
    )


def analyze_meeting(
    transcript: str,
    context: str = "",
    *,
    model: str | None = None,
    template: str | None = None,
    transcript_pre_redacted: str | None = None,
    ollama_model: str | None = None,
    pii_mode: str = "ON",
) -> tuple[Any, float]:
    """Return (MeetingAnalysis | template schema instance, cost_usd).
    Block 1: template in (standup, sprint_review, one_on_one, brainstorm, interview) uses template schema.
    Block 4: ollama_model for local classify/simple_answer.
    Block 10.2: transcript_pre_redacted skips in-call redact (use when PII already done in pipeline).
    Block 11: pii_mode (OFF | ON | EMAIL_ONLY) used when transcript_pre_redacted is None."""
    from voiceforge.llm.local_llm import DEFAULT_MODEL as OLLAMA_DEFAULT
    from voiceforge.llm.schemas import MeetingAnalysis

    model_id = model or DEFAULT_MODEL
    response_model: type[MeetingAnalysis] | None = MeetingAnalysis
    system_prompt_override: str | None = None
    if template:
        schema_cls, prompt = _template_schema(template)
        if schema_cls is not None and prompt is not None:
            response_model = schema_cls
            system_prompt_override = prompt

    local_model = (ollama_model or OLLAMA_DEFAULT).strip() or OLLAMA_DEFAULT
    try:
        ollama_result = _try_ollama_faq(transcript, context, local_model, response_model)
        if ollama_result is not None:
            return ollama_result
    except Exception as e:
        log.warning("llm.ollama_fallback_failed", error=str(e))

    if response_model is None:
        response_model = MeetingAnalysis
    result, cost = complete_structured(
        prompt=_analysis_prompt(
            transcript,
            context,
            model_id=model_id,
            transcript_pre_redacted=transcript_pre_redacted,
            system_prompt_override=system_prompt_override,
            pii_mode=pii_mode,
        ),
        response_model=response_model,
        model=model_id,
    )
    return (result, cost)


def _live_summary_system() -> str:
    """Live summary system prompt (from prompts/live_summary.txt or fallback)."""
    fallback = """You are a meeting analyst. Given a transcript fragment, produce a SHORT live summary:
- key_points: 3–5 bullet points (main topics, decisions, outcomes).
- action_items: only concrete action items with description; assignee and deadline if clearly stated.

Write in the same language as the transcript. Be very concise. Output only valid JSON matching the schema (key_points, action_items)."""
    return load_prompt("live_summary") or fallback


def analyze_live_summary(
    transcript: str,
    context: str = "",
    *,
    model: str | None = None,
    transcript_pre_redacted: str | None = None,
    pii_mode: str = "ON",
) -> tuple[Any, float]:
    """Return (LiveSummaryOutput, cost_usd). Block 10: short key points + action items for listen --live-summary."""
    from voiceforge.llm.schemas import LiveSummaryOutput

    model_id = model or DEFAULT_MODEL
    text_for_llm = transcript_pre_redacted if transcript_pre_redacted is not None else redact(transcript, mode=pii_mode)
    user_content = f"Context (RAG):\n{context}\n\nTranscript:\n{text_for_llm}"
    live_sys = _live_summary_system()
    prompt = [
        {"role": "system", "content": live_sys},
        {"role": "user", "content": user_content},
    ]
    if _is_claude_model(model_id):
        prompt = [
            {
                "role": "system",
                "content": [  # type: ignore[dict-item]
                    {"type": "text", "text": live_sys, "cache_control": {"type": "ephemeral"}},
                ],
            },
            {"role": "user", "content": user_content},
        ]
    result, cost = complete_structured(prompt, response_model=LiveSummaryOutput, model=model_id)
    return (result, cost)


def _status_update_system() -> str:
    """Status update system prompt (from prompts/status_update.txt or fallback)."""
    fallback = """You are an assistant that updates action item statuses. You are given:
1. A list of action items from a previous meeting (each with index 0, 1, 2, ...).
2. The transcript of the FOLLOW-UP meeting.

Your task: determine which action items were mentioned in the follow-up as DONE or CANCELLED. Output only the list of (id, status) for items that were clearly stated as done or cancelled. Use the same language as the transcript for any reasoning; output only valid JSON matching the schema (updates: list of {id, status})."""
    return load_prompt("status_update") or fallback


def update_action_item_statuses(
    action_items: list[dict[str, Any]],
    next_meeting_transcript: str,
    *,
    model: str | None = None,
    pii_mode: str = "ON",
) -> tuple[Any, float]:
    """Return (StatusUpdateResponse, cost_usd). Block 2: which items are done/cancelled per next meeting."""
    from voiceforge.llm.schemas import StatusUpdateResponse

    if not action_items:
        return (StatusUpdateResponse(updates=[]), 0.0)
    model_id = model or DEFAULT_MODEL
    transcript_for_llm = redact(next_meeting_transcript, mode=pii_mode) or next_meeting_transcript
    lines = []
    for i, ai in enumerate(action_items):
        desc = ai.get("description", "")
        assignee = ai.get("assignee") or ""
        lines.append(f"  [{i}] {desc}" + (f" (assignee: {assignee})" if assignee else ""))
    user_content = (
        "Action items from previous meeting:\n" + "\n".join(lines) + "\n\nTranscript of follow-up meeting:\n" + transcript_for_llm
    )
    prompt = [
        {"role": "system", "content": _status_update_system()},
        {"role": "user", "content": user_content},
    ]
    result, cost = complete_structured(prompt, response_model=StatusUpdateResponse, model=model_id)
    return (result, cost)


def _analysis_prompt(
    transcript: str,
    context: str,
    model_id: str = "",
    transcript_pre_redacted: str | None = None,
    system_prompt_override: str | None = None,
    pii_mode: str = "ON",
) -> list[dict[str, Any]]:
    """Build messages for completion. For Claude: system content with cache_control (ephemeral)."""
    text_for_llm = transcript_pre_redacted if transcript_pre_redacted is not None else redact(transcript, mode=pii_mode)
    user_content = f"Context (RAG):\n{context}\n\nTranscript:\n{text_for_llm}"
    system_text = system_prompt_override if system_prompt_override is not None else _system_prompt()
    if _is_claude_model(model_id):
        return [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}},
                ],
            },
            {"role": "user", "content": user_content},
        ]
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_content},
    ]


def _content_from_llm_response(raw: Any, model_id: str) -> tuple[str, str]:
    """Extract content and raw_content from completion response. Raises if no choices."""
    choices = getattr(raw, "choices", None) or []
    if not choices:
        raise RuntimeError("LLM returned empty choices")
    first = choices[0]
    message = getattr(first, "message", None)
    raw_content = (getattr(message, "content", None) or "") if message is not None else ""
    if not raw_content.strip():
        log.warning("llm.empty_response", model=model_id)
    return (raw_content or "{}", raw_content)


def _usage_and_cost_from_response(raw: Any, model_id: str) -> tuple[int, int, int, int, float]:
    """Extract input_tokens, output_tokens, cache_read, cache_creation, cost_usd from response."""
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
        from litellm import completion_cost

        cost = float(completion_cost(completion_response=raw, model=model_id) or 0)
    except Exception as e:
        log.warning("llm.cost_calculation_failed", error=str(e), model=model_id)
        cost = 0.0
        if hasattr(raw, "_hidden_params") and isinstance(raw._hidden_params, dict):
            cost = float(raw._hidden_params.get("response_cost") or 0)
    return (inp, out, cache_read, cache_creation, cost)


def complete_structured(
    prompt: list[dict[str, Any]],
    response_model: type[TModel],
    model: str | None = None,
) -> tuple[TModel, float]:
    """Call LLM with fallbacks; return (validated Pydantic model, cost_usd).
    Uses Instructor retry (max_retries=3) with validation context on parse errors (#33).
    Pre-call budget check: reject if daily cost >= daily_budget_limit_usd (#38).
    Response cache: content-hash key, TTL from config (#44)."""
    from voiceforge.core.config import Settings
    from voiceforge.core.metrics import get_cost_today, log_llm_call, log_response_cache
    from voiceforge.llm.cache import cache_key
    from voiceforge.llm.cache import get as cache_get
    from voiceforge.llm.cache import set as cache_set

    cfg = Settings()
    ttl = int(getattr(cfg, "response_cache_ttl_seconds", 0) or 0)
    model_id = model or DEFAULT_MODEL
    if ttl > 0:
        key = cache_key(prompt, model_id, response_model.__name__)
        cached = cache_get(key, response_model, ttl)
        if cached is not None:
            parsed, cost = cached
            log_response_cache(True)
            return (parsed, cost)
    cost_today = get_cost_today()
    daily_limit = cfg.daily_budget_limit_usd or 0.0
    if daily_limit > 0 and cost_today >= daily_limit:
        raise BudgetExceeded(
            f"Daily LLM budget exceeded: ${cost_today:.2f} >= ${daily_limit:.2f}. "
            "Adjust VOICEFORGE_DAILY_BUDGET_LIMIT_USD or wait until tomorrow."
        )
    if daily_limit > 0 and cost_today >= 0.8 * daily_limit:
        log.warning(
            "llm.budget_alert",
            cost_today_usd=round(cost_today, 4),
            daily_limit_usd=round(daily_limit, 4),
            pct=round(100 * cost_today / daily_limit, 1),
        )

    log_response_cache(False)
    set_env_keys_from_keyring()
    try:
        import instructor
        from litellm import completion
    except ImportError as e:
        raise ImportError("Install [llm] extras: uv sync --extra llm") from e

    fallbacks = [m for m in FALLBACK_MODELS if m != model_id][:3]
    client = instructor.from_litellm(completion)
    try:
        parsed, raw_used = client.create_with_completion(
            messages=prompt,
            response_model=response_model,
            max_retries=3,
            model=model_id,
            fallbacks=fallbacks if fallbacks else None,
            max_tokens=1024,
        )
    except Exception as e:
        try:
            from voiceforge.core.observability import record_llm_call

            record_llm_call(model_id, 0.0, success=False)
        except ImportError:
            pass
        log.warning(
            "llm.instructor_retries_exhausted",
            model=model_id,
            error=str(e),
            response_model=response_model.__name__,
        )
        raise

    _, raw_content = _content_from_llm_response(raw_used, model_id)
    model_fields = getattr(response_model, "model_fields", None)
    if isinstance(model_fields, dict) and all(not getattr(parsed, f, None) for f in model_fields) and not raw_content.strip():
        log.warning("llm.empty_structured_response", model=model_id)

    inp, out, cache_read, cache_creation, cost = _usage_and_cost_from_response(raw_used, model_id)
    if cache_read > 0 or cache_creation > 0:
        log.info("llm.cache", model=model_id, cache_read_input_tokens=cache_read, cache_creation_input_tokens=cache_creation)
    log_llm_call(model_id, inp, out, cost, cache_read_input_tokens=cache_read, cache_creation_input_tokens=cache_creation)
    if ttl > 0:
        cache_set(key, model_id, response_model.__name__, parsed, cost, ttl)
    try:
        from voiceforge.core.observability import record_llm_call

        record_llm_call(model_id, cost, success=True)
    except ImportError:
        pass
    return (parsed, cost)
