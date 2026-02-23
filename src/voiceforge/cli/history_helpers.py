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
    for s in segments:
        speaker = getattr(s, "speaker", "")
        prefix = f"**{speaker}** " if speaker else ""
        lines.append(f"- {getattr(s, 'start_sec', 0.0):.1f}–{getattr(s, 'end_sec', 0.0):.1f}s {prefix}{getattr(s, 'text', '')}")
    if analysis:
        lines.append("")
        lines.append("## Анализ")
        lines.append("")
        lines.append(f"- **Модель:** {getattr(analysis, 'model', '')}")
        qs = getattr(analysis, "questions", [])
        if qs:
            lines.append("- **Вопросы:**")
            for q in qs:
                lines.append(f"  - {q}")
        ans = getattr(analysis, "answers", [])
        if ans:
            lines.append("- **Ответы/выводы:**")
            for a in ans:
                lines.append(f"  - {a}")
        recs = getattr(analysis, "recommendations", [])
        if recs:
            lines.append("- **Рекомендации:**")
            for r in recs:
                lines.append(f"  - {r}")
        items = getattr(analysis, "action_items", [])
        if items:
            lines.append("- **Действия:**")
            for ai in items:
                desc = ai.get("description", "") if isinstance(ai, dict) else getattr(ai, "description", "")
                assignee = ai.get("assignee") if isinstance(ai, dict) else getattr(ai, "assignee", None)
                if assignee:
                    lines.append(f"  - {desc} ({assignee})")
                else:
                    lines.append(f"  - {desc}")
        cost = getattr(analysis, "cost_usd", None)
        if cost is not None:
            lines.append(f"- **Стоимость:** ${cost:.4f}")
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
