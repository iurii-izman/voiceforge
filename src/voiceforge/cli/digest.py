"""E10 (#133): Daily digest — aggregate sessions for a date, action items, cost."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from voiceforge.core.metrics import get_cost_for_date
from voiceforge.core.transcript_log import TranscriptLog


@dataclass
class DailyDigest:
    """Aggregated data for one day: sessions, action items, total cost."""

    day: date
    session_ids: list[int]
    session_summaries: list[tuple[int, str, float]]  # (id, started_at, duration_sec)
    action_items: list[dict[str, Any]]
    total_cost_usd: float


def build_daily_digest(log_db: TranscriptLog, day: date) -> DailyDigest:
    """Build digest for the given date: sessions, combined action items, cost."""
    sessions = log_db.get_sessions_for_date(day)
    session_summaries = [(s.id, s.started_at, s.duration_sec) for s in sessions]
    session_ids = [s.id for s in sessions]
    action_items: list[dict[str, Any]] = []
    for sid in session_ids:
        for row in log_db.get_action_items(limit=100, session_id=sid):
            action_items.append(
                {
                    "session_id": row.session_id,
                    "idx": row.idx_in_analysis,
                    "description": row.description,
                    "assignee": row.assignee,
                    "deadline": row.deadline,
                    "status": row.status,
                }
            )
    total_cost_usd = get_cost_for_date(day)
    return DailyDigest(
        day=day,
        session_ids=session_ids,
        session_summaries=session_summaries,
        action_items=action_items,
        total_cost_usd=total_cost_usd,
    )


def format_daily_digest_text(digest: DailyDigest) -> str:
    """Format digest as human-readable text (no LLM)."""
    lines = [
        f"# Daily digest — {digest.day.isoformat()}",
        "",
        f"Sessions: {len(digest.session_ids)}",
        f"Total cost: ${digest.total_cost_usd:.4f}",
        "",
    ]
    if digest.session_summaries:
        lines.append("## Sessions")
        lines.append("")
        for sid, started_at, duration_sec in digest.session_summaries:
            lines.append(f"- Session {sid}: {started_at[:19] if len(started_at) >= 19 else started_at} — {duration_sec:.0f}s")
        lines.append("")
    if digest.action_items:
        lines.append("## Action items")
        lines.append("")
        for ai in digest.action_items:
            sid = ai.get("session_id", "")
            desc = ai.get("description", "")
            assignee = ai.get("assignee") or ""
            status = ai.get("status", "")
            lines.append(f"- [{sid}] {desc}" + (f" ({assignee})" if assignee else "") + (f" — {status}" if status else ""))
        lines.append("")
    else:
        lines.append("## Action items")
        lines.append("")
        lines.append("None.")
    return "\n".join(lines)


def summarize_daily_with_llm(day: date, log_db: TranscriptLog) -> str:
    """E10 (#133): optional LLM summary of daily transcripts. Returns empty string on failure or no content."""
    raw = log_db.get_daily_transcript_text(day)
    text = (raw or "").strip()
    if len(text) < 50:
        return ""
    from voiceforge.core.config import Settings
    from voiceforge.core.secrets import set_env_keys_from_keyring

    set_env_keys_from_keyring()
    cfg = Settings()
    model, _ = cfg.get_effective_llm()
    if not model:
        model = "anthropic/claude-haiku-4-5"
    prompt = f"Summarize the following daily meeting transcripts in 3–5 sentences. Use the same language as the content.\n\n{text[:6000]}"
    try:
        from litellm import completion

        resp = completion(model=model, messages=[{"role": "user", "content": prompt}])
        if resp and resp.choices:
            return (resp.choices[0].message.content or "").strip()
    except Exception:
        pass
    return ""
