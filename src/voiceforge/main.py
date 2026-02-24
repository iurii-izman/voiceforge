"""VoiceForge CLI entrypoint (alpha0.1 minimal core)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess  # nosec B404 -- pandoc for PDF export, args from our paths
import sys
import threading
import time
from pathlib import Path
from typing import Any

import structlog
import typer

from voiceforge.cli.history_helpers import (
    build_session_markdown,
    history_action_items_result,
    history_date_range_result,
    history_list_result,
    history_search_result,
    history_session_detail_result,
    session_not_found_message,
)
from voiceforge.cli.status_helpers import (
    get_doctor_data,
    get_doctor_text,
    get_status_data,
    get_status_detailed_data,
    get_status_detailed_text,
    get_status_text,
)
from voiceforge.core.config import Settings
from voiceforge.core.contracts import (
    build_cli_error_payload,
    build_cli_success_payload,
    extract_error_message,
)
from voiceforge.i18n import t

log = structlog.get_logger()
app = typer.Typer(help="VoiceForge — local-first AI assistant (alpha0.1 core)")
action_items_app = typer.Typer(help=t("cli.action_items_help"))
app.add_typer(action_items_app, name="action-items")
calendar_app = typer.Typer(help="CalDAV calendar poll (keyring: caldav_url, caldav_username, caldav_password)")
app.add_typer(calendar_app, name="calendar")

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
_I18N_TEMPLATE_ACTIONS = "template.one_on_one.actions"
_HELP_OUTPUT_TEXT_JSON = "Формат вывода: text | json"
_HELP_OUTPUT_TEXT_JSON_MD = "Формат вывода: text | json | md (md только с --id)"
_SERVICE_UNIT_NAME = "voiceforge.service"


def _get_config() -> Settings:
    return Settings()


def _cli_error_payload(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return build_cli_error_payload(code=code, message=message, retryable=retryable)


def _cli_success_payload(data: dict[str, Any]) -> dict[str, Any]:
    return build_cli_success_payload(data=data)


def _extract_error_message(payload: str) -> str | None:
    return extract_error_message(payload, legacy_prefix=t("error.legacy_prefix"))


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


def _build_analysis_for_log_default(llm_result: Any, cfg: Any, cost_usd: float) -> dict[str, Any]:
    """Build analysis_for_log dict for default MeetingAnalysis."""
    return {
        "model": cfg.default_llm,
        "questions": llm_result.questions,
        "answers": llm_result.answers,
        "recommendations": llm_result.recommendations,
        "action_items": [ai.model_dump(mode="json") for ai in llm_result.action_items],
        "cost_usd": cost_usd,
    }


def run_analyze_pipeline(
    seconds: int,
    template: str | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Run core analyze pipeline and return (display_text, segments_for_log, analysis_for_log)."""
    cfg = _get_config()
    try:
        from voiceforge.core.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline(cfg)
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

    segments_for_log = [
        {
            "start_sec": s.start,
            "end_sec": s.end,
            "speaker": _speaker_for_interval(s.start, s.end, diar_segments),
            "text": s.text or "",
        }
        for s in segments
    ]

    try:
        from voiceforge.llm.router import analyze_meeting

        llm_result, cost_usd = analyze_meeting(
            transcript,
            context=context,
            model=cfg.default_llm,
            template=template,
            transcript_pre_redacted=transcript_redacted,
            ollama_model=cfg.ollama_model,
            pii_mode=cfg.pii_mode,
        )
    except ImportError:
        return (t("error.install_llm_deps"), [], {})
    except Exception as e:
        log.warning("analyze.llm_failed", error=str(e))
        return (t(_I18N_ERROR_LLM_FAILED, e=str(e)), [], {})

    if template and hasattr(llm_result, "model_dump"):
        lines, analysis_for_log = _format_template_result(template, llm_result)
        analysis_for_log["model"] = cfg.default_llm
        analysis_for_log["cost_usd"] = cost_usd
        return ("\n".join(lines), segments_for_log, analysis_for_log)

    lines = _format_meeting_analysis_lines(llm_result)
    analysis_for_log = _build_analysis_for_log_default(llm_result, cfg, cost_usd)
    return ("\n".join(lines), segments_for_log, analysis_for_log)


def run_live_summary_pipeline(seconds: int) -> tuple[list[str], float]:
    """Block 10: run pipeline on last N seconds, return (display lines, cost_usd). No session log."""
    cfg = _get_config()
    try:
        from voiceforge.core.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline(cfg)
        result, err = pipeline.run(seconds)
    except ImportError:
        return ([t("error.install_deps")], 0.0)

    if err is not None or result is None:
        return ([err or t("error.pipeline_empty")], 0.0)

    transcript = result.transcript
    context = result.context
    transcript_redacted = result.transcript_redacted

    try:
        from voiceforge.llm.router import analyze_live_summary

        live_result, cost_usd = analyze_live_summary(
            transcript,
            context=context,
            model=cfg.default_llm,
            transcript_pre_redacted=transcript_redacted,
            pii_mode=cfg.pii_mode,
        )
    except ImportError:
        return ([t("error.install_llm_deps")], 0.0)
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
        from voiceforge.stt.streaming import StreamingSegment, StreamingTranscriber
        from voiceforge.stt.transcriber import Transcriber
    except ImportError:
        return
    transcriber = Transcriber(model_size=cfg.model_size)
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
    try:
        from voiceforge.audio.capture import AudioCapture
    except ImportError:
        typer.echo(t("error.audio_module_not_found"), err=True)
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
def analyze(
    seconds: int = typer.Option(30, help="Последние N секунд"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Шаблон встречи: standup, sprint_review, one_on_one, brainstorm, interview",
    ),
) -> None:
    """Analyze ring-buffer fragment: transcribe -> diarize -> rag -> llm."""
    if template is not None and template not in _TEMPLATE_CHOICES:
        typer.echo(t("analyze.unknown_template", template=template, choices=", ".join(_TEMPLATE_CHOICES)), err=True)
        raise SystemExit(1)
    display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds, template=template)
    error_message = _extract_error_message(display_text)
    if error_message is not None:
        if output == "json":
            typer.echo(json.dumps(_cli_error_payload("ANALYZE_FAILED", error_message), ensure_ascii=False))
        else:
            typer.echo(error_message, err=True)
        raise SystemExit(1)

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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))  # NOSONAR S2083: path under home


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
    try:
        response, cost_usd = update_action_item_statuses(
            action_items,
            transcript_next,
            model=cfg.default_llm,
            pii_mode=cfg.pii_mode,
        )
    except Exception as e:
        typer.echo(t(_I18N_ERROR_LLM_FAILED, e=str(e)), err=True)
        raise SystemExit(1) from None

    updates = [(u.id, u.status) for u in response.updates]
    if save and updates:
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


def _index_directory(indexer: Any, p: Path) -> tuple[int, set[str]]:
    """Index all supported files under directory p. Return (total chunks added, indexed paths)."""
    total = 0
    indexed_paths: set[str] = set()
    for ext in _INDEX_EXTENSIONS:
        for f in sorted(p.glob(f"**/*{ext}")):
            if not f.is_file():
                continue
            try:
                total += indexer.add_file(f)
                indexed_paths.add(str(f.resolve()))
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
            total, indexed_paths = _index_directory(indexer, p)
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
        typer.echo(t("watch.banner", path=path, db_path=db_path))
        signal.signal(signal.SIGINT, lambda *a: watcher.stop())
        signal.signal(signal.SIGTERM, lambda *a: watcher.stop())
        watcher.run()
    except ImportError:
        typer.echo(t("error.rag_deps"), err=True)
        raise SystemExit(1) from None


@app.command()
def daemon() -> None:
    """Run D-Bus daemon backend."""
    from voiceforge.core.daemon import run_daemon

    run_daemon()


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
    subprocess.run(["systemctl", "--user", "enable", "--now", _SERVICE_UNIT_NAME], check=True)  # nosec B603 B607
    typer.echo(t("install_service.enabled"))


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
        if output == "json":
            typer.echo(json.dumps(_cli_success_payload(get_doctor_data()), ensure_ascii=False))
        else:
            typer.echo(get_doctor_text())
        return
    if detailed:
        cfg = _get_config()
        if output == "json":
            typer.echo(
                json.dumps(
                    _cli_success_payload(get_status_detailed_data(cfg.budget_limit_usd)),
                    ensure_ascii=False,
                )
            )
        else:
            typer.echo(get_status_detailed_text(cfg.budget_limit_usd))
        return
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload(get_status_data()), ensure_ascii=False))
    else:
        typer.echo(get_status_text())


@app.command("export")
def export_session(
    session_id: int = typer.Option(..., "--id", help="ID сессии для экспорта"),
    format: str = typer.Option("md", "--format", help="Формат: md | pdf"),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Файл вывода (по умолчанию: session_<id>.md или .pdf)",
    ),
) -> None:
    """Экспорт сессии в Markdown или PDF (PDF через pandoc, если установлен)."""
    from voiceforge.core.transcript_log import TranscriptLog

    if format not in ("md", "pdf"):
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
        md_text = build_session_markdown(session_id, segments, analysis, started_at=started_at)
    finally:
        log_db.close()

    out_path = output or Path(f"session_{session_id}.{format}")
    if format == "md":
        out_path.write_text(md_text, encoding="utf-8")
        typer.echo(t("export.saved", path=str(out_path)))
        return
    # PDF: write temp md, run pandoc
    tmp_md = out_path.with_suffix(".md")
    tmp_md.write_text(md_text, encoding="utf-8")
    try:
        subprocess.run(  # nosec B603 B607 -- pandoc from PATH, paths from our export
            ["pandoc", str(tmp_md), "-o", str(out_path), "--pdf-engine=pdflatex"],
            check=True,
            capture_output=True,
        )
        tmp_md.unlink(missing_ok=True)
        typer.echo(t("export.saved", path=str(out_path)))
    except FileNotFoundError:
        typer.echo(t("export.pdf_install"), err=True)
        typer.echo(t("export.md_fallback", path=str(tmp_md)))
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(t("error.pandoc", err=e.stderr.decode() if e.stderr else str(e)), err=True)
        raise SystemExit(1) from e


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


@app.command()
def history(
    session_id: int | None = typer.Option(None, "--id", help="Показать детали сессии"),
    last_n: int = typer.Option(10, "--last", help="Сколько последних сессий показать"),
    output: str = typer.Option("text", "--output", help=_HELP_OUTPUT_TEXT_JSON_MD),
    search: str | None = typer.Option(None, "--search", help="Поиск по тексту транскриптов (FTS5)"),
    date: str | None = typer.Option(None, "--date", help="Сессии за день YYYY-MM-DD"),
    from_date: str | None = typer.Option(None, "--from", help="Начало периода (с --to)"),
    to_date: str | None = typer.Option(None, "--to", help="Конец периода (с --from)"),
    action_items: bool = typer.Option(False, "--action-items", help="Список action items по сессиям (cross-session)"),
) -> None:
    """Show recent sessions or one detailed session."""
    from voiceforge.core.transcript_log import TranscriptLog

    if output == "md" and session_id is None:
        typer.echo(t("history.md_requires_id"), err=True)
        raise SystemExit(1)
    log_db = TranscriptLog()
    try:
        if action_items:
            _history_echo(*history_action_items_result(log_db, output))
            return
        if search is not None:
            _history_echo(*history_search_result(log_db, search, output))
            return
        if date is not None or (from_date is not None and to_date is not None):
            kind, data = history_date_range_result(log_db, date, from_date, to_date, output)
            if kind == "error":
                _history_echo(kind, data)
            else:
                _history_echo(kind, data, exit_on_error=False)
            return
        if session_id is not None:
            kind, data = history_session_detail_result(log_db, session_id, output)
            if kind == "error":
                _history_echo_session_not_found(data, output)
                raise SystemExit(1)
            _history_echo(kind, data, exit_on_error=False)
            return
        _history_echo(*history_list_result(log_db, last_n, output))
    finally:
        log_db.close()


@app.command("web")
def web_serve(
    port: int = typer.Option(8765, "--port", help="Порт HTTP-сервера"),
    host: str = typer.Option("127.0.0.1", "--host", help="Хост (только локальный по умолчанию)"),
) -> None:
    """Block 12: запустить простой локальный Web UI (статус, сессии, анализ)."""
    from voiceforge.web.server import run_server

    run_server(host=host, port=port)


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
            typer.echo(t("calendar.poll_error", msg=err), err=True)
        raise SystemExit(1)
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload({"events": events, "minutes": minutes}), ensure_ascii=False))
        return
    if not events:
        typer.echo(t("calendar.poll_no_events", minutes=minutes))
        return
    typer.echo(t("calendar.poll_events", minutes=minutes))
    for ev in events:
        typer.echo(t("calendar.poll_line", summary=ev.get("summary", ""), start_iso=ev.get("start_iso", "")))


def main() -> None:
    structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
    app()


if __name__ == "__main__":
    main()
