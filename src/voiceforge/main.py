"""VoiceForge CLI entrypoint (alpha0.1 minimal core)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import structlog
import typer

from voiceforge.cli.history_helpers import (
    build_session_detail_payload,
    build_session_markdown,
    build_sessions_payload,
    render_session_detail_lines,
    render_sessions_table_lines,
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
action_items_app = typer.Typer(help="Обновление статусов action items")
app.add_typer(action_items_app, name="action-items")

_INDEX_EXTENSIONS = (".pdf", ".md", ".markdown", ".html", ".htm", ".docx", ".txt")


def _get_config() -> Settings:
    return Settings()


def _cli_error_payload(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return build_cli_error_payload(code=code, message=message, retryable=retryable)


def _cli_success_payload(data: dict[str, Any]) -> dict[str, Any]:
    return build_cli_success_payload(data=data)


def _extract_error_message(payload: str) -> str | None:
    return extract_error_message(payload, legacy_prefix="Ошибка:")


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


def _format_template_result(template: str, llm_result: Any) -> tuple[list[str], dict[str, Any]]:
    """Format template LLM result to display lines and analysis_for_log (for log_session)."""
    d = llm_result.model_dump(mode="json") if hasattr(llm_result, "model_dump") else {}
    lines: list[str] = []
    answers_for_log: list[str] = []
    action_items_for_log: list[dict[str, Any]] = []

    if template == "standup":
        lines.append("--- Сделано ---")
        for x in d.get("done", []):
            lines.append(f"  • {x}")
            answers_for_log.append(x)
        lines.append("--- Планы ---")
        for x in d.get("planned", []):
            lines.append(f"  • {x}")
            answers_for_log.append(x)
        lines.append("--- Блокеры ---")
        for x in d.get("blockers", []):
            lines.append(f"  • {x}")
            answers_for_log.append(x)
    elif template == "sprint_review":
        for label, key in [("Демо", "demos"), ("Метрики", "metrics"), ("Фидбэк", "feedback")]:
            lines.append(f"--- {label} ---")
            for x in d.get(key, []):
                lines.append(f"  • {x}")
                answers_for_log.append(x)
    elif template == "one_on_one":
        if d.get("mood"):
            lines.append(f"--- Настроение ---\n  {d['mood']}")
            answers_for_log.append(d["mood"])
        for label, key in [("Рост", "growth"), ("Блокеры", "blockers")]:
            lines.append(f"--- {label} ---")
            for x in d.get(key, []):
                lines.append(f"  • {x}")
                answers_for_log.append(x)
        lines.append("--- Действия ---")
        for ai in d.get("action_items", []):
            desc = ai.get("description", "")
            who = (ai.get("assignee") or "").strip()
            lines.append(f"  • {desc}" + (f" ({who})" if who else ""))
            action_items_for_log.append(ai)
    elif template == "brainstorm":
        for label, key in [("Идеи", "ideas"), ("Голосование", "voting"), ("Следующие шаги", "next_steps")]:
            lines.append(f"--- {label} ---")
            for x in d.get(key, []):
                lines.append(f"  • {x}")
                answers_for_log.append(x)
    elif template == "interview":
        for label, key in [("Вопросы кандидату", "questions_asked"), ("Оценка", "assessment")]:
            lines.append(f"--- {label} ---")
            for x in d.get(key, []):
                lines.append(f"  • {x}")
                answers_for_log.append(x)
        if d.get("decision"):
            lines.append(f"--- Решение ---\n  {d['decision']}")
            answers_for_log.append(d["decision"])

    analysis_for_log = {
        "template": template,
        "questions": [],
        "answers": answers_for_log,
        "recommendations": [],
        "action_items": action_items_for_log,
    }
    return (lines, analysis_for_log)


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
        return ("Ошибка: установите зависимости (uv sync).", [], {})

    if err is not None:
        return (err, [], {})
    if result is None:
        return ("Ошибка: pipeline вернул пустой результат.", [], {})

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
        return ("Ошибка: установите LLM зависимости (uv sync --extra llm).", [], {})
    except Exception as e:
        log.warning("analyze.llm_failed", error=str(e))
        return (f"Ошибка LLM: {e}", [], {})

    if template and hasattr(llm_result, "model_dump"):
        lines, analysis_for_log = _format_template_result(template, llm_result)
        analysis_for_log["model"] = cfg.default_llm
        analysis_for_log["cost_usd"] = cost_usd
        return ("\n".join(lines), segments_for_log, analysis_for_log)

    # Default: MeetingAnalysis
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
        if who and who.upper() != "<UNKNOWN>":
            lines.append(f"  • {ai.description} ({who})")
        else:
            lines.append(f"  • {ai.description}")

    analysis_for_log = {
        "model": cfg.default_llm,
        "questions": llm_result.questions,
        "answers": llm_result.answers,
        "recommendations": llm_result.recommendations,
        "action_items": [ai.model_dump(mode="json") for ai in llm_result.action_items],
        "cost_usd": cost_usd,
    }
    return ("\n".join(lines), segments_for_log, analysis_for_log)


def run_live_summary_pipeline(seconds: int) -> tuple[list[str], float]:
    """Block 10: run pipeline on last N seconds, return (display lines, cost_usd). No session log."""
    cfg = _get_config()
    try:
        from voiceforge.core.pipeline import AnalysisPipeline

        pipeline = AnalysisPipeline(cfg)
        result, err = pipeline.run(seconds)
    except ImportError:
        return (["Ошибка: установите зависимости (uv sync)."], 0.0)

    if err is not None or result is None:
        return ([err or "Ошибка: pipeline вернул пустой результат."], 0.0)

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
        return (["Ошибка: установите LLM зависимости (uv sync --extra llm)."], 0.0)
    except Exception as e:
        log.warning("live_summary.llm_failed", error=str(e))
        return ([f"Ошибка LLM: {e}"], 0.0)

    lines: list[str] = []
    if getattr(live_result, "key_points", None):
        lines.append("--- Ключевые моменты ---")
        for k in live_result.key_points:
            if k and k.strip():
                lines.append(f"  • {k.strip()}")
    if getattr(live_result, "action_items", None):
        lines.append("--- Действия ---")
        for ai in live_result.action_items:
            desc = getattr(ai, "description", "") or ""
            if not desc.strip():
                continue
            who = (getattr(ai, "assignee", None) or "").strip()
            if who and who.upper() != "<UNKNOWN>":
                lines.append(f"  • {desc} ({who})")
            else:
                lines.append(f"  • {desc}")
    if not lines:
        lines.append("(ничего существенного)")
    return (lines, cost_usd)


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


# Block 10: interval (seconds) between live summaries during listen
LIVE_SUMMARY_INTERVAL_SEC = 90
LIVE_SUMMARY_LAST_SEC = 90


def _live_summary_listen_worker(stop_event: threading.Event) -> None:
    """Block 10: periodically run live summary on ring buffer and print to stdout."""
    while not stop_event.wait(timeout=LIVE_SUMMARY_INTERVAL_SEC):
        lines, cost = run_live_summary_pipeline(LIVE_SUMMARY_LAST_SEC)
        if not lines or (len(lines) == 1 and lines[0].startswith("Ошибка")):
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
        typer.echo("Ошибка: модуль audio не найден.", err=True)
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
        typer.echo("Стриминг STT включён — partial/final в терминале.", err=True)

    live_summary_stop = threading.Event()
    live_summary_thread: threading.Thread | None = None
    if live_summary:
        live_summary_thread = threading.Thread(
            target=_live_summary_listen_worker,
            args=(live_summary_stop,),
            daemon=True,
        )
        live_summary_thread.start()
        typer.echo("Live summary включён — каждые 90 с по последним 90 с.", err=True)

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
            live_summary_thread.join(timeout=LIVE_SUMMARY_INTERVAL_SEC + 60.0)
        if streaming_stt:
            sys.stdout.write("\n")
            sys.stdout.flush()
        capture.stop()


_TEMPLATE_CHOICES = ["standup", "sprint_review", "one_on_one", "brainstorm", "interview"]


@app.command()
def analyze(
    seconds: int = typer.Option(30, help="Последние N секунд"),
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Шаблон встречи: standup, sprint_review, one_on_one, brainstorm, interview",
    ),
) -> None:
    """Analyze ring-buffer fragment: transcribe -> diarize -> rag -> llm."""
    if template is not None and template not in _TEMPLATE_CHOICES:
        typer.echo(f"Неизвестный шаблон: {template}. Доступны: {', '.join(_TEMPLATE_CHOICES)}", err=True)
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
    return Path(base) / "voiceforge" / "action_item_status.json"


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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


@action_items_app.command("update")
def action_items_update(
    from_session: int = typer.Option(..., "--from-session", help="ID сессии с action items"),
    next_session: int = typer.Option(..., "--next-session", help="ID сессии (встреча), по которой обновляем статусы"),
    output: str = typer.Option("text", "--output", help="text | json"),
    save: bool = typer.Option(True, "--save/--no-save", help="Сохранить статусы в action_item_status.json"),
) -> None:
    """Обновить статусы action items из сессии --from-session по транскрипту встречи --next-session."""
    try:
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.llm.router import update_action_item_statuses
    except ImportError as e:
        typer.echo(f"Ошибка: {e}", err=True)
        raise SystemExit(1) from None

    log_db = TranscriptLog()
    detail_from = log_db.get_session_detail(from_session)
    detail_next = log_db.get_session_detail(next_session)
    log_db.close()

    if detail_from is None:
        typer.echo(t("history.session_not_found", session_id=from_session), err=True)
        raise SystemExit(1)
    if detail_next is None:
        typer.echo(t("history.session_not_found", session_id=next_session), err=True)
        raise SystemExit(1)
    segments_next, _ = detail_next
    analysis_from = detail_from[1]
    if analysis_from is None:
        typer.echo(f"В сессии {from_session} нет анализа (action items).", err=True)
        raise SystemExit(1)
    action_items = analysis_from.action_items
    if not action_items:
        typer.echo("Нет action items для обновления.", err=True)
        raise SystemExit(0)
    transcript_next = "\n".join(s.text for s in segments_next).strip()
    if not transcript_next:
        typer.echo(f"В сессии {next_session} нет текста сегментов.", err=True)
        raise SystemExit(1)

    cfg = _get_config()
    try:
        response, cost_usd = update_action_item_statuses(
            action_items,
            transcript_next,
            model=cfg.default_llm,
            pii_mode=cfg.pii_mode,
        )
    except Exception as e:
        typer.echo(f"Ошибка LLM: {e}", err=True)
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
        except Exception:
            pass

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
            typer.echo(f"Сохранено в {_action_item_status_path()}")


@app.command()
def index(
    path: str = typer.Argument(help="Путь к файлу или папке (PDF, MD, HTML, DOCX, TXT)"),
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
        typer.echo("Установите зависимости RAG: uv sync --extra rag", err=True)
        raise SystemExit(1) from None

    indexer = KnowledgeIndexer(db_path)
    try:
        if p.is_file():
            if p.suffix.lower() not in _INDEX_EXTENSIONS:
                typer.echo(f"Формат не поддерживается: {p.suffix}", err=True)
                raise SystemExit(1)
            added = indexer.add_file(p)
            typer.echo(f"Добавлено чанков: {added}")
            return
        if p.is_dir():
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
                        typer.echo(f"Пропуск {f}: {e}", err=True)
            pruned = indexer.prune_sources_not_in(indexed_paths, only_under_prefix=str(p.resolve()))
            if pruned:
                typer.echo(f"Удалено чанков (файлы удалены): {pruned}")
            typer.echo(f"Добавлено чанков: {total}")
            return
        typer.echo("Укажите файл или папку.", err=True)
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
        typer.echo(f"VoiceForge watch: {path} -> {db_path} (Ctrl+C для остановки)")
        signal.signal(signal.SIGINT, lambda *a: watcher.stop())
        signal.signal(signal.SIGTERM, lambda *a: watcher.stop())
        watcher.run()
    except ImportError:
        typer.echo("Установите зависимости RAG: uv sync --extra rag", err=True)
        raise SystemExit(1) from None


@app.command()
def daemon() -> None:
    """Run D-Bus daemon backend."""
    from voiceforge.core.daemon import run_daemon

    run_daemon()


def _service_unit_path() -> Path:
    env_path = os.environ.get("VOICEFORGE_SERVICE_FILE")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
    repo_scripts = Path(__file__).resolve().parents[2] / "scripts" / "voiceforge.service"
    if repo_scripts.is_file():
        return repo_scripts
    cwd_scripts = Path.cwd() / "scripts" / "voiceforge.service"
    if cwd_scripts.is_file():
        return cwd_scripts
    raise FileNotFoundError("voiceforge.service not found")


@app.command()
def install_service() -> None:
    """Install systemd user service and enable it."""
    unit_src = _service_unit_path()
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    user_dir = Path(xdg) / "systemd" / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    unit_dst = user_dir / "voiceforge.service"
    shutil.copy2(unit_src, unit_dst)
    typer.echo(f"Скопировано: {unit_dst}")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)  # nosec B603 B607
    subprocess.run(["systemctl", "--user", "enable", "--now", "voiceforge.service"], check=True)  # nosec B603 B607
    typer.echo("Сервис включён. Логи: journalctl --user -u voiceforge -f")


@app.command("uninstall-service")
def uninstall_service() -> None:
    """Disable and stop systemd user service."""
    subprocess.run(["systemctl", "--user", "disable", "--now", "voiceforge.service"], check=True)  # nosec B603 B607
    typer.echo("Сервис voiceforge отключён и остановлен.")


@app.command()
def cost(
    days: int = typer.Option(30, "--days", help="За последние N дней (если не заданы --from/--to)"),
    from_date: str | None = typer.Option(None, "--from", help="Начало периода YYYY-MM-DD"),
    to_date: str | None = typer.Option(None, "--to", help="Конец периода YYYY-MM-DD"),
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
) -> None:
    """Отчёт по затратам LLM (из БД метрик)."""
    from datetime import date

    from voiceforge.core.metrics import get_stats, get_stats_range

    if from_date is not None and to_date is not None:
        try:
            fd = date.fromisoformat(from_date)
            td = date.fromisoformat(to_date)
        except ValueError as e:
            typer.echo(f"Неверный формат даты (ожидается YYYY-MM-DD): {e}", err=True)
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
    # Текстовый вывод: итог + по дням
    total = data.get("total_cost_usd") or 0
    calls = data.get("total_calls") or 0
    typer.echo(f"Затраты: ${total:.4f} (вызовов: {calls})")
    by_day = data.get("by_day") or []
    if by_day:
        typer.echo("По дням:")
        for row in by_day[-10:]:  # последние 10 дней
            d = row.get("date", "")
            c = row.get("cost_usd") or 0
            n = row.get("calls") or 0
            typer.echo(f"  {d}: ${c:.4f} ({n})")


@app.command()
def status(
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
    detailed: bool = typer.Option(False, "--detailed", help="Разбивка затрат по моделям/дням и % от бюджета"),
    doctor: bool = typer.Option(False, "--doctor", help="Диагностика окружения (конфиг, keyring, RAG, ring, Ollama, RAM, импорты)"),
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
        typer.echo("Формат должен быть md или pdf.", err=True)
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
        typer.echo(f"Экспорт: {out_path}")
        return
    # PDF: write temp md, run pandoc
    tmp_md = out_path.with_suffix(".md")
    tmp_md.write_text(md_text, encoding="utf-8")
    try:
        subprocess.run(
            ["pandoc", str(tmp_md), "-o", str(out_path), "--pdf-engine=pdflatex"],
            check=True,
            capture_output=True,
        )
        tmp_md.unlink(missing_ok=True)
        typer.echo(f"Экспорт: {out_path}")
    except FileNotFoundError:
        typer.echo("Для PDF установите pandoc и pdflatex (или: pandoc -o out.pdf session.md).", err=True)
        typer.echo(f"Markdown сохранён: {tmp_md}")
        raise SystemExit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Ошибка pandoc: {e.stderr.decode() if e.stderr else e}", err=True)
        raise SystemExit(1) from e


@app.command()
def history(
    session_id: int | None = typer.Option(None, "--id", help="Показать детали сессии"),
    last_n: int = typer.Option(10, "--last", help="Сколько последних сессий показать"),
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json | md (md только с --id)"),
    search: str | None = typer.Option(None, "--search", help="Поиск по тексту транскриптов (FTS5)"),
    date: str | None = typer.Option(None, "--date", help="Сессии за день YYYY-MM-DD"),
    from_date: str | None = typer.Option(None, "--from", help="Начало периода (с --to)"),
    to_date: str | None = typer.Option(None, "--to", help="Конец периода (с --from)"),
    action_items: bool = typer.Option(False, "--action-items", help="Список action items по сессиям (cross-session)"),
) -> None:
    """Show recent sessions or one detailed session."""
    from datetime import date as date_type

    from voiceforge.core.transcript_log import TranscriptLog

    log_db = TranscriptLog()
    try:
        if output == "md" and session_id is None:
            typer.echo(t("history.md_requires_id"), err=True)
            raise SystemExit(1)
        if action_items:
            items = log_db.get_action_items(limit=100)
            if output == "json":
                typer.echo(
                    json.dumps(
                        _cli_success_payload(
                            {
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
                        ),
                        ensure_ascii=False,
                    )
                )
            else:
                if not items:
                    typer.echo(t("history.no_action_items"))
                else:
                    for r in items:
                        assign = f" ({r.assignee})" if r.assignee else ""
                        typer.echo(f"  [{r.session_id}] #{r.idx_in_analysis} {r.status}: {r.description}{assign}")
            return
        if search is not None:
            hits = log_db.search_transcripts(search.strip(), limit=30)
            if output == "json":
                typer.echo(
                    json.dumps(
                        _cli_success_payload(
                            {
                                "query": search,
                                "hits": [
                                    {"session_id": s, "start_sec": st, "end_sec": e, "snippet": sn}
                                    for s, _tx, st, e, sn in hits
                                ],
                            }
                        ),
                        ensure_ascii=False,
                    )
                )
            else:
                if not hits:
                    typer.echo(t("history.no_results"))
                    return
                for sid, _text, start_sec, end_sec, snippet in hits:
                    typer.echo(f"session_id={sid} | {start_sec:.1f}s | {snippet}")
            return
        if date is not None or (from_date is not None and to_date is not None):
            try:
                if date is not None:
                    if from_date or to_date:
                        typer.echo(t("history.date_or_range"), err=True)
                        raise SystemExit(1)
                    day = date_type.fromisoformat(date)
                    sessions = log_db.get_sessions_for_date(day)
                else:
                    fd = date_type.fromisoformat(from_date)
                    td = date_type.fromisoformat(to_date)
                    if fd > td:
                        typer.echo(t("history.from_after_to"), err=True)
                        raise SystemExit(1)
                    sessions = log_db.get_sessions_in_range(fd, td)
            except ValueError as e:
                typer.echo(t("history.date_invalid", err=str(e)), err=True)
                raise SystemExit(1) from e
            if output == "json":
                typer.echo(json.dumps(_cli_success_payload(build_sessions_payload(sessions)), ensure_ascii=False))
            else:
                if not sessions:
                    typer.echo(t("history.no_sessions_period"))
                else:
                    for line in render_sessions_table_lines(sessions):
                        typer.echo(line)
            return
        if session_id is not None:
            detail = log_db.get_session_detail(session_id)
            if detail is None:
                message = session_not_found_message(session_id)
                if output == "json":
                    typer.echo(json.dumps(_cli_error_payload("SESSION_NOT_FOUND", message), ensure_ascii=False))
                else:
                    typer.echo(message, err=True)
                raise SystemExit(1)
            segments, analysis = detail
            if output == "json":
                typer.echo(
                    json.dumps(
                        _cli_success_payload(build_session_detail_payload(session_id, segments, analysis)), ensure_ascii=False
                    )
                )
                return
            if output == "md":
                meta = log_db.get_session_meta(session_id)
                started_at = meta[0] if meta else None
                typer.echo(build_session_markdown(session_id, segments, analysis, started_at=started_at))
                return
            for line in render_session_detail_lines(session_id, segments, analysis):
                typer.echo(line)
            return

        sessions = log_db.get_sessions(last_n=last_n)
        if not sessions:
            if output == "json":
                typer.echo(json.dumps(_cli_success_payload({"sessions": []}), ensure_ascii=False))
            else:
                typer.echo(t("history.no_sessions"))
        else:
            if output == "json":
                typer.echo(json.dumps(_cli_success_payload(build_sessions_payload(sessions)), ensure_ascii=False))
            else:
                for line in render_sessions_table_lines(sessions):
                    typer.echo(line)
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


def main() -> None:
    structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
    app()


if __name__ == "__main__":
    main()
