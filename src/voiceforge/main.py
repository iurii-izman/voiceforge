"""VoiceForge CLI entrypoint (alpha 0.2 core)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess  # nosec B404 -- pandoc for PDF export, args from our paths
import sys
import threading
import time
from datetime import UTC
from pathlib import Path
from typing import Any

import structlog
import typer

from voiceforge.cli.history_helpers import (
    build_session_export_notion,
    build_session_export_otter,
    build_session_markdown,
    history_action_items_result,
    history_date_range_result,
    history_list_result,
    history_search_result,
    history_session_detail_result,
    session_not_found_message,
)
from voiceforge.cli.meeting import run_meeting
from voiceforge.cli.setup import run_config_init, run_setup_wizard
from voiceforge.cli.status_helpers import (
    get_doctor_data,
    get_doctor_text,
    get_status_data,
    get_status_detailed_data,
    get_status_detailed_text,
    get_status_text,
)
from voiceforge.cli.watch_helpers import get_watch_banner, install_watch_stop_signal_handlers
from voiceforge.core.config import Settings, get_default_config_yaml_path
from voiceforge.core.contracts import (
    BudgetExceeded,
    build_cli_error_payload,
    build_cli_success_payload,
    extract_error_message,
)
from voiceforge.core.fs import ensure_private_dir, ensure_private_file
from voiceforge.core.tracing import bind_trace_id
from voiceforge.i18n import t

log = structlog.get_logger()
app = typer.Typer(help="VoiceForge — local-first AI assistant (alpha 0.2)")
action_items_app = typer.Typer(help=t("cli.action_items_help"))
app.add_typer(action_items_app, name="action-items")
calendar_app = typer.Typer(help="CalDAV calendar poll (keyring: caldav_url, caldav_username, caldav_password)")
app.add_typer(calendar_app, name="calendar")


def _get_app_version() -> str:
    """Return VoiceForge package version (block 55)."""
    try:
        from importlib.metadata import version

        return version("voiceforge")
    except Exception:
        return "0.2.0-alpha.1"


def _is_first_run() -> bool:
    """E7 (#130): True if no DB and no config file (first-run: show setup hint)."""
    from voiceforge.core.transcript_log import DB_NAME

    data_base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    db_path = Path(data_base) / "voiceforge" / DB_NAME
    config_path = get_default_config_yaml_path()
    return not db_path.exists() and not config_path.is_file()


@app.callback(invoke_without_command=True)
def _cli_trace(ctx: typer.Context) -> None:
    """Bind trace_id; when no command given, show help; first-run shows setup hint."""
    bind_trace_id()
    if ctx.invoked_subcommand is None:
        if _is_first_run():
            typer.echo(t("setup.welcome_first_run"), err=True)
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app.command()
def version() -> None:
    """Print VoiceForge version (block 55)."""
    typer.echo(_get_app_version())


@app.command()
def setup() -> None:
    """E7 (#130): Guided setup wizard — PipeWire, language, Whisper model, API keys, config."""
    run_setup_wizard()


config_app = typer.Typer(help="Config: init (generate voiceforge.yaml)")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(
    overwrite: bool = typer.Option(False, "--overwrite", "-f", help="Overwrite existing voiceforge.yaml"),
) -> None:
    """E7 (#130): Generate voiceforge.yaml with defaults and comments (quick alternative to full setup)."""
    run_config_init(overwrite=overwrite)


_INDEX_EXTENSIONS = (
    ".pdf",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".docx",
    ".txt",
    ".odt",
    ".rtf",
)
_I18N_ERROR_LLM_FAILED = "error.llm_failed"
_I18N_ERROR_BUDGET_EXCEEDED = "error.budget_exceeded"
_I18N_TEMPLATE_ACTIONS = "template.one_on_one.actions"
_HELP_OUTPUT_TEXT_JSON = "Формат вывода: text | json"
_HELP_OUTPUT_TEXT_JSON_MD = "Формат вывода: text | json | md (md только с --id)"
_SERVICE_UNIT_NAME = "voiceforge.service"
_ISO_UTC_SUFFIX = "+00:00"
_ICAL_DT_FORMAT = "%Y%m%dT%H%M%SZ"
_I18N_CALENDAR_POLL_ERROR = "calendar.poll_error"


def _calendar_export_ical_fail(err: str) -> None:
    """Echo calendar error and hint; raise SystemExit(1). S3776."""
    typer.echo(t(_I18N_CALENDAR_POLL_ERROR, msg=err), err=True)
    hint = _hint_for_error(err)
    if hint:
        typer.echo(hint, err=True)
    raise SystemExit(1)


def _emit_success(output: str, data: dict[str, Any], text: str) -> None:
    """Emit CLI success payload as json or plain text."""
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload(data), ensure_ascii=False))
        return
    typer.echo(text)


def _calendar_poll_emit(output: str, minutes: int, events: list[dict[str, Any]]) -> None:
    """Emit calendar poll result as json or text."""
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload({"events": events, "minutes": minutes}), ensure_ascii=False))
        return
    if not events:
        typer.echo(t("calendar.poll_no_events", minutes=minutes))
        return
    typer.echo(t("calendar.poll_events", minutes=minutes))
    for ev in events:
        typer.echo(t("calendar.poll_line", summary=ev.get("summary", ""), start_iso=ev.get("start_iso", "")))


def _calendar_create_emit(output: str, event_uid: str) -> None:
    """Emit create-from-session success as json or text."""
    _emit_success(output, {"event_uid": event_uid}, f"Created calendar event: {event_uid}")


def _sessions_to_ical_fetch_sessions(log_db: Any, from_date: str | None, to_date: str | None, limit: int) -> list[Any]:
    """Return sessions for iCal export; on date parse error echo and raise SystemExit(1). S3776."""
    from datetime import date as date_type

    if from_date is not None and to_date is not None:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
        except ValueError:
            typer.echo(t("history.date_invalid", err=from_date + " / " + to_date), err=True)
            raise SystemExit(1)
        return log_db.get_sessions_in_range(fd, td)
    return log_db.get_sessions(last_n=limit, offset=0)


def _iso_to_ical_utc(iso_str: str) -> str:
    """Convert ISO datetime string to iCal format 20250307T100000Z (S3776)."""
    if not iso_str:
        return ""
    from datetime import datetime as dt_class

    try:
        s = iso_str.strip().replace("Z", _ISO_UTC_SUFFIX)
        dt = dt_class.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime(_ICAL_DT_FORMAT)
    except (ValueError, TypeError):
        return ""


def _session_to_vevent_lines(session: Any) -> list[str]:
    """Build VEVENT lines for one session (S3776)."""
    from datetime import datetime as dt_class
    from datetime import timedelta

    start_ical = _iso_to_ical_utc(getattr(session, "started_at", "") or "")
    if not start_ical:
        return []
    dur_sec = float(getattr(session, "duration_sec", 0) or 0)
    started = (getattr(session, "started_at", "") or "").replace("Z", _ISO_UTC_SUFFIX)
    end_dt = dt_class.fromisoformat(started)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=UTC)
    end_dt = end_dt + timedelta(seconds=dur_sec)
    end_ical = end_dt.strftime(_ICAL_DT_FORMAT)
    sid = getattr(session, "id", 0) or 0
    return [
        "BEGIN:VEVENT",
        f"UID:session-{sid}@voiceforge",
        f"DTSTAMP:{start_ical}",
        f"DTSTART:{start_ical}",
        f"DTEND:{end_ical}",
        f"SUMMARY:Session {sid}",
        f"DESCRIPTION:VoiceForge session {sid}",
        "END:VEVENT",
    ]


def _get_config() -> Settings:
    return Settings()


def _cli_error_payload(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return build_cli_error_payload(code=code, message=message, retryable=retryable)


def _cli_success_payload(data: dict[str, Any]) -> dict[str, Any]:
    return build_cli_success_payload(data=data)


def _extract_error_message(payload: str) -> str | None:
    return extract_error_message(payload, legacy_prefix=t("error.legacy_prefix"))


def _hint_for_error(message: str) -> str | None:
    """Return a one-line hint for typical errors (block 56)."""
    if not message:
        return None
    msg_lower = message.lower()
    if "missing keyring" in msg_lower or ("keyring" in msg_lower and "set" not in msg_lower):
        return "Подсказка: keyring set voiceforge caldav_url (и caldav_username, caldav_password). См. docs/runbooks/keyring-keys-reference.md"
    if "audio" in msg_lower or "pipewire" in msg_lower or "микрофон" in msg_lower:
        return "Подсказка: проверьте PipeWire (systemctl --user status pipewire) и доступ микрофона."
    if "daemon" in msg_lower or "демон" in msg_lower:
        return "Подсказка: запустите voiceforge daemon в отдельном терминале."
    return None


def _speaker_for_interval(start: float, end: float, diar_segments: list[Any]) -> str:
    best = ""
    best_overlap = 0.0
    for d in diar_segments:
        o_start = max(start, getattr(d, "start", 0.0))
        o_end = min(end, getattr(d, "end", 0.0))
        if o_end > o_start:
            overlap = o_end - o_start
            if overlap > best_overlap:
                best_overlap = overlap
                best = getattr(d, "speaker", "") or ""
    return best


def _format_template_standup(d: dict) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    lines, answers = [], []
    for key, label in [
        ("done", "template.standup.done"),
        ("planned", "template.standup.planned"),
        ("blockers", "template.standup.blockers"),
    ]:
        lines.append(f"--- {t(label)} ---")
        for x in d.get(key, []):
            lines.append(f"  • {x}")
            answers.append(x)
    return (lines, answers, [])


def _format_template_sprint_review(d: dict) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    lines, answers = [], []
    for label_key, key in [
        ("template.sprint_review.demos", "demos"),
        ("template.sprint_review.metrics", "metrics"),
        ("template.sprint_review.feedback", "feedback"),
    ]:
        lines.append(f"--- {t(label_key)} ---")
        for x in d.get(key, []):
            lines.append(f"  • {x}")
            answers.append(x)
    return (lines, answers, [])


def _format_template_one_on_one(d: dict) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    lines, answers, action_items = [], [], []
    if d.get("mood"):
        lines.append(f"--- {t('template.one_on_one.mood')} ---\n  {d['mood']}")
        answers.append(d["mood"])
    for label_key, key in [("template.one_on_one.growth", "growth"), ("template.one_on_one.blockers", "blockers")]:
        lines.append(f"--- {t(label_key)} ---")
        for x in d.get(key, []):
            lines.append(f"  • {x}")
            answers.append(x)
    lines.append(f"--- {t(_I18N_TEMPLATE_ACTIONS)} ---")
    for ai in d.get("action_items", []):
        desc = ai.get("description", "")
        who = (ai.get("assignee") or "").strip()
        lines.append(f"  • {desc}" + (f" ({who})" if who else ""))
        action_items.append(ai)
    return (lines, answers, action_items)


def _format_template_brainstorm(d: dict) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    lines, answers = [], []
    for label_key, key in [
        ("template.brainstorm.ideas", "ideas"),
        ("template.brainstorm.voting", "voting"),
        ("template.brainstorm.next_steps", "next_steps"),
    ]:
        lines.append(f"--- {t(label_key)} ---")
        for x in d.get(key, []):
            lines.append(f"  • {x}")
            answers.append(x)
    return (lines, answers, [])


def _format_template_interview(d: dict) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    lines, answers = [], []
    for label_key, key in [
        ("template.interview.questions_asked", "questions_asked"),
        ("template.interview.assessment", "assessment"),
    ]:
        lines.append(f"--- {t(label_key)} ---")
        for x in d.get(key, []):
            lines.append(f"  • {x}")
            answers.append(x)
    if d.get("decision"):
        lines.append(f"--- {t('template.interview.decision')} ---\n  {d['decision']}")
        answers.append(d["decision"])
    return (lines, answers, [])


_TEMPLATE_FORMATTERS: dict[str, Any] = {
    "standup": _format_template_standup,
    "sprint_review": _format_template_sprint_review,
    "one_on_one": _format_template_one_on_one,
    "brainstorm": _format_template_brainstorm,
    "interview": _format_template_interview,
}


def _format_template_result(template: str, llm_result: Any) -> tuple[list[str], dict[str, Any]]:
    """Format template LLM result to display lines and analysis_for_log (for log_session)."""
    d = llm_result.model_dump(mode="json") if hasattr(llm_result, "model_dump") else {}
    formatter = _TEMPLATE_FORMATTERS.get(template)
    if formatter is None:
        lines, answers_for_log, action_items_for_log = [], [], []
    else:
        lines, answers_for_log, action_items_for_log = formatter(d)
    analysis_for_log = {
        "template": template,
        "questions": [],
        "answers": answers_for_log,
        "recommendations": [],
        "action_items": action_items_for_log,
    }
    return (lines, analysis_for_log)


def _format_meeting_analysis_lines(llm_result: Any) -> list[str]:
    """Format default MeetingAnalysis to display lines."""
    lines = ["--- Вопросы ---"]
    for q in llm_result.questions:
        lines.append(f"  • {q}")
    lines.append("--- Ответы/выводы ---")
    for a in llm_result.answers:
        lines.append(f"  • {a}")
    lines.append("--- Рекомендации ---")
    for r in llm_result.recommendations:
        lines.append(f"  • {r}")
    lines.append("--- Действия ---")
    for ai in llm_result.action_items:
        who = (ai.assignee or "").strip()
        lines.append(f"  • {ai.description} ({who})" if who and who.upper() != "<UNKNOWN>" else f"  • {ai.description}")
    return lines


def _build_analysis_for_log_default(llm_result: Any, cfg: Any, cost_usd: float, model: str | None = None) -> dict[str, Any]:
    """Build analysis_for_log dict for default MeetingAnalysis. E6: model is effective_llm when provided."""
    return {
        "model": model if model is not None else cfg.default_llm,
        "questions": llm_result.questions,
        "answers": llm_result.answers,
        "recommendations": llm_result.recommendations,
        "action_items": [ai.model_dump(mode="json") for ai in llm_result.action_items],
        "cost_usd": cost_usd,
    }


def run_analyze_pipeline(
    seconds: int,
    template: str | None = None,
    dry_run: bool = False,
    stream_callback: Any = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Run core analyze pipeline and return (display_text, segments_for_log, analysis_for_log).
    If stream_callback is set, LLM output is streamed via stream_callback(delta) (#91)."""
    bind_trace_id()  # one trace_id per pipeline run (CLI or daemon worker)
    cfg = _get_config()
    try:
        from voiceforge.core.pipeline import AnalysisPipeline

        with AnalysisPipeline(cfg) as pipeline:
            result, err = pipeline.run(seconds)
    except ImportError:
        return (t("error.install_deps"), [], {})

    if err is not None:
        return (err, [], {})
    if result is None:
        return (t("error.pipeline_empty"), [], {})

    segments = result.segments
    transcript = result.transcript
    diar_segments = result.diar_segments
    context = result.context
    transcript_redacted = result.transcript_redacted
    pipeline_warnings: list[str] = getattr(result, "warnings", None) or []

    segments_for_log = [
        {
            "start_sec": s.start,
            "end_sec": s.end,
            "speaker": _speaker_for_interval(s.start, s.end, diar_segments),
            "text": s.text or "",
        }
        for s in segments
    ]

    if dry_run:
        msg = (
            f"Dry-run: would analyze last {seconds}s, template={template or 'default'}, "
            f"{len(segments)} segments, transcript ~{len(transcript or '')} chars. No LLM call."
        )
        return (msg, segments_for_log, {})

    effective_model, is_ollama_fallback = cfg.get_effective_llm()
    if effective_model is None:
        return (t("error.no_llm_backend"), [], {})

    if is_ollama_fallback:
        log.info("llm.ollama_fallback", model=effective_model, message="No API keys found. Using Ollama as LLM backend.")

    try:
        from voiceforge.llm.router import analyze_meeting, analyze_meeting_stream, get_budget_warning_if_near_limit

        budget_warn = get_budget_warning_if_near_limit(cfg)
        if stream_callback is not None:
            llm_result, cost_usd = analyze_meeting_stream(
                transcript,
                context=context,
                model=effective_model,
                template=template,
                transcript_pre_redacted=transcript_redacted,
                ollama_model=cfg.ollama_model,
                pii_mode=cfg.pii_mode,
                stream_callback=stream_callback,
            )
        else:
            llm_result, cost_usd = analyze_meeting(
                transcript,
                context=context,
                model=effective_model,
                template=template,
                transcript_pre_redacted=transcript_redacted,
                ollama_model=cfg.ollama_model,
                pii_mode=cfg.pii_mode,
            )
    except ImportError:
        return (t("error.install_llm_deps"), [], {})
    except BudgetExceeded as e:
        log.warning("analyze.budget_exceeded", error=str(e))
        return (t(_I18N_ERROR_BUDGET_EXCEEDED, msg=str(e)), [], {})
    except Exception as e:
        from voiceforge.core.preflight import NetworkUnavailableError

        if isinstance(e, NetworkUnavailableError):
            suffix = "" if e.i18n_key == "error.ollama_not_running" else (". " + t("error.ollama_suggestion"))
            return (t(e.i18n_key) + suffix, [], {})
        log.warning("analyze.llm_failed", error=str(e))
        return (t(_I18N_ERROR_LLM_FAILED, e=str(e)), [], {})

    header_lines: list[str] = list(pipeline_warnings)
    if budget_warn:
        header_lines.append(budget_warn)

    if template and hasattr(llm_result, "model_dump"):
        lines, analysis_for_log = _format_template_result(template, llm_result)
        analysis_for_log["model"] = effective_model
        analysis_for_log["cost_usd"] = cost_usd
        return ("\n".join(header_lines + lines), segments_for_log, analysis_for_log)

    lines = _format_meeting_analysis_lines(llm_result)
    analysis_for_log = _build_analysis_for_log_default(llm_result, cfg, cost_usd, effective_model)
    return ("\n".join(header_lines + lines), segments_for_log, analysis_for_log)


def run_live_summary_pipeline(seconds: int) -> tuple[list[str], float]:
    """Block 10: run pipeline on last N seconds, return (display lines, cost_usd). No session log."""
    cfg = _get_config()
    try:
        from voiceforge.core.pipeline import AnalysisPipeline

        with AnalysisPipeline(cfg) as pipeline:
            result, err = pipeline.run(seconds)
    except ImportError:
        return ([t("error.install_deps")], 0.0)

    if err is not None or result is None:
        return ([err or t("error.pipeline_empty")], 0.0)

    transcript = result.transcript
    context = result.context
    transcript_redacted = result.transcript_redacted

    effective_model, _ = cfg.get_effective_llm()
    if effective_model is None:
        return ([t("error.no_llm_backend")], 0.0)

    try:
        from voiceforge.llm.router import analyze_live_summary

        live_result, cost_usd = analyze_live_summary(
            transcript,
            context=context,
            model=effective_model,
            transcript_pre_redacted=transcript_redacted,
            pii_mode=cfg.pii_mode,
        )
    except ImportError:
        return ([t("error.install_llm_deps")], 0.0)
    except BudgetExceeded as e:
        log.warning("live_summary.budget_exceeded", error=str(e))
        return ([t(_I18N_ERROR_BUDGET_EXCEEDED, msg=str(e))], 0.0)
    except Exception as e:
        log.warning("live_summary.llm_failed", error=str(e))
        return ([t(_I18N_ERROR_LLM_FAILED, e=str(e))], 0.0)

    lines = _format_live_summary_lines(live_result)
    return (lines, cost_usd)


def _format_live_key_points(live_result: Any) -> list[str]:
    """Format key_points section (S3776)."""
    lines: list[str] = []
    if getattr(live_result, "key_points", None):
        lines.append("--- Ключевые моменты ---")
        for k in live_result.key_points:
            if k and k.strip():
                lines.append(f"  • {k.strip()}")
    return lines


def _format_live_action_items(live_result: Any) -> list[str]:
    """Format action_items section (S3776)."""
    lines: list[str] = []
    if getattr(live_result, "action_items", None):
        lines.append(f"--- {t(_I18N_TEMPLATE_ACTIONS)} ---")
        for ai in live_result.action_items:
            desc = getattr(ai, "description", "") or ""
            if not desc.strip():
                continue
            who = (getattr(ai, "assignee", None) or "").strip()
            lines.append(f"  • {desc} ({who})" if who and who.upper() != "<UNKNOWN>" else f"  • {desc}")
    return lines


def _format_live_summary_lines(live_result: Any) -> list[str]:
    """Format live summary result to display lines."""
    lines = _format_live_key_points(live_result) + _format_live_action_items(live_result)
    if not lines:
        lines = ["(ничего существенного)"]
    return lines


def _streaming_listen_worker(
    capture: Any,
    cfg: Settings,
    stop_event: threading.Event,
) -> None:
    """Block 10.1: stream STT in a thread — partial/final to stdout (CLI listen)."""
    try:
        from voiceforge.stt import get_transcriber_for_config
        from voiceforge.stt.streaming import StreamingSegment, StreamingTranscriber
    except ImportError:
        return
    transcriber = get_transcriber_for_config(cfg)
    lang = getattr(cfg, "language", "auto")
    language_hint = None if lang in ("auto", "") else lang

    def on_partial(text: str) -> None:
        if text:
            sys.stdout.write(f"\r  [partial] {text}    ")
            sys.stdout.flush()

    def on_final(segment: StreamingSegment) -> None:
        t = getattr(segment, "text", "") or ""
        if not t.strip():
            return
        sys.stdout.write("\n  " + t + "\n")
        sys.stdout.flush()

    stream = StreamingTranscriber(
        transcriber,
        sample_rate=cfg.sample_rate,
        language=language_hint,
        on_partial=on_partial,
        on_final=on_final,
    )
    chunk_sec, interval_sec = 2.0, 1.5
    get_chunk = getattr(capture, "get_chunk", None)
    if not get_chunk:
        return
    while not stop_event.wait(timeout=interval_sec):
        try:
            mic, _ = get_chunk(chunk_sec)
            if mic.size >= cfg.sample_rate * int(chunk_sec) * 0.5:
                stream.process_chunk(mic, start_offset_sec=0.0)
        except Exception as e:
            log.warning("listen.streaming_stt.failed", error=str(e))


def _live_summary_listen_worker(stop_event: threading.Event, interval_sec: int) -> None:
    """Block 10: periodically run live summary on ring buffer and print to stdout."""
    while not stop_event.wait(timeout=interval_sec):
        lines, cost = run_live_summary_pipeline(interval_sec)
        err_prefix = t("error.legacy_prefix").rstrip(":")
        if not lines or (len(lines) == 1 and lines[0].startswith(err_prefix)):
            continue
        sys.stdout.write("\n--- Live summary ---\n")
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.write(f"  (cost ${cost:.4f})\n")
        sys.stdout.flush()


@app.command()
def listen(
    duration: int = typer.Option(0, help="Секунды (0 = бесконечно)"),
    stream: bool = typer.Option(
        None,
        "--stream/--no-stream",
        help="Показывать partial/final транскрипт в реальном времени (по умолчанию — из конфига streaming_stt)",
    ),
    live_summary: bool = typer.Option(
        False,
        "--live-summary/--no-live-summary",
        help="Периодически выводить краткий саммари (ключевые моменты + действия) по последним 90 с",
    ),
) -> None:
    """Start microphone/system recording to ring buffer for analyze."""
    cfg = _get_config()
    from voiceforge.core.preflight import check_disk_space, check_pipewire

    pw_err = check_pipewire()
    if pw_err:
        typer.echo(t(pw_err), err=True)
        typer.echo(t("error.pipewire_fix"), err=True)
        raise SystemExit(1)
    data_dir = cfg.get_data_dir()
    disk_err, disk_warn = check_disk_space(data_dir)
    if disk_err:
        typer.echo(t(disk_err), err=True)
        raise SystemExit(1)
    if disk_warn:
        typer.echo(t(disk_warn), err=True)
    try:
        from voiceforge.audio.capture import AudioCapture
    except ImportError:
        typer.echo(t("error.audio_module_not_found"), err=True)
        hint = _hint_for_error(t("error.audio_module_not_found"))
        if hint:
            typer.echo(hint, err=True)
        raise SystemExit(1) from None

    ring_path = cfg.get_ring_file_path()
    Path(ring_path).parent.mkdir(parents=True, exist_ok=True)
    capture = AudioCapture(
        sample_rate=cfg.sample_rate,
        buffer_seconds=cfg.ring_seconds,
        monitor_source=cfg.monitor_source,
    )
    capture.start()

    stop = False
    streaming_stt = stream if stream is not None else cfg.streaming_stt
    streaming_stop = threading.Event()
    streaming_thread: threading.Thread | None = None
    if streaming_stt:
        streaming_thread = threading.Thread(
            target=_streaming_listen_worker,
            args=(capture, cfg, streaming_stop),
            daemon=True,
        )
        streaming_thread.start()
        typer.echo(t("listen.streaming_on"), err=True)

    live_summary_stop = threading.Event()
    live_summary_thread: threading.Thread | None = None
    if live_summary:
        interval_sec = getattr(cfg, "live_summary_interval_sec", 90)
        live_summary_thread = threading.Thread(
            target=_live_summary_listen_worker,
            args=(live_summary_stop, interval_sec),
            daemon=True,
        )
        live_summary_thread.start()
        typer.echo(t("listen.live_summary_on", interval=interval_sec), err=True)

    def on_signal(*args: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    started = time.monotonic()
    try:
        while not stop and (duration <= 0 or (time.monotonic() - started) < duration):
            time.sleep(2)
            mic, _mon = capture.get_chunk(cfg.ring_seconds)
            if mic.size > 0:
                ring = Path(ring_path)
                tmp = ring.with_suffix(".tmp")
                tmp.write_bytes(mic.tobytes())
                os.replace(tmp, ring)
    finally:
        streaming_stop.set()
        if streaming_thread:
            streaming_thread.join(timeout=4.0)
        live_summary_stop.set()
        if live_summary_thread:
            interval_sec = getattr(cfg, "live_summary_interval_sec", 90)
            live_summary_thread.join(timeout=interval_sec + 60.0)
        if streaming_stt:
            sys.stdout.write("\n")
            sys.stdout.flush()
        capture.stop()


_TEMPLATE_CHOICES = ["standup", "sprint_review", "one_on_one", "brainstorm", "interview"]


@app.command()
def meeting(
    template: str | None = typer.Option(
        None,
        "--template",
        help="Meeting template: standup, sprint_review, one_on_one, brainstorm, interview (passed to analyze).",
    ),
    no_analyze: bool = typer.Option(
        False,
        "--no-analyze",
        help="Only listen; do not run analyze on Ctrl+C.",
    ),
    seconds: int | None = typer.Option(
        None,
        "--seconds",
        help="Analyze last N seconds on exit; default: entire buffer.",
    ),
) -> None:
    """One-shot meeting: listen, optional smart-trigger auto-analyze, then analyze on Ctrl+C."""
    cfg = _get_config()
    if template is not None and template not in _TEMPLATE_CHOICES:
        typer.echo(t("analyze.unknown_template", template=template, choices=", ".join(_TEMPLATE_CHOICES)), err=True)
        raise SystemExit(1)
    run_meeting(cfg, template=template, no_analyze=no_analyze, seconds=seconds)


def _analyze_echo_success(
    session_id: int | None,
    display_text: str | None,
    analysis_for_log: dict,
    output: str,
) -> None:
    """Echo analyze result (JSON or text) to reduce cognitive complexity (S3776)."""
    if output == "json":
        typer.echo(
            json.dumps(
                _cli_success_payload(
                    {
                        "session_id": session_id,
                        "display_text": display_text,
                        "analysis": analysis_for_log,
                    }
                ),
                ensure_ascii=False,
            )
        )
    else:
        if session_id is not None:
            typer.echo(f"session_id={session_id}")
        typer.echo(display_text)


@app.command()
def analyze(
    seconds: int | None = typer.Option(
        None,
        "--seconds",
        help="Last N seconds of ring buffer; omit to analyze entire buffer (ring_seconds from config).",
    ),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Шаблон встречи: standup, sprint_review, one_on_one, brainstorm, interview",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Показать, что будет проанализировано (транскрипт, сегменты), без вызова LLM (блок 60).",
    ),
) -> None:
    """Analyze ring-buffer fragment: transcribe -> diarize -> rag -> llm."""
    cfg = _get_config()
    if seconds is None:
        seconds = int(cfg.ring_seconds)
    if template is not None and template not in _TEMPLATE_CHOICES:
        typer.echo(t("analyze.unknown_template", template=template, choices=", ".join(_TEMPLATE_CHOICES)), err=True)
        raise SystemExit(1)
    from voiceforge.core.preflight import check_disk_space

    disk_err, disk_warn = check_disk_space(cfg.get_data_dir())
    if disk_err:
        typer.echo(t(disk_err), err=True)
        raise SystemExit(1)
    if disk_warn:
        typer.echo(t(disk_warn), err=True)
    if not dry_run and output == "text" and sys.stderr.isatty():
        # Block 72: rough estimate (transcribe + LLM) for user feedback
        est_lo = max(10, seconds // 5 + 5)
        est_hi = min(120, max(20, seconds // 2 + 30))
        typer.echo(f"Analyzing… (≈ {est_lo}–{est_hi} s)", err=True)
    display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds, template=template, dry_run=dry_run)
    error_message = _extract_error_message(display_text)
    if error_message is not None:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("ANALYZE_FAILED", error_message), ensure_ascii=False))
        else:
            typer.echo(error_message, err=True)
        raise SystemExit(1)

    if dry_run:
        if output == "json":
            typer.echo(
                json.dumps(
                    _cli_success_payload({"dry_run": True, "message": display_text, "segments_count": len(segments_for_log)}),
                    ensure_ascii=False,
                )
            )
        else:
            typer.echo(display_text)
        return

    session_id: int | None = None
    try:
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        session_id = log_db.log_session(
            segments=segments_for_log,
            duration_sec=seconds,
            model=analysis_for_log.get("model", ""),
            questions=analysis_for_log.get("questions"),
            answers=analysis_for_log.get("answers"),
            recommendations=analysis_for_log.get("recommendations"),
            action_items=analysis_for_log.get("action_items"),
            cost_usd=analysis_for_log.get("cost_usd", 0.0),
            template=analysis_for_log.get("template"),
        )
        log_db.close()
    except Exception as e:
        log.warning("analyze.log_failed", error=str(e))

    try:
        from voiceforge.core.telegram_notify import notify_analyze_done

        notify_analyze_done(session_id, (display_text or "")[:400])
    except Exception as e:
        log.debug("analyze.telegram_notify_failed", error=str(e))

    try:
        from voiceforge.core.desktop_notify import notify_analyze_done as desktop_notify_analyze_done

        desktop_notify_analyze_done((display_text or "")[:80])
    except Exception:
        pass  # notify-send optional (E1)

    _analyze_echo_success(session_id, display_text, analysis_for_log, output)


def _action_item_status_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    base_path = Path(base).resolve()
    home = Path.home()
    if not str(base_path).startswith(str(home)):
        base_path = home / ".local" / "share"
    return base_path / "voiceforge" / "action_item_status.json"


def _load_action_item_status() -> dict[str, str]:
    path = _action_item_status_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save_action_item_status(data: dict[str, str]) -> None:
    path = _action_item_status_path()
    ensure_private_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))  # NOSONAR S2083: path under home
    ensure_private_file(path)


def _action_items_update_validate(log_db: Any, from_session: int, next_session: int) -> tuple[Any, Any, Any, str]:
    """Validate and return (detail_from, detail_next, action_items, transcript_next). Raises SystemExit on error."""
    detail_from = log_db.get_session_detail(from_session)
    detail_next = log_db.get_session_detail(next_session)
    if detail_from is None:
        typer.echo(t("history.session_not_found", session_id=from_session), err=True)
        raise SystemExit(1)
    if detail_next is None:
        typer.echo(t("history.session_not_found", session_id=next_session), err=True)
        raise SystemExit(1)
    segments_next, _ = detail_next
    analysis_from = detail_from[1]
    if analysis_from is None:
        typer.echo(t("action_items.no_analysis", session_id=from_session), err=True)
        raise SystemExit(1)
    action_items = analysis_from.action_items
    if not action_items:
        typer.echo(t("action_items.none_to_update"), err=True)
        raise SystemExit(0)
    transcript_next = "\n".join(s.text for s in segments_next).strip()
    if not transcript_next:
        typer.echo(t("action_items.no_segments", session_id=next_session), err=True)
        raise SystemExit(1)
    return (detail_from, detail_next, action_items, transcript_next)


def _action_items_update_persist(from_session: int, updates: list[tuple[int, str]]) -> None:
    """Save updates to status JSON and DB."""
    from voiceforge.core.transcript_log import TranscriptLog

    status_data = _load_action_item_status()
    for idx, status in updates:
        status_data[f"{from_session}:{idx}"] = status
    _save_action_item_status(status_data)
    try:
        log_db2 = TranscriptLog()
        log_db2.update_action_item_statuses_in_db(from_session, updates)
        log_db2.close()
    except Exception as _e:
        structlog.get_logger().debug("action_items DB update failed", exc_info=_e)


def _action_items_update_echo(
    output: str, from_session: int, next_session: int, updates: list[tuple[int, str]], cost_usd: float, save: bool
) -> None:
    """Emit JSON or text output for action-items update."""
    if output == "json":
        typer.echo(
            json.dumps(
                _cli_success_payload(
                    {
                        "from_session": from_session,
                        "next_session": next_session,
                        "updates": [{"id": i, "status": s} for i, s in updates],
                        "cost_usd": cost_usd,
                    }
                ),
                ensure_ascii=False,
            )
        )
    else:
        for idx, status in updates:
            typer.echo(f"  [{idx}] {status}")
        if updates and save:
            typer.echo(t("action_items.saved_to", path=str(_action_item_status_path())))


@action_items_app.command("update")
def action_items_update(
    from_session: int = typer.Option(..., "--from-session", help="ID сессии с action items"),
    next_session: int = typer.Option(..., "--next-session", help="ID сессии (встреча), по которой обновляем статусы"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
    save: bool = typer.Option(True, "--save/--no-save", help="Сохранить статусы в action_item_status.json"),
) -> None:
    """Обновить статусы action items из сессии --from-session по транскрипту встречи --next-session."""
    try:
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.llm.router import update_action_item_statuses
    except ImportError as e:
        typer.echo(t("error.generic", msg=str(e)), err=True)
        raise SystemExit(1) from None

    log_db = TranscriptLog()
    try:
        _, _, action_items, transcript_next = _action_items_update_validate(log_db, from_session, next_session)
    finally:
        log_db.close()

    cfg = _get_config()
    effective_model, _ = cfg.get_effective_llm()
    if effective_model is None:
        typer.echo(t("error.no_llm_backend"), err=True)
        raise SystemExit(1) from None
    try:
        response, cost_usd = update_action_item_statuses(
            action_items,
            transcript_next,
            model=effective_model,
            pii_mode=cfg.pii_mode,
        )
    except BudgetExceeded as e:
        typer.echo(t(_I18N_ERROR_BUDGET_EXCEEDED, msg=str(e)), err=True)
        raise SystemExit(1) from None
    except Exception as e:
        typer.echo(t(_I18N_ERROR_LLM_FAILED, e=str(e)), err=True)
        raise SystemExit(1) from None

    updates = [(u.id, u.status) for u in response.updates]
    if save and updates:
        _action_items_update_persist(from_session, updates)
    _action_items_update_echo(output, from_session, next_session, updates, cost_usd, save)


def _index_directory(indexer: Any, p: Path, exclude_patterns: list[str] | None = None) -> tuple[int, set[str]]:
    """Index all supported files under directory p. Block 74: skip paths matching rag_exclude_patterns."""
    import fnmatch

    total = 0
    indexed_paths: set[str] = set()
    patterns = exclude_patterns or []
    for ext in _INDEX_EXTENSIONS:
        for f in sorted(p.glob(f"**/*{ext}")):
            if not f.is_file():
                continue
            path_str = str(f.resolve())
            if any(fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(f.name, pat) for pat in patterns):
                continue
            try:
                total += indexer.add_file(f)
                indexed_paths.add(path_str)
            except Exception as e:
                typer.echo(t("index.skip_file", path=str(f), e=str(e)), err=True)
    return (total, indexed_paths)


@app.command()
def index(
    path: str = typer.Argument(help="Путь к файлу или папке (PDF, MD, HTML, DOCX, TXT, ODT, RTF)"),
    db: str | None = typer.Option(None, "--db", help="Путь к RAG-БД"),
) -> None:
    """Index knowledge files into SQLite-vec + FTS5 database."""
    cfg = _get_config()
    db_path = db or cfg.get_rag_db_path()
    p = Path(path)
    if not p.exists():
        typer.echo(t("error.path_not_found", path=path), err=True)
        raise SystemExit(1)

    try:
        from voiceforge.rag.indexer import KnowledgeIndexer
    except ImportError:
        typer.echo(t("error.rag_deps"), err=True)
        raise SystemExit(1) from None

    indexer = KnowledgeIndexer(db_path)
    try:
        if p.is_file():
            if p.suffix.lower() not in _INDEX_EXTENSIONS:
                typer.echo(t("index.unsupported_format", suffix=p.suffix), err=True)
                raise SystemExit(1)
            added = indexer.add_file(p)
            typer.echo(t("index.chunks_added", n=added))
            return
        if p.is_dir():
            total, indexed_paths = _index_directory(indexer, p, getattr(cfg, "rag_exclude_patterns", None) or [])
            pruned = indexer.prune_sources_not_in(indexed_paths, only_under_prefix=str(p.resolve()))
            if pruned:
                typer.echo(t("index.chunks_pruned", n=pruned))
            typer.echo(t("index.chunks_added", n=total))
            return
        typer.echo(t("index.specify_file_or_dir"), err=True)
        raise SystemExit(1)
    finally:
        indexer.close()


@app.command()
def watch(
    path: str = typer.Argument(help="Папка KB для наблюдения"),
    db: str | None = typer.Option(None, "--db", help="Путь к RAG-БД"),
) -> None:
    """Watch KB directory and auto-index changed files."""
    cfg = _get_config()
    db_path = db or cfg.get_rag_db_path()
    watch_dir = Path(path)
    if not watch_dir.is_dir():
        typer.echo(t("error.folder_not_found", path=path), err=True)
        raise SystemExit(1)
    try:
        from voiceforge.rag.watcher import KBWatcher

        watcher = KBWatcher(watch_dir, Path(db_path))
        typer.echo(get_watch_banner(path, db_path, t))
        install_watch_stop_signal_handlers(signal, watcher.stop)
        watcher.run()
    except ImportError:
        typer.echo(t("error.rag_deps"), err=True)
        raise SystemExit(1) from None


@app.command("rag-export")
def rag_export(
    output: Path = typer.Option(..., "--output", "-o", path_type=Path, help="Output file (JSON)"),
    db: str | None = typer.Option(None, "--db", help="RAG DB path; default from config"),
    include_content: bool = typer.Option(False, "--content", help="Include chunk content in export"),
) -> None:
    """Export RAG index metadata for backup (block 77). Writes sources and chunk list to JSON."""
    cfg = _get_config()
    db_path = Path(db or cfg.get_rag_db_path())
    if not db_path.is_file():
        typer.echo(t("error.path_not_found", path=str(db_path)), err=True)
        raise SystemExit(1)
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, source, page, chunk_index, timestamp"  # nosec B608
            + (", content" if include_content else "")
            + " FROM chunks ORDER BY source, page, chunk_index"
        )
        rows = cur.fetchall()
        sources = sorted({r["source"] for r in rows})
        chunks = [dict(r) for r in rows]
        out = {"sources": sources, "chunks_count": len(chunks), "chunks": chunks}
    finally:
        conn.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    typer.echo(f"Exported {len(sources)} sources, {len(chunks)} chunks to {output}")


class _Tee:
    """Write to multiple files (block 65: daemon log to file)."""

    def __init__(self, *files):
        self._files = files

    def write(self, data):
        for f in self._files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self._files:
            f.flush()


@app.command()
def daemon(
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground, log to stdout"),
    log_file: Path | None = typer.Option(None, "--log-file", path_type=Path, help="Append daemon logs to this file"),
) -> None:
    """Run D-Bus daemon backend."""
    from voiceforge.core.daemon import run_daemon

    if foreground:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(stream=sys.stdout),
            ]
        )
    log_file_handle = None
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file_handle = log_file.open("a", encoding="utf-8")
        sys.stderr = _Tee(sys.stderr, log_file_handle)
    try:
        run_daemon()
    finally:
        if log_file_handle is not None:
            sys.stderr = sys.__stderr__
            log_file_handle.close()


def _service_unit_path() -> Path:
    candidates: list[Path] = []
    if os.environ.get("VOICEFORGE_SERVICE_FILE"):
        candidates.append(Path(os.environ["VOICEFORGE_SERVICE_FILE"]))
    candidates.append(Path(__file__).resolve().parents[2] / "scripts" / _SERVICE_UNIT_NAME)
    candidates.append(Path.cwd() / "scripts" / _SERVICE_UNIT_NAME)
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"{_SERVICE_UNIT_NAME} not found")


@app.command()
def install_service() -> None:
    """Install systemd user service and enable it."""
    unit_src = _service_unit_path()
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    user_dir = Path(xdg) / "systemd" / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    unit_dst = user_dir / _SERVICE_UNIT_NAME
    shutil.copy2(unit_src, unit_dst)
    typer.echo(t("install_service.copied", path=str(unit_dst)))
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)  # nosec B603 B607
    subprocess.run(["systemctl", "--user", "enable", _SERVICE_UNIT_NAME], check=True)  # nosec B603 B607
    subprocess.run(["systemctl", "--user", "start", _SERVICE_UNIT_NAME], check=True)  # nosec B603 B607
    typer.echo(t("install_service.enabled_and_started"))


@app.command("uninstall-service")
def uninstall_service() -> None:
    """Disable and stop systemd user service."""
    subprocess.run(["systemctl", "--user", "disable", "--now", _SERVICE_UNIT_NAME], check=True)  # nosec B603 B607
    typer.echo(t("uninstall_service.done"))


def _cost_echo_text(data: dict) -> None:
    """Emit cost report as text (S3776)."""
    total = data.get("total_cost_usd") or 0
    calls = data.get("total_calls") or 0
    typer.echo(t("cost.summary", total=total, calls=calls))
    by_model = data.get("by_model") or []
    if by_model:
        typer.echo(t("cost.by_models"))
        for row in by_model:
            typer.echo(
                t("cost.model_line", model=row.get("model", ""), cost=row.get("cost_usd") or 0, calls=row.get("calls") or 0)
            )
    by_day = data.get("by_day") or []
    if by_day:
        typer.echo(t("cost.by_days"))
        for row in by_day[-10:]:
            typer.echo(t("cost.day_line", date=row.get("date", ""), cost=row.get("cost_usd") or 0, calls=row.get("calls") or 0))


@app.command()
def cost(
    days: int = typer.Option(30, "--days", help="За последние N дней (если не заданы --from/--to)"),
    from_date: str | None = typer.Option(None, "--from", help="Начало периода YYYY-MM-DD"),
    to_date: str | None = typer.Option(None, "--to", help="Конец периода YYYY-MM-DD"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
) -> None:
    """Отчёт по затратам LLM (из БД метрик)."""
    from datetime import date

    from voiceforge.core.metrics import get_stats, get_stats_range

    if from_date is not None and to_date is not None:
        try:
            fd = date.fromisoformat(from_date)
            td = date.fromisoformat(to_date)
        except ValueError as e:
            typer.echo(t("cost.date_invalid", e=str(e)), err=True)
            raise SystemExit(1) from e
        if fd > td:
            typer.echo(t("history.from_after_to"), err=True)
            raise SystemExit(1)
        data = get_stats_range(fd, td)
    else:
        data = get_stats(days=days)
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload(data), ensure_ascii=False))
        return
    _cost_echo_text(data)


@app.command()
def status(
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
    detailed: bool = typer.Option(False, "--detailed", help="Разбивка затрат по моделям/дням и % от бюджета"),
    doctor: bool = typer.Option(
        False, "--doctor", help="Диагностика окружения (конфиг, keyring, RAG, ring, Ollama, RAM, импорты)"
    ),
) -> None:
    """Show RAM and cost snapshot."""
    if doctor:
        _emit_success(output, get_doctor_data(), get_doctor_text())
        return
    if detailed:
        cfg = _get_config()
        _emit_success(
            output,
            get_status_detailed_data(cfg.budget_limit_usd),
            get_status_detailed_text(cfg.budget_limit_usd),
        )
        return
    _emit_success(output, get_status_data(), get_status_text())


@app.command("sessions-to-ical")
def sessions_to_ical(
    output: Path = typer.Option(..., "--output", "-o", path_type=Path, help="Output .ics file"),
    limit: int = typer.Option(50, "--limit", "-n", help="Max sessions to include (newest first)"),
    from_date: str | None = typer.Option(None, "--from", help="From date YYYY-MM-DD (inclusive)"),
    to_date: str | None = typer.Option(None, "--to", help="To date YYYY-MM-DD (inclusive)"),
) -> None:
    """Export sessions list to iCalendar .ics (block 83). DTSTART/DTEND from started_at and duration."""
    from voiceforge.core.transcript_log import TranscriptLog

    log_db = TranscriptLog()
    try:
        sessions = _sessions_to_ical_fetch_sessions(log_db, from_date, to_date, limit)
    finally:
        log_db.close()

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VoiceForge//sessions//EN"]
    for s in sessions:
        lines.extend(_session_to_vevent_lines(s))
    lines.append("END:VCALENDAR")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\r\n".join(lines), encoding="utf-8")
    typer.echo(f"Exported {len([x for x in lines if x == 'BEGIN:VEVENT'])} sessions to {output}")


@app.command("weekly-report")
def weekly_report(
    output: Path | None = typer.Option(None, "--output", "-o", path_type=Path, help="Write report to file (default: stdout)"),
    days: int = typer.Option(7, "--days", help="Report period in days (default 7)"),
    format: str = typer.Option("text", "--format", help="Output: text | json | md"),
) -> None:
    """Generate weekly report: sessions count, cost, action items (block 82)."""
    from datetime import date, timedelta

    from voiceforge.core.metrics import get_stats_range
    from voiceforge.core.transcript_log import TranscriptLog

    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    log_db = TranscriptLog()
    try:
        sessions = log_db.get_sessions_in_range(from_date, to_date)
        session_ids = {s.id for s in sessions}
        items = log_db.get_action_items(limit=500)
        week_items = [r for r in items if r.session_id in session_ids]
    finally:
        log_db.close()
    try:
        stats = get_stats_range(from_date, to_date)
        total_cost = stats.get("total_cost_usd") or 0
    except Exception:
        total_cost = 0.0

    if format == "json":
        payload = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "sessions_count": len(sessions),
            "total_cost_usd": total_cost,
            "action_items_count": len(week_items),
            "action_items": [{"session_id": r.session_id, "description": r.description, "status": r.status} for r in week_items],
        }
        out = json.dumps(payload, ensure_ascii=False, indent=2)
    elif format == "md":
        lines = [
            f"# Отчёт за {days} дн. ({from_date} — {to_date})",
            "",
            f"- **Сессий:** {len(sessions)}",
            f"- **Затраты (LLM):** ${total_cost:.2f}",
            f"- **Action items:** {len(week_items)}",
            "",
            "## Action items",
            "",
        ]
        for r in week_items:
            lines.append(f"- [{r.session_id}] {r.status}: {r.description}")
        out = "\n".join(lines)
    else:
        lines = [
            f"Period: {from_date} — {to_date} ({days} days)",
            f"Sessions: {len(sessions)}",
            f"Cost (LLM): ${total_cost:.2f}",
            f"Action items: {len(week_items)}",
            "",
        ]
        for r in week_items:
            lines.append(f"  [{r.session_id}] {r.status}: {r.description}")
        out = "\n".join(lines)

    if output is not None:
        output.write_text(out, encoding="utf-8")
        typer.echo(f"Report written to {output}")
    else:
        typer.echo(out)


@app.command("export")
def export_session(
    session_id: int = typer.Option(..., "--id", help="ID сессии для экспорта"),
    format: str = typer.Option("md", "--format", help="Формат: md | pdf | docx | notion | otter"),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Файл вывода (по умолчанию: session_<id>.<format>)",
    ),
) -> None:
    """Экспорт сессии в Markdown, PDF, DOCX, Notion или Otter (blocks 39, 81)."""
    from voiceforge.core.transcript_log import TranscriptLog

    if sys.stderr.isatty():
        typer.echo("Exporting…", err=True)
    if format not in ("md", "pdf", "docx", "notion", "otter"):
        typer.echo(t("export.format_md_or_pdf"), err=True)
        raise SystemExit(1)
    log_db = TranscriptLog()
    try:
        detail = log_db.get_session_detail(session_id)
        if detail is None:
            typer.echo(session_not_found_message(session_id), err=True)
            raise SystemExit(1)
        segments, analysis = detail
        meta = log_db.get_session_meta(session_id)
        started_at = meta[0] if meta else None
        if format == "notion":
            md_text = build_session_export_notion(session_id, segments, analysis, started_at=started_at)
        elif format == "otter":
            md_text = build_session_export_otter(session_id, segments, analysis, started_at=started_at)
        else:
            md_text = build_session_markdown(session_id, segments, analysis, started_at=started_at)
    finally:
        log_db.close()

    def _export_suffix(fmt: str) -> str:
        if fmt == "pdf":
            return "pdf"
        if fmt == "docx":
            return "docx"
        if fmt == "otter":
            return "txt"
        return "md"

    suffix = _export_suffix(format)
    out_path = output or Path(f"session_{session_id}.{suffix}")
    if format in ("md", "notion", "otter"):
        out_path.write_text(md_text, encoding="utf-8")
        typer.echo(t("export.saved", path=str(out_path)))
        return
    _export_via_pandoc(format, out_path, md_text)


def _export_via_pandoc(format: str, out_path: Path, md_text: str) -> None:
    """Run pandoc for PDF/DOCX export (S3776). Raises SystemExit on failure."""
    tmp_md = out_path.with_suffix(".md")
    tmp_md.write_text(md_text, encoding="utf-8")
    pandoc_args = ["pandoc", str(tmp_md), "-o", str(out_path)]
    if format == "pdf":
        pandoc_args.append("--pdf-engine=pdflatex")
    try:
        subprocess.run(  # nosec B603 B607 -- pandoc from PATH, paths from our export
            pandoc_args,
            check=True,
            capture_output=True,
        )
        tmp_md.unlink(missing_ok=True)
        typer.echo(t("export.saved", path=str(out_path)))
    except FileNotFoundError:
        typer.echo(t("export.pdf_install") if format == "pdf" else "pandoc not found. Install: pandoc", err=True)
        typer.echo(t("export.md_fallback", path=str(tmp_md)))
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(t("error.pandoc", err=e.stderr.decode() if e.stderr else str(e)), err=True)
        raise SystemExit(1) from e


def _backup_data_dir() -> Path:
    """VoiceForge data directory (transcripts.db, metrics.db). #63"""
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge"


@app.command("backup")
def backup_cmd(
    output_dir: Path = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Каталог для бэкапов (по умолчанию: <data_dir>/backups)",
    ),
    keep: int = typer.Option(5, "--keep", help="Хранить последние N бэкапов (0 = не удалять старые)"),
) -> None:
    """Создать бэкап transcripts.db, metrics.db, rag.db в каталог с меткой времени (#63)."""
    data_dir = _backup_data_dir()
    out = output_dir or (data_dir / "backups")
    ensure_private_dir(out)
    cfg = _get_config()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_sub = out / f"voiceforge-backup-{timestamp}"
    ensure_private_dir(backup_sub)
    copied = []
    for name, src_path in [
        ("transcripts.db", data_dir / "transcripts.db"),
        ("metrics.db", data_dir / "metrics.db"),
        ("rag.db", Path(cfg.get_rag_db_path())),
    ]:
        if src_path.exists():
            dest = backup_sub / name
            shutil.copy2(src_path, dest)
            ensure_private_file(dest)
            copied.append(name)
    if not copied:
        typer.echo(t("backup.no_files"), err=True)
        raise SystemExit(1)
    typer.echo(t("backup.done", path=str(backup_sub), count=len(copied)))
    if keep > 0:
        existing = sorted([p for p in out.iterdir() if p.is_dir() and p.name.startswith("voiceforge-backup-")], reverse=True)
        for old in existing[keep:]:
            shutil.rmtree(old, ignore_errors=True)
            log.info("backup.rotated", path=str(old))


def _history_echo_error_data(data: Any) -> None:
    """Emit error message for history_helpers error kind (reduces S3776 complexity)."""
    if isinstance(data, tuple):
        key, kwargs = data
        typer.echo(t(key, **kwargs), err=True)
    else:
        typer.echo(t(data) if isinstance(data, str) and data.startswith("history.") else data, err=True)


def _history_echo_session_not_found(data: Any, output: str) -> None:
    """Emit session not found error for history --id (S3776)."""
    if output == "json":
        typer.echo(json.dumps(_cli_error_payload("SESSION_NOT_FOUND", data), ensure_ascii=False))
    else:
        typer.echo(data, err=True)


def _history_echo(kind: str, data: Any, exit_on_error: bool = True) -> None:
    """Emit history command output from (kind, data) returned by history_helpers."""
    if kind == "error":
        _history_echo_error_data(data)
        if exit_on_error:
            raise SystemExit(1)
        return
    if kind == "message":
        typer.echo(t(data))
        return
    if kind == "json":
        typer.echo(json.dumps(_cli_success_payload(data), ensure_ascii=False))
        return
    if kind == "lines":
        for line in data:
            typer.echo(line)
        return
    if kind == "md":
        typer.echo(data)


def _history_resolve(
    log_db: Any,
    purge_before: str | None,
    action_items: bool,
    search: str | None,
    date: str | None,
    from_date: str | None,
    to_date: str | None,
    session_id: int | None,
    last_n: int,
    output: str,
    offset: int = 0,
) -> tuple[str, Any, Any] | None:
    """Resolve history command to (kind, data, exit_on_error) or handle purge and return None."""
    from datetime import date as date_type

    if purge_before is not None:
        try:
            cutoff = date_type.fromisoformat(purge_before)
        except ValueError:
            typer.echo(t("history.date_invalid", err=purge_before), err=True)
            raise SystemExit(1)
        n = log_db.purge_before(cutoff)
        typer.echo(t("history.purge_done", count=n))
        return None
    if action_items:
        kind, data = history_action_items_result(log_db, output)
        return (kind, data, True)
    if search is not None:
        kind, data = history_search_result(log_db, search, output)
        return (kind, data, True)
    if date is not None or (from_date is not None and to_date is not None):
        kind, data = history_date_range_result(log_db, date, from_date, to_date, output)
        return (kind, data, kind == "error")
    if session_id is not None:
        kind, data = history_session_detail_result(log_db, session_id, output)
        if kind == "error":
            _history_echo_session_not_found(data, output)
            raise SystemExit(1)
        return (kind, data, False)
    kind, data = history_list_result(log_db, last_n, output, offset=offset)
    return (kind, data, True)


@app.command()
def history(
    session_id: int | None = typer.Option(None, "--id", help="Показать детали сессии"),
    last_n: int = typer.Option(10, "--last", help="Сколько последних сессий показать"),
    offset: int = typer.Option(0, "--offset", help="Пропустить N сессий (пагинация, блок 51)"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON_MD),
    search: str | None = typer.Option(None, "--search", help="Поиск по тексту транскриптов (FTS5)"),
    date: str | None = typer.Option(None, "--date", help="Сессии за день YYYY-MM-DD"),
    from_date: str | None = typer.Option(None, "--from", help="Начало периода (с --to)"),
    to_date: str | None = typer.Option(None, "--to", help="Конец периода (с --from)"),
    action_items: bool = typer.Option(False, "--action-items", help="Список action items по сессиям (cross-session)"),
    purge_before: str | None = typer.Option(None, "--purge-before", help="Удалить сессии, начатые до даты YYYY-MM-DD (#43)"),
) -> None:
    """Show recent sessions or one detailed session."""
    from voiceforge.core.transcript_log import TranscriptLog

    if output == "md" and session_id is None:
        typer.echo(t("history.md_requires_id"), err=True)
        raise SystemExit(1)
    log_db = TranscriptLog()
    try:
        result = _history_resolve(
            log_db, purge_before, action_items, search, date, from_date, to_date, session_id, last_n, output, offset
        )
        if result is None:
            return
        kind, data, exit_on_error = result
        _history_echo(kind, data, exit_on_error=exit_on_error)
    finally:
        log_db.close()


@app.command("web")
def web_serve(
    port: int = typer.Option(8765, "--port", help="Порт HTTP-сервера"),
    host: str = typer.Option("127.0.0.1", "--host", help="Хост (только локальный по умолчанию)"),
    web_async: bool = typer.Option(
        False,
        "--async",
        help="Использовать async-сервер (Starlette + uvicorn). Требует uv sync --extra web-async.",
    ),
) -> None:
    """Block 12: запустить простой локальный Web UI (статус, сессии, анализ). Phase C #66: --async для Starlette+uvicorn."""
    use_async_env = os.environ.get("VOICEFORGE_WEB_ASYNC", "").strip() in ("1", "true", "yes")
    if web_async or use_async_env:
        try:
            from voiceforge.web.server_async import run_async_server

            run_async_server(host=host, port=port)
            return
        except ImportError:
            log.warning("web.async_fallback", reason="starlette/uvicorn not installed", hint="uv sync --extra web-async")
    from voiceforge.web.server import run_server

    run_server(host=host, port=port)


@calendar_app.command("upcoming")
def calendar_upcoming(
    hours: int = typer.Option(48, "--hours", "-H", help="Часы вперёд для выборки событий"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
) -> None:
    """Upcoming calendar events (from now to now+hours)."""
    from voiceforge.calendar import get_upcoming_events

    events, err = get_upcoming_events(hours_ahead=hours)
    if err:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("CALDAV_UPCOMING_FAILED", err), ensure_ascii=False))
        else:
            typer.echo(t(_I18N_CALENDAR_POLL_ERROR, msg=err), err=True)
            hint = _hint_for_error(err)
            if hint:
                typer.echo(hint, err=True)
        raise SystemExit(1)
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload({"events": events, "hours": hours}), ensure_ascii=False))
        return
    if not events:
        typer.echo(t("calendar.poll_no_events", minutes=hours * 60))
        return
    for ev in events:
        typer.echo(t("calendar.poll_line", summary=ev.get("summary", ""), start_iso=ev.get("start_iso", "")))


@calendar_app.command("list")
def calendar_list(
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
) -> None:
    """List CalDAV calendars (names and URLs). Block 58."""
    from voiceforge.calendar import list_calendars

    calendars, err = list_calendars()
    if err:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("CALDAV_LIST_FAILED", err), ensure_ascii=False))
        else:
            typer.echo(t(_I18N_CALENDAR_POLL_ERROR, msg=err), err=True)
            hint = _hint_for_error(err)
            if hint:
                typer.echo(hint, err=True)
        raise SystemExit(1)
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload({"calendars": calendars}), ensure_ascii=False))
        return
    for cal in calendars:
        typer.echo(f"  {cal.get('name', '(no name)')} — {cal.get('url', '')}")


@calendar_app.command("export-ical")
def calendar_export_ical(
    output: Path = typer.Option(..., "--output", "-o", path_type=Path, help="Output .ics file (block 48)"),
    hours: int = typer.Option(48, "--hours", "-H", help="Hours ahead to fetch"),
) -> None:
    """Export upcoming calendar events to iCalendar .ics (block 48)."""
    from datetime import datetime as dt_class

    from voiceforge.calendar import get_upcoming_events

    events, err = get_upcoming_events(hours_ahead=hours)
    if err:
        _calendar_export_ical_fail(err)

    def _iso_to_ical_utc(iso_str: str) -> str:
        if not iso_str:
            return ""
        try:
            s = iso_str.strip().replace("Z", _ISO_UTC_SUFFIX)
            dt = dt_class.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            else:
                dt = dt.astimezone(UTC)
            return dt.strftime(_ICAL_DT_FORMAT)
        except (ValueError, TypeError):
            return ""

    def _event_to_vevent_lines(ev: dict, index: int) -> list[str]:
        """Build VEVENT lines for one calendar event (S3776)."""
        start_ical = _iso_to_ical_utc(ev.get("start_iso") or "")
        if not start_ical:
            return []
        end_ical = _iso_to_ical_utc(ev.get("end_iso") or "") or start_ical
        summary = (ev.get("summary") or "(no title)").replace("\r", "").replace("\n", " ")
        uid = f"voiceforge-upcoming-{index}-{hash(ev.get('start_iso', '')) & 0x7FFFFFFF}@voiceforge"
        return [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{start_ical}",
            f"DTEND:{end_ical}",
            f"SUMMARY:{summary}",
            "END:VEVENT",
        ]

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VoiceForge//calendar-upcoming//EN"]
    for i, ev in enumerate(events):
        lines.extend(_event_to_vevent_lines(ev, i))
    lines.append("END:VCALENDAR")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\r\n".join(lines), encoding="utf-8")
    typer.echo(f"Exported {len(events)} upcoming events to {output}")


@calendar_app.command("poll")
def calendar_poll(
    minutes: int = typer.Option(5, "--minutes", "-m", help="События, начавшиеся за последние N минут"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
) -> None:
    """Poll CalDAV for events that started in the last N minutes."""
    from voiceforge.calendar import poll_events_started_in_last

    events, err = poll_events_started_in_last(minutes=minutes)
    if err is not None:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("CALDAV_POLL_FAILED", err), ensure_ascii=False))
        else:
            typer.echo(t(_I18N_CALENDAR_POLL_ERROR, msg=err), err=True)
            hint = _hint_for_error(err)
            if hint:
                typer.echo(hint, err=True)
        raise SystemExit(1)
    _calendar_poll_emit(output, minutes, events)


def _calendar_event_description_from_detail(detail: Any, sid: int) -> str:
    """Build event description from session detail (action items). S3776."""
    if not detail:
        return f"Session {sid} (VoiceForge)"
    _segments, analysis = detail
    if not (analysis and analysis.action_items):
        return f"Session {sid} (VoiceForge)"
    parts: list[str] = []
    for ai in analysis.action_items:
        desc = (ai.get("description") or ai.get("text") or "").strip()
        if not desc:
            continue
        assignee = (ai.get("assignee") or "").strip()
        deadline = (ai.get("deadline") or "").strip()
        if assignee or deadline:
            desc = f"{desc} ({', '.join(x for x in [assignee, deadline] if x)})"
        parts.append(f"- {desc}")
    return "\n".join(parts) if parts else f"Session {sid} (VoiceForge)"


@calendar_app.command("create-from-session")
def calendar_create_from_session(
    session_id: int = typer.Argument(..., help="Session ID to create calendar event from (block 79, #95)."),
    calendar_url: str | None = typer.Option(None, "--calendar-url", "-c", help="CalDAV calendar URL (default: first calendar)."),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
) -> None:
    """Create a CalDAV event from a VoiceForge session (summary + action items in description)."""
    from voiceforge.calendar import create_event
    from voiceforge.core.transcript_log import TranscriptLog

    log_db = TranscriptLog()
    try:
        meta = log_db.get_session_meta(session_id)
        if not meta:
            if output == "json":
                typer.echo(
                    json.dumps(_cli_error_payload("SESSION_NOT_FOUND", f"Session {session_id} not found"), ensure_ascii=False)
                )
            else:
                typer.echo(session_not_found_message(session_id), err=True)
            raise SystemExit(1)
        started_at, ended_at, _duration_sec = meta
        detail = log_db.get_session_detail(session_id)
        description = _calendar_event_description_from_detail(detail, session_id)
    finally:
        log_db.close()

    summary = f"VoiceForge session {session_id}"
    event_uid, err = create_event(
        start_iso=started_at,
        end_iso=ended_at,
        summary=summary,
        description=description,
        calendar_url=calendar_url or None,
    )
    if err is not None:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("CALDAV_CREATE_EVENT_FAILED", err), ensure_ascii=False))
        else:
            typer.echo(t(_I18N_CALENDAR_POLL_ERROR, msg=err), err=True)
            hint = _hint_for_error(err)
            if hint:
                typer.echo(hint, err=True)
        raise SystemExit(1)
    _calendar_create_emit(output, event_uid)


def main() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )
    app()


if __name__ == "__main__":
    main()
