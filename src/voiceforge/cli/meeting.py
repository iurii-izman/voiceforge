"""One-shot meeting mode: listen + optional smart-trigger + analyze on Ctrl+C (E2 #125)."""

from __future__ import annotations

import os
import signal
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog
import typer

from voiceforge.core.contracts import extract_error_message
from voiceforge.i18n import t

log = structlog.get_logger()


def _persist_ring_snapshot(capture: Any, ring_path: str, seconds: float) -> bool:
    """Persist current capture snapshot to ring file; prefer mic, fall back to monitor."""
    mic, monitor = capture.get_chunk(seconds)
    audio = mic if mic.size > 0 else monitor
    if audio.size <= 0:
        return False
    ring = Path(ring_path)
    tmp = ring.with_suffix(".tmp")
    tmp.write_bytes(audio.tobytes())
    os.replace(tmp, ring)
    return True


def _run_meeting_preflight(cfg: Any) -> None:
    from voiceforge.core.preflight import check_disk_space, check_pipewire, get_pipewire_fix_key

    pw_err = check_pipewire()
    if pw_err:
        typer.echo(t(pw_err), err=True)
        typer.echo(t(get_pipewire_fix_key(pw_err)), err=True)
        raise SystemExit(1)
    disk_err, disk_warn = check_disk_space(cfg.get_data_dir())
    if disk_err:
        typer.echo(t(disk_err), err=True)
        raise SystemExit(1)
    if disk_warn:
        typer.echo(t(disk_warn), err=True)


def _build_capture(cfg: Any) -> Any:
    try:
        from voiceforge.audio.capture import AudioCapture
    except ImportError:
        typer.echo(t("error.audio_module_not_found"), err=True)
        raise SystemExit(1) from None
    return AudioCapture(
        sample_rate=cfg.sample_rate,
        buffer_seconds=cfg.ring_seconds,
        monitor_source=cfg.monitor_source,
    )


def _notify_desktop(summary_text: str) -> None:
    try:
        from voiceforge.core.desktop_notify import notify_analyze_done as desktop_notify

        desktop_notify(summary_text[:80])
    except Exception:
        pass


def _log_session(duration_sec: float, segments_for_log: list[Any], analysis_for_log: dict[str, Any]) -> int | None:
    try:
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        session_id = log_db.log_session(
            segments=segments_for_log,
            duration_sec=duration_sec,
            model=analysis_for_log.get("model", ""),
            questions=analysis_for_log.get("questions"),
            answers=analysis_for_log.get("answers"),
            recommendations=analysis_for_log.get("recommendations"),
            action_items=analysis_for_log.get("action_items"),
            cost_usd=analysis_for_log.get("cost_usd", 0.0),
            template=analysis_for_log.get("template"),
        )
        log_db.close()
        return session_id
    except Exception as e:
        log.warning("meeting.log_failed", error=str(e))
        return None


def _analyze_and_log(seconds: int, template: str | None) -> tuple[str, int | None]:
    from voiceforge.main import run_analyze_pipeline

    display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds, template=template)
    err_msg = extract_error_message(display_text)
    if err_msg is not None:
        typer.echo(err_msg, err=True)
        raise SystemExit(1)
    session_id = _log_session(seconds, segments_for_log, analysis_for_log)
    _notify_desktop(display_text or "")
    return display_text, session_id


def _run_smart_trigger_analysis(trigger: Any, template: str | None) -> None:
    from voiceforge.main import run_analyze_pipeline

    text, segments_for_log, analysis_for_log = run_analyze_pipeline(trigger.analyze_seconds, template=template)
    if extract_error_message(text) is not None:
        log.warning("meeting.smart_trigger.analyze_failed", message=text[:100])
        return
    typer.echo("\n--- Smart trigger analyze ---")
    typer.echo(text)
    session_id = _log_session(float(trigger.analyze_seconds), segments_for_log, analysis_for_log)
    if session_id is not None:
        log.info("meeting.smart_trigger.logged", session_id=session_id)
    _notify_desktop(text or "")


def _start_smart_trigger_thread(
    cfg: Any, ring_path: str, template: str | None, no_analyze: bool
) -> tuple[threading.Event, threading.Thread | None]:
    trigger_stop = threading.Event()
    smart_trigger_enabled = getattr(cfg, "smart_trigger", True)
    if not smart_trigger_enabled or no_analyze:
        return trigger_stop, None

    def _trigger_worker() -> None:
        from voiceforge.audio.smart_trigger import SmartTrigger

        trigger = SmartTrigger(
            sample_rate=cfg.sample_rate,
            min_speech_sec=30.0,
            min_silence_sec=3.0,
            cooldown_sec=120.0,
            analyze_seconds=30,
        )
        template_val = template or getattr(cfg, "smart_trigger_template", None)
        while not trigger_stop.wait(timeout=2.0):
            if not trigger.check(ring_path):
                continue
            try:
                _run_smart_trigger_analysis(trigger, template_val)
            except Exception as e:
                log.warning("meeting.smart_trigger.error", error=str(e))

    trigger_thread = threading.Thread(target=_trigger_worker, daemon=True)
    trigger_thread.start()
    return trigger_stop, trigger_thread


def _run_capture_loop(
    capture: Any,
    ring_path: str,
    ring_seconds: float,
    persist_interval: float,
    should_stop: Callable[[], bool],
) -> None:
    last_persist_at: float = 0.0
    while not should_stop():
        now = time.monotonic()
        if now - last_persist_at >= persist_interval and _persist_ring_snapshot(capture, ring_path, ring_seconds):
            last_persist_at = now
        if should_stop():
            break
        time.sleep(2.0)


def run_meeting(
    cfg: Any,
    template: str | None = None,
    no_analyze: bool = False,
    seconds: int | None = None,
) -> None:
    """Run standalone listen loop; on Ctrl+C run analyze and exit. Smart trigger in background if enabled."""
    _run_meeting_preflight(cfg)

    ring_path = cfg.get_ring_file_path()
    Path(ring_path).parent.mkdir(parents=True, exist_ok=True)
    capture = _build_capture(cfg)
    capture.start()

    stop = False

    def on_signal(*args: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    trigger_stop, trigger_thread = _start_smart_trigger_thread(cfg, ring_path, template, no_analyze)

    typer.echo(t("meeting.listening_hint"), err=True)

    persist_interval = max(1.0, getattr(cfg, "ring_persist_interval_sec", 10.0))
    try:
        _run_capture_loop(capture, ring_path, cfg.ring_seconds, persist_interval, lambda: stop)
    finally:
        trigger_stop.set()
        if trigger_thread:
            trigger_thread.join(timeout=4.0)
        _persist_ring_snapshot(capture, ring_path, cfg.ring_seconds)
        capture.stop()

    if no_analyze:
        return

    analyze_seconds = int(cfg.ring_seconds) if seconds is None else seconds
    display_text, session_id = _analyze_and_log(analyze_seconds, template)

    if session_id is not None:
        typer.echo(f"session_id={session_id}")
    typer.echo(display_text or "")
