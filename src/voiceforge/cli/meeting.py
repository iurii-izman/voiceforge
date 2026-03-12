"""One-shot meeting mode: listen + optional smart-trigger + analyze on Ctrl+C (E2 #125)."""

from __future__ import annotations

import os
import signal
import threading
import time
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


def run_meeting(
    cfg: Any,
    template: str | None = None,
    no_analyze: bool = False,
    seconds: int | None = None,
) -> None:
    """Run standalone listen loop; on Ctrl+C run analyze and exit. Smart trigger in background if enabled."""
    from voiceforge.core.preflight import check_disk_space, check_pipewire, get_pipewire_fix_key

    pw_err = check_pipewire()
    if pw_err:
        typer.echo(t(pw_err), err=True)
        typer.echo(t(get_pipewire_fix_key(pw_err)), err=True)
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
    trigger_stop = threading.Event()
    trigger_thread: threading.Thread | None = None
    smart_trigger_enabled = getattr(cfg, "smart_trigger", True)

    def on_signal(*args: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    if smart_trigger_enabled and not no_analyze:

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
                if trigger_stop.is_set():
                    break
                if not trigger.check(ring_path):
                    continue
                try:
                    from voiceforge.main import run_analyze_pipeline

                    text, segments_for_log, analysis_for_log = run_analyze_pipeline(
                        trigger.analyze_seconds, template=template_val
                    )
                    if extract_error_message(text) is not None:
                        log.warning("meeting.smart_trigger.analyze_failed", message=text[:100])
                        continue
                    typer.echo("\n--- Smart trigger analyze ---")
                    typer.echo(text)
                    try:
                        from voiceforge.core.transcript_log import TranscriptLog

                        log_db = TranscriptLog()
                        session_id = log_db.log_session(
                            segments=segments_for_log,
                            duration_sec=float(trigger.analyze_seconds),
                            model=analysis_for_log.get("model", ""),
                            questions=analysis_for_log.get("questions"),
                            answers=analysis_for_log.get("answers"),
                            recommendations=analysis_for_log.get("recommendations"),
                            action_items=analysis_for_log.get("action_items"),
                            cost_usd=analysis_for_log.get("cost_usd", 0.0),
                            template=analysis_for_log.get("template"),
                        )
                        log_db.close()
                        log.info("meeting.smart_trigger.logged", session_id=session_id)
                    except Exception as e:
                        log.warning("meeting.smart_trigger.log_failed", error=str(e))
                    try:
                        from voiceforge.core.desktop_notify import notify_analyze_done as desktop_notify

                        desktop_notify((text or "")[:80])
                    except Exception:
                        pass
                except Exception as e:
                    log.warning("meeting.smart_trigger.error", error=str(e))

        trigger_thread = threading.Thread(target=_trigger_worker, daemon=True)
        trigger_thread.start()

    typer.echo(t("meeting.listening_hint"), err=True)

    persist_interval = max(1.0, getattr(cfg, "ring_persist_interval_sec", 10.0))
    last_persist_at: float = 0.0
    try:
        while not stop:
            now = time.monotonic()
            if now - last_persist_at >= persist_interval and _persist_ring_snapshot(capture, ring_path, cfg.ring_seconds):
                last_persist_at = now
            if stop:
                break
            time.sleep(2.0)
    finally:
        trigger_stop.set()
        if trigger_thread:
            trigger_thread.join(timeout=4.0)
        _persist_ring_snapshot(capture, ring_path, cfg.ring_seconds)
        capture.stop()

    if no_analyze:
        return

    analyze_seconds = int(cfg.ring_seconds) if seconds is None else seconds
    from voiceforge.main import run_analyze_pipeline

    display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(analyze_seconds, template=template)
    err_msg = extract_error_message(display_text)
    if err_msg is not None:
        typer.echo(err_msg, err=True)
        raise SystemExit(1)

    session_id: int | None = None
    try:
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        session_id = log_db.log_session(
            segments=segments_for_log,
            duration_sec=analyze_seconds,
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
        log.warning("meeting.log_failed", error=str(e))

    try:
        from voiceforge.core.desktop_notify import notify_analyze_done as desktop_notify

        desktop_notify((display_text or "")[:80])
    except Exception:
        pass

    if session_id is not None:
        typer.echo(f"session_id={session_id}")
    typer.echo(display_text or "")
