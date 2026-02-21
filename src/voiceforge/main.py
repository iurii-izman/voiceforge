"""VoiceForge CLI entrypoint (alpha0.1 minimal core)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

import structlog
import typer

from voiceforge.cli.history_helpers import (
    build_session_detail_payload,
    build_sessions_payload,
    render_session_detail_lines,
    render_sessions_table_lines,
    session_not_found_message,
)
from voiceforge.cli.status_helpers import get_status_data, get_status_text
from voiceforge.core.config import Settings
from voiceforge.core.contracts import (
    build_cli_error_payload,
    build_cli_success_payload,
    extract_error_message,
)

log = structlog.get_logger()
app = typer.Typer(help="VoiceForge — local-first AI assistant (alpha0.1 core)")

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


def run_analyze_pipeline(seconds: int) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
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
            transcript_pre_redacted=transcript_redacted,
        )
    except ImportError:
        return ("Ошибка: установите LLM зависимости (uv sync --extra llm).", [], {})
    except Exception as e:
        log.warning("analyze.llm_failed", error=str(e))
        return (f"Ошибка LLM: {e}", [], {})

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


@app.command()
def listen(
    duration: int = typer.Option(0, help="Секунды (0 = бесконечно)"),
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
        capture.stop()


@app.command()
def analyze(
    seconds: int = typer.Option(30, help="Последние N секунд"),
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
) -> None:
    """Analyze ring-buffer fragment: transcribe -> diarize -> rag -> llm."""
    display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds)
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
        typer.echo(f"Ошибка: путь не найден: {path}", err=True)
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
        typer.echo(f"Ошибка: папка не найдена: {path}", err=True)
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
def status(
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
) -> None:
    """Show RAM and cost snapshot."""
    if output == "json":
        typer.echo(json.dumps(_cli_success_payload(get_status_data()), ensure_ascii=False))
    else:
        typer.echo(get_status_text())


@app.command()
def history(
    session_id: int | None = typer.Option(None, "--id", help="Показать детали сессии"),
    last_n: int = typer.Option(10, "--last", help="Сколько последних сессий показать"),
    output: str = typer.Option("text", "--output", help="Формат вывода: text | json"),
) -> None:
    """Show recent sessions or one detailed session."""
    from voiceforge.core.transcript_log import TranscriptLog

    log_db = TranscriptLog()
    try:
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
                typer.echo(json.dumps(_cli_success_payload(build_session_detail_payload(session_id, segments, analysis)), ensure_ascii=False))
                return
            for line in render_session_detail_lines(session_id, segments, analysis):
                typer.echo(line)
            return

        sessions = log_db.get_sessions(last_n=last_n)
        if not sessions:
            if output == "json":
                typer.echo(json.dumps(_cli_success_payload({"sessions": []}), ensure_ascii=False))
            else:
                typer.echo("Нет сохранённых сессий. Запустите voiceforge analyze.")
            return
        if output == "json":
            typer.echo(json.dumps(_cli_success_payload(build_sessions_payload(sessions)), ensure_ascii=False))
            return
        for line in render_sessions_table_lines(sessions):
            typer.echo(line)
    finally:
        log_db.close()


def main() -> None:
    structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
    app()


if __name__ == "__main__":
    main()
