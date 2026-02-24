"""Helpers for the `voiceforge history` command output and payloads."""

from __future__ import annotations

from typing import Any


def session_not_found_message(session_id: int) -> str:
    """Return user-facing message for absent session."""
    return f"Сессия {session_id} не найдена."


def session_not_found_error(session_id: int) -> tuple[str, str, bool]:
    """Build CLI error descriptor for absent session."""
    return "SESSION_NOT_FOUND", session_not_found_message(session_id), False


def build_session_detail_payload(session_id: int, segments: list[object], analysis: object | None) -> dict[str, Any]:
    """Build JSON-serializable payload for one session detail (includes template if set)."""
    return {
        "session_id": session_id,
        "segments": [vars(s) for s in segments],
        "analysis": vars(analysis) if analysis else None,
    }


def render_session_detail_lines(session_id: int, segments: list[object], analysis: object | None) -> list[str]:
    """Build text lines for one session detail view."""
    lines = [f"--- Сессия {session_id} ---"]
    for s in segments:
        speaker = getattr(s, "speaker", "")
        prefix = f"[{speaker}] " if speaker else ""
        lines.append(f"  {getattr(s, 'start_sec', 0.0):.1f}-{getattr(s, 'end_sec', 0.0):.1f}s {prefix}{getattr(s, 'text', '')}")
    if analysis:
        lines.append("--- Анализ ---")
        if getattr(analysis, "template", None):
            lines.append(f"  Шаблон: {analysis.template}")
        lines.append(f"  Модель: {getattr(analysis, 'model', '')}")
        for q in getattr(analysis, "questions", []):
            lines.append(f"  Вопрос: {q}")
        for a in getattr(analysis, "answers", []):
            lines.append(f"  Ответ: {a}")
    return lines


def build_sessions_payload(sessions: list[object]) -> dict[str, Any]:
    """Build JSON-serializable payload for list mode."""
    return {"sessions": [vars(s) for s in sessions]}


def empty_sessions_payload() -> dict[str, Any]:
    """Build JSON payload for empty sessions list mode."""
    return {"sessions": []}


def no_saved_sessions_message() -> str:
    return "Нет сохранённых сессий. Запустите voiceforge analyze."


def sessions_list_payload(sessions: list[object]) -> dict[str, Any]:
    """Build list-mode payload for history command, including empty state."""
    if not sessions:
        return empty_sessions_payload()
    return build_sessions_payload(sessions)


def sessions_list_lines(sessions: list[object]) -> list[str]:
    """Build text lines for history list mode, including empty state."""
    if not sessions:
        return [no_saved_sessions_message()]
    return render_sessions_table_lines(sessions)


def _format_analysis_block(analysis: object) -> list[str]:
    """Format '## Анализ' section lines."""
    lines = [f"- **Модель:** {getattr(analysis, 'model', '')}"]
    for attr, label in [("questions", "Вопросы"), ("answers", "Ответы/выводы"), ("recommendations", "Рекомендации")]:
        items = getattr(analysis, attr, [])
        if items:
            lines.append(f"- **{label}:**")
            for x in items:
                lines.append(f"  - {x}")
    action_items = getattr(analysis, "action_items", [])
    if action_items:
        lines.append("- **Действия:**")
        for ai in action_items:
            desc = ai.get("description", "") if isinstance(ai, dict) else getattr(ai, "description", "")
            assignee = ai.get("assignee") if isinstance(ai, dict) else getattr(ai, "assignee", None)
            lines.append(f"  - {desc} ({assignee})" if assignee else f"  - {desc}")
    cost = getattr(analysis, "cost_usd", None)
    if cost is not None:
        lines.append(f"- **Стоимость:** ${cost:.4f}")
    return lines


def _format_transcript_segment_lines(segments: list[object]) -> list[str]:
    """Format transcript segment lines for Markdown."""
    out: list[str] = []
    for s in segments:
        speaker = getattr(s, "speaker", "")
        prefix = f"**{speaker}** " if speaker else ""
        out.append(f"- {getattr(s, 'start_sec', 0.0):.1f}–{getattr(s, 'end_sec', 0.0):.1f}s {prefix}{getattr(s, 'text', '')}")
    return out


def build_session_markdown(
    session_id: int,
    segments: list[object],
    analysis: object | None,
    started_at: str | None = None,
) -> str:
    """Build Markdown text for one session (export)."""
    lines = [f"# Сессия {session_id}", ""]
    if started_at:
        date_part = started_at[:10] if len(started_at) >= 10 else started_at
        lines.append(f"**Дата:** {date_part}")
        lines.append("")
    if analysis and getattr(analysis, "template", None):
        lines.append(f"- **Шаблон:** {analysis.template}")
        lines.append("")
    lines.append("## Транскрипт")
    lines.append("")
    lines.extend(_format_transcript_segment_lines(segments))
    if analysis:
        lines.extend(["", "## Анализ", ""])
        lines.extend(_format_analysis_block(analysis))
    return "\n".join(lines)


def render_sessions_table_lines(sessions: list[object]) -> list[str]:
    """Build text table lines for session summaries."""
    lines = [
        "  id  started_at              duration  segments",
        "  --  ----------------------  --------  -------",
    ]
    for s in sessions:
        started_at = getattr(s, "started_at", "")
        started = started_at[:19] if len(started_at) >= 19 else started_at
        lines.append(
            f"  {getattr(s, 'id', 0):<3} {started}  {getattr(s, 'duration_sec', 0.0):>6.1f}s  {getattr(s, 'segments_count', 0)}"
        )
    return lines


# --- History command result builders (return (kind, data) for main.history to echo) ---


def history_action_items_result(log_db: Any, output: str) -> tuple[str, Any]:
    """Return ("json", payload) | ("lines", list[str]) | ("message", i18n_key)."""
    items = log_db.get_action_items(limit=100)
    if output == "json":
        payload = {
            "action_items": [
                {
                    "session_id": r.session_id,
                    "idx": r.idx_in_analysis,
                    "description": r.description,
                    "assignee": r.assignee,
                    "deadline": r.deadline,
                    "status": r.status,
                }
                for r in items
            ]
        }
        return ("json", payload)
    if not items:
        return ("message", "history.no_action_items")
    lines = []
    for r in items:
        assign = f" ({r.assignee})" if r.assignee else ""
        lines.append(f"  [{r.session_id}] #{r.idx_in_analysis} {r.status}: {r.description}{assign}")
    return ("lines", lines)


def history_search_result(log_db: Any, search: str, output: str) -> tuple[str, Any]:
    """Return ("json", payload) | ("lines", list[str]) | ("message", i18n_key)."""
    hits = log_db.search_transcripts(search.strip(), limit=30)
    if output == "json":
        payload = {
            "query": search,
            "hits": [{"session_id": s, "start_sec": st, "end_sec": e, "snippet": sn} for s, _tx, st, e, sn in hits],
        }
        return ("json", payload)
    if not hits:
        return ("message", "history.no_results")
    lines = [f"session_id={sid} | {start_sec:.1f}s | {snippet}" for sid, _text, start_sec, _end_sec, snippet in hits]
    return ("lines", lines)


def history_date_range_result(
    log_db: Any,
    date_str: str | None,
    from_str: str | None,
    to_str: str | None,
    output: str,
) -> tuple[str, Any]:
    """Return ("json", payload) | ("lines", list) | ("message", i18n_key) | ("error", i18n_key)."""
    from datetime import date as date_type

    if date_str is not None:
        if from_str or to_str:
            return ("error", "history.date_or_range")
        try:
            day = date_type.fromisoformat(date_str)
        except ValueError as e:
            return ("error", ("history.date_invalid", {"err": str(e)}))
        sessions = log_db.get_sessions_for_date(day)
    else:
        try:
            fd = date_type.fromisoformat(from_str or "")
            td = date_type.fromisoformat(to_str or "")
        except ValueError as e:
            return ("error", ("history.date_invalid", {"err": str(e)}))
        if fd > td:
            return ("error", "history.from_after_to")
        sessions = log_db.get_sessions_in_range(fd, td)
    if output == "json":
        return ("json", build_sessions_payload(sessions))
    if not sessions:
        return ("message", "history.no_sessions_period")
    return ("lines", render_sessions_table_lines(sessions))


def history_session_detail_result(log_db: Any, session_id: int, output: str) -> tuple[str, Any]:
    """Return ("json", payload) | ("lines", list) | ("md", str) | ("error", msg_or_key)."""
    detail = log_db.get_session_detail(session_id)
    if detail is None:
        return ("error", session_not_found_message(session_id))
    segments, analysis = detail
    if output == "json":
        return ("json", build_session_detail_payload(session_id, segments, analysis))
    if output == "md":
        meta = log_db.get_session_meta(session_id)
        started_at = meta[0] if meta else None
        return ("md", build_session_markdown(session_id, segments, analysis, started_at=started_at))
    return ("lines", render_session_detail_lines(session_id, segments, analysis))


def history_list_result(log_db: Any, last_n: int, output: str) -> tuple[str, Any]:
    """Return ("json", payload) | ("lines", list) | ("message", i18n_key)."""
    sessions = log_db.get_sessions(last_n=last_n)
    if output == "json":
        return ("json", build_sessions_payload(sessions) if sessions else empty_sessions_payload())
    if not sessions:
        return ("message", "history.no_sessions")
    return ("lines", render_sessions_table_lines(sessions))
