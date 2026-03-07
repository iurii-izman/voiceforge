"""Block 4.1: Persistent daemon — D-Bus (com.voiceforge.App), PID file, Analyze/Status/Listen.
Block 6.1: GetSessions, GetSessionDetail, GetSettings, GetIndexedPaths for Tauri UI."""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import functools
import json
import os
import queue
import signal
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from voiceforge.core.config import Settings
from voiceforge.core.dbus_service import DaemonVoiceForgeInterface, run_dbus_service
from voiceforge.core.model_manager import ModelManager, set_model_manager

if TYPE_CHECKING:
    from voiceforge.stt.streaming import StreamingSegment

log = structlog.get_logger()

PID_FILE_NAME = "voiceforge.pid"


def _streaming_language_hint(cfg: object) -> str | None:
    """Language hint for streaming STT from config (auto → None)."""
    lang = getattr(cfg, "language", "auto")
    return None if lang in ("auto", "") else lang


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _pid_path() -> Path:
    xdg = os.environ.get("XDG_RUNTIME_DIR") or os.path.expanduser("~/.cache")
    return Path(xdg) / PID_FILE_NAME


class VoiceForgeDaemon:
    """Backend for D-Bus: analyze, status, listen_start/stop, is_listening. Lazy pipeline.
    Block 4.4: smart_trigger loop when listening."""

    def __init__(self, iface: DaemonVoiceForgeInterface | None = None) -> None:
        self._iface = iface
        self._cfg = Settings()
        self._model_manager = ModelManager(self._cfg)
        set_model_manager(self._model_manager)
        self._listen_stop = threading.Event()
        self._listen_thread: threading.Thread | None = None
        self._listen_active = False
        self._listen_lock = threading.Lock()
        self._trigger_stop = threading.Event()
        self._trigger_thread: threading.Thread | None = None

        # Block 12.1: Emitter for streaming STT via D-Bus signals
        self._streaming_chunk_queue: queue.Queue[tuple[str, str, float, bool]] = queue.Queue(maxsize=200)
        self._dbus_emitter_stop = threading.Event()
        self._dbus_emitter_thread: threading.Thread | None = None

        # Block 10.1: streaming STT state (partial + finals for UI polling)
        self._streaming_lock = threading.Lock()
        self._streaming_partial = ""
        self._streaming_finals: deque[dict] = deque(maxlen=500)
        self._streaming_stop = threading.Event()
        self._streaming_thread: threading.Thread | None = None
        self._streaming_capture: object = None

    def _dbus_streaming_emitter_loop(self) -> None:
        """Worker to get transcript chunks from queue and emit them as D-Bus signals."""
        if not self._iface:
            log.warning("dbus.emitter.no_interface", reason="Cannot emit signals")
            return

        log.info("dbus.emitter.started")
        while not self._dbus_emitter_stop.is_set():
            try:
                # Timeout allows the loop to check for the stop event periodically
                text, speaker, ts, is_final = self._streaming_chunk_queue.get(timeout=1)
                # D-Bus signal expects timestamp in milliseconds
                self._iface.TranscriptChunk(text, speaker, int(ts * 1000), is_final)
                self._streaming_chunk_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                log.error("dbus.emitter.failed", error=str(e))
        log.info("dbus.emitter.stopped")

    def analyze(self, seconds: int, template: str | None = None) -> tuple[str, int | None]:
        """Run full pipeline, save session, return (formatted text, session_id). Block 62: session_id for SessionCreated.
        template: optional meeting template. Respects analyze_timeout_sec (#39)."""
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.main import run_analyze_pipeline

        timeout_sec = max(1.0, float(getattr(self._cfg, "analyze_timeout_sec", 120.0)))
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(run_analyze_pipeline, seconds, template=template)
            try:
                text, segments_for_log, analysis_for_log = future.result(timeout=timeout_sec)
            except FuturesTimeoutError:
                return (
                    json.dumps(
                        {
                            "error": {
                                "code": "ANALYZE_TIMEOUT",
                                "message": "Analysis timed out",
                                "retryable": True,
                            }
                        }
                    ),
                    None,
                )
        session_id = None
        if segments_for_log is not None and analysis_for_log is not None:
            try:
                log_db = TranscriptLog()
                try:
                    session_id = log_db.log_session(
                        segments=segments_for_log,
                        duration_sec=float(seconds),
                        model=analysis_for_log.get("model", ""),
                        questions=analysis_for_log.get("questions"),
                        answers=analysis_for_log.get("answers"),
                        recommendations=analysis_for_log.get("recommendations"),
                        action_items=analysis_for_log.get("action_items"),
                        cost_usd=analysis_for_log.get("cost_usd", 0.0),
                        template=analysis_for_log.get("template"),
                    )
                finally:
                    log_db.close()
            except Exception as e:
                log.warning("daemon.analyze.log_failed", error=str(e))
        return (text, session_id)

    def status(self) -> str:
        """Return RAM + cost string."""
        from voiceforge.main import get_status_text

        return get_status_text()

    def listen_start(self) -> None:
        """Start ring-buffer recording in background thread.
        If smart_trigger: start trigger loop (check every 2 s)."""
        with self._listen_lock:
            if self._listen_active:
                return
            self._listen_stop.clear()
            self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listen_thread.start()
            self._listen_active = True

            # Start D-Bus emitter thread
            self._dbus_emitter_stop.clear()
            self._dbus_emitter_thread = threading.Thread(target=self._dbus_streaming_emitter_loop, daemon=True)
            self._dbus_emitter_thread.start()

            if self._cfg.smart_trigger:
                self._trigger_stop.clear()
                self._trigger_thread = threading.Thread(target=self._trigger_loop, daemon=True)
                self._trigger_thread.start()
                log.info("daemon.listen_started", smart_trigger=True)
            else:
                log.info("daemon.listen_started")

    def listen_stop(self) -> None:
        """Stop ring-buffer recording and trigger loop."""
        with self._listen_lock:
            if not self._listen_active:
                return
            self._listen_stop.set()
            self._trigger_stop.set()
            self._dbus_emitter_stop.set()  # Stop emitter
            if self._dbus_emitter_thread:
                self._dbus_emitter_thread.join(timeout=2.0)
            if self._listen_thread:
                self._listen_thread.join(timeout=5.0)
            if self._trigger_thread:
                self._trigger_thread.join(timeout=3.0)

            self._listen_thread = None
            self._trigger_thread = None
            self._dbus_emitter_thread = None

            self._streaming_stop.set()
            if self._streaming_thread:
                self._streaming_thread.join(timeout=4.0)
            self._streaming_thread = None
            self._streaming_capture = None
            self._listen_active = False
            log.info("daemon.listen_stopped")

    def swap_model(self, model_type: str, model_name: str) -> str:
        """Block 10.4: hot-swap STT or LLM model. Returns 'ok' or error message."""
        return self._model_manager.swap_model(model_type, model_name)

    def get_streaming_transcript(self) -> str:
        """Block 10.1: return JSON {partial, finals} for UI (polling)."""
        with self._streaming_lock:
            return json.dumps(
                {"partial": self._streaming_partial, "finals": list(self._streaming_finals)},
                ensure_ascii=False,
            )

    def is_listening(self) -> bool:
        with self._listen_lock:
            return self._listen_active

    def get_sessions(self, last_n: int) -> str:
        """Return JSON array of session summaries for UI."""
        try:
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                sessions = log_db.get_sessions(last_n=min(last_n, 500))
                out = [
                    {
                        "id": s.id,
                        "started_at": s.started_at,
                        "ended_at": s.ended_at,
                        "duration_sec": s.duration_sec,
                        "segments_count": s.segments_count,
                    }
                    for s in sessions
                ]
                return json.dumps(out, ensure_ascii=False)
            finally:
                log_db.close()
        except Exception as e:
            log.warning("daemon.get_sessions_failed", error=str(e))
            return "[]"

    def get_session_detail(self, session_id: int) -> str:
        """Return JSON with segments and analysis for session_id."""
        try:
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                detail = log_db.get_session_detail(session_id)
                if detail is None:
                    return "{}"
                segments, analysis = detail
                segs = [
                    {
                        "start_sec": s.start_sec,
                        "end_sec": s.end_sec,
                        "speaker": s.speaker,
                        "text": s.text,
                    }
                    for s in segments
                ]
                ana = None
                if analysis:
                    ana = {
                        "model": analysis.model,
                        "questions": analysis.questions,
                        "answers": analysis.answers,
                        "recommendations": analysis.recommendations,
                        "action_items": analysis.action_items,
                        "cost_usd": analysis.cost_usd,
                    }
                return json.dumps({"segments": segs, "analysis": ana}, ensure_ascii=False)
            finally:
                log_db.close()
        except Exception as e:
            log.warning("daemon.get_session_detail_failed", session_id=session_id, error=str(e))
            return "{}"

    def search_transcripts(self, query: str, limit: int = 20) -> str:
        """Return JSON array of FTS hits: session_id, text, start_sec, end_sec, snippet."""
        if not query or not query.strip():
            return "[]"
        try:
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                hits = log_db.search_transcripts(query.strip(), limit=min(limit, 50))
                out = [
                    {
                        "session_id": h[0],
                        "text": h[1],
                        "start_sec": h[2],
                        "end_sec": h[3],
                        "snippet": h[4],
                    }
                    for h in hits
                ]
                return json.dumps(out, ensure_ascii=False)
            finally:
                log_db.close()
        except Exception as e:
            log.warning("daemon.search_transcripts_failed", error=str(e))
            return "[]"

    def get_settings(self) -> str:
        """Return JSON with current settings for UI. privacy_mode is alias for pii_mode (W4)."""
        c = self._cfg
        pii = getattr(c, "pii_mode", "ON")
        return json.dumps(
            {
                "model_size": c.model_size,
                "stt_backend": getattr(c, "stt_backend", "local"),
                "default_llm": c.default_llm,
                "budget_limit_usd": c.budget_limit_usd,
                "smart_trigger": c.smart_trigger,
                "sample_rate": c.sample_rate,
                "streaming_stt": c.streaming_stt,
                "pii_mode": pii,
                "privacy_mode": pii,
                "language": getattr(c, "language", "auto"),
                "calendar_autostart_enabled": getattr(c, "calendar_autostart_enabled", False),
                "calendar_autostart_minutes": getattr(c, "calendar_autostart_minutes", 5),
            },
            ensure_ascii=False,
        )

    def get_indexed_paths(self) -> str:
        """Return JSON array of distinct source paths from RAG DB."""
        try:
            import sqlite3

            db_path = self._cfg.get_rag_db_path()
            if not Path(db_path).is_file():
                return "[]"
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.execute("SELECT DISTINCT source FROM chunks ORDER BY source")
                paths = [row[0] for row in cur.fetchall()]
                return json.dumps(paths, ensure_ascii=False)
            finally:
                conn.close()
        except Exception as e:
            log.warning("daemon.get_indexed_paths_failed", error=str(e))
            return "[]"

    def get_session_ids_with_action_items(self) -> str:
        """Return JSON array of session_id that have at least one action item (block 47)."""
        try:
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                ids = log_db.get_session_ids_with_action_items()
                return json.dumps(ids, ensure_ascii=False)
            finally:
                log_db.close()
        except Exception as e:
            log.warning("daemon.get_session_ids_with_action_items_failed", error=str(e))
            return "[]"

    def get_upcoming_events(self, hours_ahead: int = 48) -> str:
        """Return JSON array of upcoming calendar events (block 64)."""
        try:
            from voiceforge.calendar import get_upcoming_events as cal_get_upcoming

            events, err = cal_get_upcoming(hours_ahead=hours_ahead)
            if err:
                log.debug("daemon.get_upcoming_events_skipped", error=err)
                return "[]"
            return json.dumps(events, ensure_ascii=False)
        except Exception as e:
            log.warning("daemon.get_upcoming_events_failed", error=str(e))
            return "[]"

    def get_analytics(self, last: str) -> str:
        """Return JSON analytics for period (e.g. last='7d' or '30d'). Block 11.5."""
        days = 30
        if last:
            s = (last or "").strip().lower()
            if s.endswith("d") and s[:-1].isdigit():
                days = min(365, max(1, int(s[:-1])))
            elif s.isdigit():
                days = min(365, max(1, int(s)))
        try:
            from voiceforge.core.metrics import get_stats

            data = get_stats(days=days)
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            log.warning("daemon.get_analytics_failed", error=str(e))
            return "{}"

    def get_api_version(self) -> str:
        """D-Bus API contract version."""
        return "1.0"

    def get_version(self) -> str:
        """Application version for UI/daemon sync (block 61)."""
        try:
            from importlib.metadata import version

            return version("voiceforge")
        except Exception:
            return "0.2.0-alpha.1"

    def get_capabilities(self) -> str:
        """Return capabilities supported by this daemon build."""
        return json.dumps(
            {
                "api_version": "1.0",
                "features": {
                    "listen": True,
                    "analyze": True,
                    "streaming_transcript": True,
                    "swap_model": True,
                    "analytics": True,
                    "signals": True,
                    "signals_v1": True,
                    "analyze_timeout_v1": True,
                    "envelope_v1": _env_flag("VOICEFORGE_IPC_ENVELOPE", default=True),
                },
            },
            ensure_ascii=False,
        )

    def _streaming_loop(self) -> None:
        """Block 10.1: every 1.5s get 2s chunk, transcribe, update _streaming_partial/_streaming_finals."""
        capture = self._streaming_capture
        if capture is None or not getattr(capture, "get_chunk", None):
            return
        get_chunk = getattr(capture, "get_chunk", None)
        if get_chunk is None:
            return
        try:
            from voiceforge.stt import get_transcriber_for_config
            from voiceforge.stt.streaming import StreamingTranscriber
        except ImportError:
            return
        transcriber = get_transcriber_for_config(self._cfg)

        def on_partial(text: str) -> None:
            # For D-Bus signal emitter
            with contextlib.suppress(queue.Full):
                self._streaming_chunk_queue.put_nowait((text, "SPEAKER_??", 0.0, False))

            # For polling clients
            if text:
                with self._streaming_lock:
                    self._streaming_partial = text

        def on_final(segment: StreamingSegment) -> None:
            t = getattr(segment, "text", "") or ""
            if not t.strip():
                return
            start = getattr(segment, "start", 0.0)
            end = getattr(segment, "end", 0.0)

            # For D-Bus signal emitter
            with contextlib.suppress(queue.Full):
                self._streaming_chunk_queue.put_nowait((t, "SPEAKER_??", end, True))

            # For polling clients
            with self._streaming_lock:
                self._streaming_finals.append({"text": t, "start": start, "end": end})

        language_hint = _streaming_language_hint(self._cfg)
        stream = StreamingTranscriber(
            transcriber,
            sample_rate=self._cfg.sample_rate,
            language=language_hint,
            on_partial=on_partial,
            on_final=on_final,
        )
        chunk_sec, interval_sec = 2.0, 1.5
        min_samples = int(self._cfg.sample_rate * chunk_sec * 0.5)

        def process_one_chunk() -> None:
            try:
                mic, _ = get_chunk(chunk_sec)
                if mic.size >= min_samples:
                    stream.process_chunk(mic, start_offset_sec=0.0)
            except Exception as e:
                log.warning("daemon.streaming_stt.failed", error=str(e))

        while not self._streaming_stop.is_set():
            if self._streaming_stop.wait(timeout=interval_sec):
                break
            process_one_chunk()

    def _listen_loop(self) -> None:
        try:
            from voiceforge.audio.capture import AudioCapture
        except ImportError:
            log.warning("daemon.listen_no_audio_module")
            with self._listen_lock:
                self._listen_active = False
            return
        ring_path = self._cfg.get_ring_file_path()
        Path(ring_path).parent.mkdir(parents=True, exist_ok=True)
        capture = AudioCapture(
            sample_rate=self._cfg.sample_rate,
            buffer_seconds=self._cfg.ring_seconds,
            monitor_source=self._cfg.monitor_source,
        )
        capture.start()
        if self._cfg.streaming_stt:
            with self._streaming_lock:
                self._streaming_partial = ""
                self._streaming_finals.clear()
            self._streaming_stop.clear()
            self._streaming_capture = capture
            self._streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
            self._streaming_thread.start()
        try:
            while not self._listen_stop.wait(timeout=2.0):
                mic, _ = capture.get_chunk(self._cfg.ring_seconds)
                if mic.size > 0:
                    ring = Path(ring_path)
                    tmp = ring.with_suffix(".tmp")
                    tmp.write_bytes(mic.tobytes())
                    os.replace(tmp, ring)
        finally:
            # Stop streaming thread before capture so it doesn't call get_chunk on stopped device
            if self._streaming_thread:
                self._streaming_stop.set()
                self._streaming_thread.join(timeout=4.0)
                self._streaming_thread = None
            self._streaming_capture = None
            capture.stop()

    def _trigger_loop(self) -> None:
        """Every 2 s: SmartTrigger.check(ring_path); if fired, run analyze and log."""
        from voiceforge.audio.smart_trigger import SmartTrigger

        ring_path = self._cfg.get_ring_file_path()
        trigger = SmartTrigger(
            sample_rate=self._cfg.sample_rate,
            min_speech_sec=30.0,
            min_silence_sec=3.0,
            cooldown_sec=120.0,
            analyze_seconds=30,
        )
        while not self._trigger_stop.wait(timeout=2.0):
            if self._trigger_stop.is_set():
                break
            if not trigger.check(ring_path):
                continue
            try:
                from voiceforge.main import run_analyze_pipeline

                template = getattr(self._cfg, "smart_trigger_template", None)
                text, segments_for_log, analysis_for_log = run_analyze_pipeline(trigger.analyze_seconds, template=template)
                if text.startswith("Ошибка:") or text.startswith("Error:"):
                    log.warning("smart_trigger.analyze_failed", message=text[:100])
                    continue
                from voiceforge.core.transcript_log import TranscriptLog

                log_db = TranscriptLog()
                try:
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
                    log.info("smart_trigger.logged", session_id=session_id)
                    try:
                        from voiceforge.core.telegram_notify import notify_analyze_done

                        notify_analyze_done(session_id, (text or "")[:400])
                    except Exception as _e:
                        log.debug("smart_trigger.telegram_notify_failed", error=str(_e))
                finally:
                    log_db.close()
            except Exception as e:
                log.warning("smart_trigger.error", error=str(e))


def _retention_purge_at_startup(daemon: VoiceForgeDaemon) -> None:
    """Run retention purge once at daemon startup (#43). Extracted for S3776."""
    retention_days = getattr(daemon._cfg, "retention_days", 0)
    if retention_days <= 0:
        return
    from datetime import date, timedelta

    from voiceforge.core.transcript_log import TranscriptLog

    cutoff = date.today() - timedelta(days=retention_days)
    log_db = TranscriptLog()
    try:
        n = log_db.purge_before(cutoff)
        if n:
            log.info("retention.purged_at_startup", count=n, cutoff=cutoff.isoformat())
    finally:
        log_db.close()


def _wire_daemon_iface(iface: DaemonVoiceForgeInterface, daemon: VoiceForgeDaemon) -> None:
    """Wire real daemon methods to D-Bus iface. Extracted for S3776."""
    iface._analyze = daemon.analyze
    iface._status = daemon.status
    iface._listen_start = daemon.listen_start
    iface._listen_stop = daemon.listen_stop
    iface._is_listening = daemon.is_listening
    iface._get_sessions = daemon.get_sessions
    iface._get_session_detail = daemon.get_session_detail
    iface._search_transcripts = daemon.search_transcripts
    iface._get_settings = daemon.get_settings
    iface._get_indexed_paths = daemon.get_indexed_paths
    iface._get_session_ids_with_action_items = daemon.get_session_ids_with_action_items
    iface._get_upcoming_events = lambda: daemon.get_upcoming_events(48)
    iface._get_streaming_transcript = daemon.get_streaming_transcript
    iface._swap_model = daemon.swap_model
    iface._ping = lambda: "pong"
    iface._get_analytics = daemon.get_analytics
    iface._get_api_version = daemon.get_api_version
    iface._get_version = daemon.get_version
    iface._get_capabilities = daemon.get_capabilities


async def _run_one_retention_purge(daemon: VoiceForgeDaemon) -> tuple[int, date | None]:
    """Run one retention purge in executor. Returns (count, cutoff_date). S3776."""
    from datetime import date, timedelta

    from voiceforge.core.transcript_log import TranscriptLog

    retention_days = getattr(daemon._cfg, "retention_days", 0)
    if retention_days <= 0:
        return (0, None)

    def do_purge(cutoff_date: date) -> int:
        log_db = TranscriptLog()
        try:
            return log_db.purge_before(cutoff_date)
        finally:
            log_db.close()

    cutoff = date.today() - timedelta(days=retention_days)
    loop = asyncio.get_running_loop()
    n = await loop.run_in_executor(None, functools.partial(do_purge, cutoff))
    return (n, cutoff)


async def _cancel_purge_then_service_reraise(
    purge_task: asyncio.Task,
    service_task: asyncio.Task,
) -> None:
    """Cancel purge_task, then service_task; re-raise CancelledError after cleanup. S3776/S7497."""
    purge_task.cancel()
    try:
        await purge_task
    except asyncio.CancelledError as exc:
        service_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await service_task
        raise exc
    service_task.cancel()
    await service_task  # CancelledError propagates to caller (S2737: avoid redundant rethrow)


def _event_start_in_window(ev: dict, now: datetime, window_end: datetime) -> bool:
    """True if event start time is in [now, window_end] (S3776)."""
    start_iso = ev.get("start_iso") or ""
    if not start_iso:
        return False
    try:
        if start_iso.endswith("Z"):
            start_iso = start_iso[:-1] + "+00:00"
        event_start = datetime.fromisoformat(start_iso)
        if event_start.tzinfo is None:
            event_start = event_start.replace(tzinfo=UTC)
        return now <= event_start <= window_end
    except (ValueError, TypeError):
        return False


def _calendar_autostart_try_start(daemon: VoiceForgeDaemon, minutes_ahead: int) -> None:
    """If an event starts within minutes_ahead, start listen (S3776)."""
    try:
        from voiceforge.calendar import get_upcoming_events

        events, err = get_upcoming_events(hours_ahead=1)
        if err or not events:
            return
        now = datetime.now(UTC)
        window_end = now + timedelta(minutes=minutes_ahead)
        for ev in events:
            if _event_start_in_window(ev, now, window_end):
                log.info(
                    "calendar_autostart.starting",
                    summary=ev.get("summary", ""),
                    start=ev.get("start_iso", ""),
                )
                daemon.listen_start()
                return
    except Exception as e:
        log.debug("calendar_autostart.check_failed", error=str(e))


def _calendar_autostart_loop(daemon: VoiceForgeDaemon) -> None:
    """Block 78: every 60s, if an event starts within N minutes and not listening, start listen."""
    if not getattr(daemon._cfg, "calendar_autostart_enabled", False):
        return
    minutes_ahead = max(1, getattr(daemon._cfg, "calendar_autostart_minutes", 5))
    interval_sec = 60
    while True:
        try:
            import time

            time.sleep(interval_sec)
        except Exception:
            break
        if not daemon.is_listening():
            _calendar_autostart_try_start(daemon, minutes_ahead)


async def _periodic_purge_task(daemon: VoiceForgeDaemon, stop_event: asyncio.Event) -> None:
    """Run retention purge every 24h (S3776: extracted from _run_daemon_loop)."""
    PURGE_INTERVAL_SEC = 86400  # 24h (#63)
    while True:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=PURGE_INTERVAL_SEC)
        if stop_event.is_set():
            return
        try:
            n, cutoff = await _run_one_retention_purge(daemon)
            if n and cutoff is not None:
                log.info("retention.purged_periodic", count=n, cutoff=cutoff.isoformat())
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("retention.purge_failed", error=str(e))


def _run_daemon_loop(
    iface: DaemonVoiceForgeInterface,
    daemon: VoiceForgeDaemon,
    stop_event: asyncio.Event,
    pid_path: Path,
    loop_holder: list[asyncio.AbstractEventLoop | None],
) -> None:
    """Run asyncio loop with D-Bus service and periodic purge. S3776: extracted from run_daemon."""

    async def _serve() -> None:
        service_task = asyncio.create_task(run_dbus_service(iface))
        purge_task = asyncio.create_task(_periodic_purge_task(daemon, stop_event))
        try:
            await stop_event.wait()
        finally:
            await _cancel_purge_then_service_reraise(purge_task, service_task)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop_holder[0] = loop
    try:
        loop.run_until_complete(_serve())
    except Exception as e:
        log.exception("daemon.crash", error=str(e), pid=os.getpid(), pid_file=str(pid_path))
        raise
    finally:
        loop.close()


def run_daemon() -> None:
    """Run daemon: write PID, register D-Bus, graceful SIGTERM."""
    pid_path = _pid_path()
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    def _dummy_analyze(seconds: int, template: str | None = None) -> tuple[str, int | None]:
        return ("", None)

    iface = DaemonVoiceForgeInterface(
        analyze_fn=_dummy_analyze,
        status_fn=lambda: "",
        listen_start_fn=lambda: None,
        listen_stop_fn=lambda: None,
        is_listening_fn=lambda: False,
    )
    daemon = VoiceForgeDaemon(iface)
    _retention_purge_at_startup(daemon)
    _wire_daemon_iface(iface, daemon)

    if getattr(daemon._cfg, "calendar_autostart_enabled", False):
        _calendar_thread = threading.Thread(target=_calendar_autostart_loop, args=(daemon,), daemon=True)
        _calendar_thread.start()
        log.info("daemon.calendar_autostart_enabled", minutes=getattr(daemon._cfg, "calendar_autostart_minutes", 5))

    log.info("daemon.starting", pid=os.getpid(), pid_file=str(pid_path))
    stop_event = asyncio.Event()
    loop_holder: list[asyncio.AbstractEventLoop | None] = [None]

    def on_sigterm(*args: object) -> None:
        log.info("daemon.sigterm")
        daemon.listen_stop()
        pid_path.unlink(missing_ok=True)
        loop = loop_holder[0]
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGTERM, on_sigterm)
    signal.signal(signal.SIGINT, on_sigterm)
    pid_path.write_text(str(os.getpid()))
    atexit.register(lambda: pid_path.unlink(missing_ok=True))

    _run_daemon_loop(iface, daemon, stop_event, pid_path, loop_holder)
