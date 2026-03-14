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
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from voiceforge.core.config import Settings
from voiceforge.core.dbus_service import DaemonVoiceForgeInterface, run_dbus_service
from voiceforge.core.model_manager import ModelManager, set_model_manager

if TYPE_CHECKING:
    from voiceforge.stt.streaming import StreamingSegment

log = structlog.get_logger()

PID_FILE_NAME = "voiceforge.pid"

# E5 #128: systemd watchdog — send status via NOTIFY_SOCKET (no extra dependency)
_WATCHDOG_INTERVAL_SEC = 30


def _sd_notify(message: str) -> bool:
    """Send message to systemd via NOTIFY_SOCKET. Returns True if sent."""
    sock_path = os.environ.get("NOTIFY_SOCKET")
    if not sock_path or not message:
        return False
    try:
        import socket

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.connect(sock_path)
        sock.sendall(message.encode("utf-8"))
        sock.close()
        return True
    except Exception:
        return False


def _streaming_language_hint(cfg: object) -> str | None:
    """Language hint for streaming STT from config (auto → None)."""
    lang = getattr(cfg, "language", "auto")
    return None if lang in ("auto", "") else lang


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _analyze_result_is_error_daemon(result: str) -> bool:
    """True if analyze result string indicates error (KC3: copilot release)."""
    if not result:
        return False
    if result.startswith("Ошибка:") or result.startswith("Error:"):
        return True
    try:
        parsed = json.loads(result)
        return isinstance(parsed, dict) and "error" in parsed
    except (json.JSONDecodeError, TypeError):
        return False


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
        # KC4: cache transcribers by size (tiny for copilot capture, default otherwise)
        self._streaming_transcriber_cache: dict[str, Any] = {}

        # KC3: copilot push-to-capture markers, pre-roll, 30s auto-stop
        self._copilot_lock = threading.Lock()
        self._listen_capture: Any = None  # AudioCapture while listen_loop is running
        self._copilot_capture_start_time: float | None = None
        self._copilot_warning_emitted = False
        self._copilot_watcher_stop = threading.Event()
        self._copilot_watcher_thread: threading.Thread | None = None
        self._last_copilot_stt_ambiguous = False
        self._last_copilot_transcript: str = ""  # KC4: transcript snippet for downstream/UI
        # KC5 (#177): evidence-first RAG for overlay
        self._last_copilot_rag_groundedness: str | None = None
        self._last_copilot_rag_citations: list[Any] = []
        self._last_copilot_rag_conflict_hint: str | None = None
        # KC6 (#178): fast-track cards Answer, Do/Don't, Clarify
        self._last_copilot_answer: list[str] = []
        self._last_copilot_dos: list[str] = []
        self._last_copilot_donts: list[str] = []
        self._last_copilot_clarify: list[str] = []
        self._last_copilot_confidence: float = 0.0
        # KC7 (#179): session memory — recent turns for conversation continuity (cleared on listen_stop)
        self._copilot_session_turns: list[str] = []
        self._COPILOT_SESSION_MAX_TURNS = 5
        # KC7: deep-track cards (Risk, Strategy, Emotion)
        self._last_copilot_risk: list[str] = []
        self._last_copilot_strategy: str = ""
        self._last_copilot_emotion: str | None = None

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

    def analyze(
        self,
        seconds: int,
        template: str | None = None,
        out_transcript: list[str] | None = None,
    ) -> tuple[str, int | None]:
        """Run full pipeline, save session, return (formatted text, session_id). Block 62: session_id for SessionCreated.
        template: optional meeting template. Respects analyze_timeout_sec (#39).
        KC4: if out_transcript is a list, it is filled with the raw STT transcript."""
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.main import run_analyze_pipeline

        timeout_sec = max(1.0, float(getattr(self._cfg, "analyze_timeout_sec", 120.0)))

        def stream_cb(delta: str | None) -> None:
            if self._iface:
                self._iface.StreamingAnalysisChunk(delta if delta is not None else "")

        with self._copilot_lock:
            session_ctx = list(self._copilot_session_turns[-self._COPILOT_SESSION_MAX_TURNS :])
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(
                run_analyze_pipeline,
                seconds,
                template=template,
                stream_callback=stream_cb,
                out_transcript=out_transcript,
                for_copilot=True,
                session_context=session_ctx if session_ctx else None,
            )
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
        with self._copilot_lock:
            self._last_copilot_rag_groundedness = analysis_for_log.get("rag_groundedness") if analysis_for_log else None
            self._last_copilot_rag_citations = list(analysis_for_log.get("rag_citations") or []) if analysis_for_log else []
            self._last_copilot_rag_conflict_hint = analysis_for_log.get("rag_conflict_hint") if analysis_for_log else None
            # KC6 (#178): fast-track cards
            self._last_copilot_answer = list(analysis_for_log.get("copilot_answer") or []) if analysis_for_log else []
            self._last_copilot_dos = list(analysis_for_log.get("copilot_dos") or []) if analysis_for_log else []
            self._last_copilot_donts = list(analysis_for_log.get("copilot_donts") or []) if analysis_for_log else []
            self._last_copilot_clarify = list(analysis_for_log.get("copilot_clarify") or []) if analysis_for_log else []
            self._last_copilot_confidence = (
                float(analysis_for_log.get("copilot_confidence", 0.0) or 0.0) if analysis_for_log else 0.0
            )
            # KC7: deep-track cards
            self._last_copilot_risk = list(analysis_for_log.get("copilot_risk") or []) if analysis_for_log else []
            self._last_copilot_strategy = (analysis_for_log.get("copilot_strategy") or "") if analysis_for_log else ""
            self._last_copilot_emotion = analysis_for_log.get("copilot_emotion") if analysis_for_log else None
            # KC7: append this turn to session memory for next capture (max N turns)
            if out_transcript and len(out_transcript) > 0 and (out_transcript[0] or "").strip():
                turn = (out_transcript[0] or "").strip()[:500]
                self._copilot_session_turns.append(turn)
                if len(self._copilot_session_turns) > self._COPILOT_SESSION_MAX_TURNS:
                    self._copilot_session_turns = self._copilot_session_turns[-self._COPILOT_SESSION_MAX_TURNS :]
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
            with self._copilot_lock:
                self._copilot_session_turns = []  # KC7: new conversation on listen_stop
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

    def _copilot_watcher_loop(self) -> None:
        """KC3: every 1s check elapsed; at 25s emit recording_warning, at 30s auto-release."""
        max_cap = getattr(self._cfg, "copilot_max_capture_seconds", 30.0)
        warn_at = 25.0
        while not self._copilot_watcher_stop.wait(timeout=1.0):
            with self._copilot_lock:
                start = self._copilot_capture_start_time
                if start is None:
                    break
            elapsed = time.monotonic() - start
            if elapsed >= max_cap:
                if self._iface:
                    with contextlib.suppress(Exception):
                        self._iface.CaptureStateChanged("analyzing")
                self._do_capture_release_sync()
                break
            if elapsed >= warn_at:
                with self._copilot_lock:
                    if self._copilot_warning_emitted:
                        continue
                    self._copilot_warning_emitted = True
                if self._iface:
                    with contextlib.suppress(Exception):
                        self._iface.CaptureStateChanged("recording_warning")
        log.debug("daemon.copilot_watcher_stopped")

    def capture_start(self) -> None:
        """KC3: start copilot capture segment (ensure listen, set start marker, start 30s watcher)."""
        self.listen_start()
        pre_roll = getattr(self._cfg, "copilot_pre_roll_seconds", 1.0)
        max_cap = getattr(self._cfg, "copilot_max_capture_seconds", 30.0)
        with self._copilot_lock:
            self._copilot_capture_start_time = time.monotonic()
            self._copilot_warning_emitted = False
            self._last_copilot_stt_ambiguous = False
            # KC6/KC7: clear fast-track and deep-track cards for new recording
            self._last_copilot_answer = []
            self._last_copilot_dos = []
            self._last_copilot_donts = []
            self._last_copilot_clarify = []
            self._last_copilot_confidence = 0.0
            self._last_copilot_risk = []
            self._last_copilot_strategy = ""
            self._last_copilot_emotion = None
        self._copilot_watcher_stop.clear()
        self._copilot_watcher_thread = threading.Thread(target=self._copilot_watcher_loop, daemon=True)
        self._copilot_watcher_thread.start()
        if self._iface:
            with contextlib.suppress(Exception):
                self._iface.CaptureStateChanged("recording")
        log.info("daemon.copilot_capture_started", pre_roll=pre_roll, max_capture_seconds=max_cap)

    def _do_capture_release_sync(self) -> tuple[str, int | None, bool]:
        """KC3: get segment from ring, write to ring file, run analyze; return (status, session_id, stt_ambiguous)."""
        with self._copilot_lock:
            start = self._copilot_capture_start_time
            capture = self._listen_capture
            self._copilot_capture_start_time = None
            self._copilot_warning_emitted = False
        if self._copilot_watcher_thread:
            self._copilot_watcher_stop.set()
            self._copilot_watcher_thread.join(timeout=2.0)
            self._copilot_watcher_thread = None
        if start is None and capture is None:
            return ("error", None, False)
        if capture is None:
            log.warning("daemon.copilot_release_no_capture")
            return ("error", None, False)
        elapsed = time.monotonic() - start if start is not None else 0.0
        pre_roll = getattr(self._cfg, "copilot_pre_roll_seconds", 1.0)
        max_cap = getattr(self._cfg, "copilot_max_capture_seconds", 30.0)
        segment_sec = min(elapsed + pre_roll, max_cap)
        segment_sec = max(1.0, segment_sec)
        try:
            mic, _ = capture.get_chunk(segment_sec)
        except Exception as e:
            log.warning("daemon.copilot_release_get_chunk_failed", error=str(e))
            return ("error", None, False)
        ring_path = Path(self._cfg.get_ring_file_path())
        ring_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp = ring_path.with_suffix(".tmp")
            tmp.write_bytes(mic.tobytes())
            os.replace(tmp, ring_path)
        except Exception as e:
            log.warning("daemon.copilot_release_write_ring_failed", error=str(e))
            return ("error", None, False)
        seconds_for_analyze = max(1, round(segment_sec))
        out_transcript: list[str] = [""]
        copilot_size = getattr(self._cfg, "copilot_stt_model_size", "tiny")
        saved_stt_size = self._model_manager.get_stt_model_size()
        try:
            self._model_manager.swap_stt(copilot_size)
            try:
                text, session_id = self.analyze(seconds_for_analyze, template=None, out_transcript=out_transcript)
            finally:
                self._model_manager.swap_stt(saved_stt_size)
        except Exception as e:
            log.warning("daemon.copilot_release_analyze_failed", error=str(e))
            return ("error", None, False)
        with self._copilot_lock:
            self._last_copilot_transcript = out_transcript[0] if out_transcript else ""
        is_error = bool(
            (text or "").startswith("Ошибка:") or (text or "").startswith("Error:") or (_analyze_result_is_error_daemon(text))
        )
        from voiceforge.i18n import t

        silence_label = t("pipeline.silence")
        stt_ambiguous = silence_label in (text or "") or (len((text or "").strip()) < 20) or (text or "").strip() == ""
        with self._copilot_lock:
            self._last_copilot_stt_ambiguous = stt_ambiguous
        status = "error" if is_error else "ok"
        return (status, session_id, stt_ambiguous)

    def capture_release(self) -> None:
        """KC3: end capture segment, extract audio, run analyze (async from D-Bus: signals emitted by caller)."""
        if self._iface:
            with contextlib.suppress(Exception):
                self._iface.CaptureStateChanged("analyzing")
        result = self._do_capture_release_sync()
        status, session_id, stt_ambiguous = result
        if self._iface:
            try:
                self._iface.AnalysisDone(status)
                if session_id is not None:
                    self._iface.SessionCreated(session_id)
                self._iface.TranscriptUpdated(0)
            except Exception:
                pass
        log.info("daemon.copilot_capture_released", status=status, session_id=session_id, stt_ambiguous=stt_ambiguous)

    def get_copilot_capture_status(self) -> str:
        """KC3–KC7: return JSON for overlay: stt_ambiguous, transcript_snippet, rag_*, fast-track and deep-track cards."""
        with self._copilot_lock:
            ambiguous = self._last_copilot_stt_ambiguous
            snippet = self._last_copilot_transcript
            rag_groundedness = self._last_copilot_rag_groundedness
            rag_citations = self._last_copilot_rag_citations
            rag_conflict_hint = self._last_copilot_rag_conflict_hint
            answer = list(self._last_copilot_answer)
            dos = list(self._last_copilot_dos)
            donts = list(self._last_copilot_donts)
            clarify = list(self._last_copilot_clarify)
            confidence = self._last_copilot_confidence
            risk = list(self._last_copilot_risk)
            strategy = self._last_copilot_strategy
            emotion = self._last_copilot_emotion
        payload: dict[str, Any] = {
            "copilot_mode": getattr(self._cfg, "copilot_mode", "hybrid"),
            "stt_ambiguous": ambiguous,
            "transcript_snippet": snippet,
        }
        if rag_groundedness is not None:
            payload["rag_groundedness"] = rag_groundedness
        if rag_citations:
            payload["rag_citations"] = rag_citations
        if rag_conflict_hint:
            payload["rag_conflict_hint"] = rag_conflict_hint
        if answer:
            payload["copilot_answer"] = answer
        if dos:
            payload["copilot_dos"] = dos
        if donts:
            payload["copilot_donts"] = donts
        if clarify:
            payload["copilot_clarify"] = clarify
        payload["copilot_confidence"] = confidence
        if risk:
            payload["copilot_risk"] = risk
        if strategy:
            payload["copilot_strategy"] = strategy
        if emotion:
            payload["copilot_emotion"] = emotion
        return json.dumps(payload, ensure_ascii=False)

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
                "calendar_auto_listen": getattr(c, "calendar_auto_listen", False),
                "copilot_mode": getattr(c, "copilot_mode", "hybrid"),
                "copilot_max_visible_cards": getattr(c, "copilot_max_visible_cards", 3),
                "copilot_stt_model_size": getattr(c, "copilot_stt_model_size", "tiny"),
                "copilot_pre_roll_seconds": getattr(c, "copilot_pre_roll_seconds", 1.0),
                "copilot_max_capture_seconds": getattr(c, "copilot_max_capture_seconds", 30.0),
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

    def get_rag_stats(self) -> str:
        """KC9: Return JSON with indexed_sources_count and chunks_count for Knowledge UI."""
        try:
            import sqlite3

            db_path = self._cfg.get_rag_db_path()
            if not Path(db_path).is_file():
                return json.dumps({"indexed_sources_count": 0, "chunks_count": 0}, ensure_ascii=False)
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.execute("SELECT COUNT(DISTINCT source) FROM chunks")
                sources = cur.fetchone()[0] or 0
                cur = conn.execute("SELECT COUNT(*) FROM chunks")
                chunks = cur.fetchone()[0] or 0
                return json.dumps(
                    {"indexed_sources_count": sources, "chunks_count": chunks},
                    ensure_ascii=False,
                )
            finally:
                conn.close()
        except Exception as e:
            log.warning("daemon.get_rag_stats_failed", error=str(e))
            return json.dumps({"indexed_sources_count": 0, "chunks_count": 0}, ensure_ascii=False)

    def index_paths(self, paths_json: str) -> str:
        """KC9: Index file/dir paths (JSON array of strings). Runs voiceforge index for each; returns {ok, errors}."""
        try:
            paths = json.loads(paths_json)
            if not isinstance(paths, list):
                return json.dumps({"ok": False, "errors": ["paths must be a JSON array"]}, ensure_ascii=False)
            errors: list[str] = []
            for path_str in paths:
                if not isinstance(path_str, str) or not path_str.strip():
                    continue
                p = Path(path_str.strip()).resolve()
                if not p.exists():
                    errors.append(f"not found: {p}")
                    continue
                try:
                    import subprocess

                    out = subprocess.run(
                        ["voiceforge", "index", str(p)],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if out.returncode != 0 and out.stderr:
                        errors.append(out.stderr.strip()[:200])
                except subprocess.TimeoutExpired:
                    errors.append(f"timeout: {p}")
                except Exception as e:
                    errors.append(f"{p}: {e}")
            return json.dumps({"ok": len(errors) == 0, "errors": errors}, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "errors": [str(e)]}, ensure_ascii=False)
        except Exception as e:
            log.warning("daemon.index_paths_failed", error=str(e))
            return json.dumps({"ok": False, "errors": [str(e)]}, ensure_ascii=False)

    def search_rag(self, query: str, top_k: int = 10) -> str:
        """Return JSON array of RAG search hits: chunk_id, content, source, page, chunk_index, timestamp, score (block 75). Uses cached HybridSearcher (#100)."""
        if not query or not query.strip():
            return "[]"
        try:
            from voiceforge.core.pipeline import _get_cached_searcher

            db_path = self._cfg.get_rag_db_path()
            if not Path(db_path).is_file():
                return "[]"
            searcher = _get_cached_searcher(db_path)
            results = searcher.search(query.strip(), top_k=min(top_k, 25))
            out = [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content,
                    "source": r.source,
                    "page": r.page,
                    "chunk_index": r.chunk_index,
                    "timestamp": r.timestamp,
                    "score": round(r.score, 6),
                }
                for r in results
            ]
            return json.dumps(out, ensure_ascii=False)
        except Exception as e:
            log.warning("daemon.search_rag_failed", error=str(e))
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

    def create_event_from_session(self, session_id: int, calendar_url: str | None = None) -> str:
        """Create CalDAV event from session (block 79, #95). Returns JSON envelope with event_uid or error."""
        from voiceforge.calendar import create_event
        from voiceforge.core.contracts import ErrorCode, build_cli_error_payload, build_cli_success_payload
        from voiceforge.core.transcript_log import TranscriptLog

        try:
            log_db = TranscriptLog()
            try:
                meta = log_db.get_session_meta(session_id)
                if not meta:
                    return json.dumps(
                        build_cli_error_payload(ErrorCode.SESSION_NOT_FOUND.value, f"Session {session_id} not found"),
                        ensure_ascii=False,
                    )
                started_at, ended_at, _ = meta
                detail = log_db.get_session_detail(session_id)
                description = _event_description_from_detail(detail, session_id)
            finally:
                log_db.close()
            summary = f"VoiceForge session {session_id}"
            cal_url = (calendar_url or "").strip() or None
            event_uid, err = create_event(
                start_iso=started_at,
                end_iso=ended_at,
                summary=summary,
                description=description,
                calendar_url=cal_url,
            )
            if err:
                return json.dumps(build_cli_error_payload(ErrorCode.CALDAV_CREATE_EVENT_FAILED.value, err), ensure_ascii=False)
            return json.dumps(build_cli_success_payload({"event_uid": event_uid}), ensure_ascii=False)
        except Exception as e:
            log.warning("daemon.create_event_from_session_failed", session_id=session_id, error=str(e))
            return json.dumps(
                build_cli_error_payload(ErrorCode.CALDAV_CREATE_EVENT_FAILED.value, str(e)),
                ensure_ascii=False,
            )

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

    def _streaming_on_partial(self, text: str) -> None:
        with contextlib.suppress(queue.Full):
            self._streaming_chunk_queue.put_nowait((text, "SPEAKER_??", 0.0, False))
        if text:
            with self._streaming_lock:
                self._streaming_partial = text

    def _streaming_on_final(self, segment: "StreamingSegment") -> None:  # noqa: UP037 — forward ref
        t = getattr(segment, "text", "") or ""
        if not t.strip():
            return
        start = getattr(segment, "start", 0.0)
        end = getattr(segment, "end", 0.0)
        with contextlib.suppress(queue.Full):
            self._streaming_chunk_queue.put_nowait((t, "SPEAKER_??", end, True))
        with self._streaming_lock:
            self._streaming_finals.append({"text": t, "start": start, "end": end})

    def _streaming_loop(self) -> None:
        """Block 10.1: every 1.5s get 2s chunk, transcribe, update _streaming_partial/_streaming_finals.
        KC4: during copilot capture use copilot_stt_model_size (tiny) for latency budget."""
        capture = self._streaming_capture
        get_chunk = getattr(capture, "get_chunk", None) if capture else None
        if not get_chunk:
            return
        try:
            from voiceforge.stt import get_transcriber_for_config
            from voiceforge.stt.streaming import StreamingTranscriber
        except ImportError:
            return
        language_hint = _streaming_language_hint(self._cfg)
        chunk_sec, interval_sec = 2.0, 1.5
        min_samples = int(self._cfg.sample_rate * chunk_sec * 0.5)

        while not self._streaming_stop.is_set():
            if self._streaming_stop.wait(timeout=interval_sec):
                break
            with self._copilot_lock:
                in_copilot = self._copilot_capture_start_time is not None
            size = (
                getattr(self._cfg, "copilot_stt_model_size", "tiny") if in_copilot else getattr(self._cfg, "model_size", "small")
            )
            if size not in self._streaming_transcriber_cache:
                self._streaming_transcriber_cache[size] = get_transcriber_for_config(self._cfg, model_size_override=size)
            transcriber = self._streaming_transcriber_cache[size]
            stream = StreamingTranscriber(
                transcriber,
                sample_rate=self._cfg.sample_rate,
                language=language_hint,
                on_partial=self._streaming_on_partial,
                on_final=self._streaming_on_final,
            )
            try:
                mic, _ = get_chunk(chunk_sec)
                if mic.size >= min_samples:
                    stream.process_chunk(mic, start_offset_sec=0.0)
            except Exception as e:
                log.warning("daemon.streaming_stt.failed", error=str(e))

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
        with self._copilot_lock:
            self._listen_capture = capture
        if self._cfg.streaming_stt:
            with self._streaming_lock:
                self._streaming_partial = ""
                self._streaming_finals.clear()
            self._streaming_stop.clear()
            self._streaming_capture = capture
            self._streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
            self._streaming_thread.start()
        persist_interval = max(1.0, getattr(self._cfg, "ring_persist_interval_sec", 10.0))
        last_persist_at: float = 0.0
        try:
            while not self._listen_stop.wait(timeout=2.0):
                mic, _ = capture.get_chunk(self._cfg.ring_seconds)
                if mic.size > 0:
                    now = time.monotonic()
                    if now - last_persist_at >= persist_interval:
                        ring = Path(ring_path)
                        tmp = ring.with_suffix(".tmp")
                        tmp.write_bytes(mic.tobytes())
                        os.replace(tmp, ring)
                        last_persist_at = now
        finally:
            # Stop streaming thread before capture so it doesn't call get_chunk on stopped device
            if self._streaming_thread:
                self._streaming_stop.set()
                self._streaming_thread.join(timeout=4.0)
                self._streaming_thread = None
            self._streaming_capture = None
            with self._copilot_lock:
                self._listen_capture = None
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
                    _notify_analyze_done(session_id, text or "")
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
    iface._search_rag = daemon.search_rag
    iface._get_settings = daemon.get_settings
    iface._get_indexed_paths = daemon.get_indexed_paths
    iface._get_rag_stats = daemon.get_rag_stats
    iface._index_paths = daemon.index_paths
    iface._get_session_ids_with_action_items = daemon.get_session_ids_with_action_items
    iface._get_upcoming_events = lambda: daemon.get_upcoming_events(48)
    iface._create_event_from_session = lambda session_id, calendar_url: daemon.create_event_from_session(
        session_id, (calendar_url or "").strip() or None
    )
    iface._get_streaming_transcript = daemon.get_streaming_transcript
    iface._swap_model = daemon.swap_model
    iface._ping = lambda: "pong"
    iface._get_analytics = daemon.get_analytics
    iface._get_api_version = daemon.get_api_version
    iface._get_version = daemon.get_version
    iface._get_capabilities = daemon.get_capabilities
    iface._capture_start = daemon.capture_start
    iface._capture_release = daemon.capture_release
    iface._get_copilot_capture_status = daemon.get_copilot_capture_status


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


def _notify_analyze_done(session_id: int | None, text: str) -> None:
    """Send telegram and desktop notifications after analyze (QA3: single place for notify logic)."""
    snippet = (text or "")[:400]
    try:
        from voiceforge.core.telegram_notify import notify_analyze_done

        notify_analyze_done(session_id, snippet)
    except Exception as e:
        log.debug("notify.telegram_failed", error=str(e))
    try:
        from voiceforge.core.desktop_notify import notify_analyze_done as desktop_notify_done

        desktop_notify_done((text or "")[:200])
    except Exception as e:
        log.debug("notify.desktop_failed", error=str(e))


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


def _event_description_from_detail(detail: Any, sid: int) -> str:
    """Build CalDAV event description from session detail (action items). Extracted for #104/S3776."""
    parts: list[str] = []
    if not detail:
        return f"Session {sid} (VoiceForge)"
    _segments, analysis = detail
    if not (analysis and getattr(analysis, "action_items", None)):
        return f"Session {sid} (VoiceForge)"
    for ai in analysis.action_items or []:
        desc = (ai.get("description") or ai.get("text") or "").strip()
        if not desc:
            continue
        assignee = (ai.get("assignee") or "").strip()
        deadline = (ai.get("deadline") or "").strip()
        if assignee or deadline:
            desc = f"{desc} ({', '.join(x for x in [assignee, deadline] if x)})"
        parts.append(f"- {desc}")
    return "\n".join(parts) if parts else f"Session {sid} (VoiceForge)"


def _calendar_try_start_listen(
    daemon: VoiceForgeDaemon, minutes_ahead: int, log_key: str = "calendar_autostart.starting"
) -> None:
    """If an event starts within minutes_ahead, start listen. log_key for log event (QA3: unified)."""
    try:
        from voiceforge.calendar import get_upcoming_events

        events, err = get_upcoming_events(hours_ahead=1)
        if err or not events:
            return
        now = datetime.now(UTC)
        window_end = now + timedelta(minutes=minutes_ahead)
        for ev in events:
            if _event_start_in_window(ev, now, window_end):
                log.info(log_key, summary=ev.get("summary", ""), start=ev.get("start_iso", ""))
                daemon.listen_start()
                return
    except Exception as e:
        log.debug("calendar.try_start_failed", key=log_key, error=str(e))


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
            _calendar_try_start_listen(daemon, minutes_ahead, log_key="calendar_autostart.starting")


def _calendar_auto_listen_try_analyze(daemon: VoiceForgeDaemon, last_processed_end: list[str]) -> None:
    """E11: if an event ended ≥1 min ago (and not yet processed), run analyze on ring tail and log+notify."""
    try:
        from voiceforge.calendar import get_events_ended_at_least_minutes_ago

        events, err = get_events_ended_at_least_minutes_ago(minutes_ago=1, lookback_hours=2)
        if err or not events:
            return
        events_sorted = sorted(events, key=lambda e: e.get("end_iso") or "", reverse=True)
        ev = events_sorted[0]
        end_iso = ev.get("end_iso") or ""
        if end_iso in last_processed_end:
            return
        last_processed_end[:] = [end_iso]
        if len(last_processed_end) > 20:
            last_processed_end.pop(0)
        log.info(
            "calendar_auto_listen.analyzing_after_end",
            summary=ev.get("summary", ""),
            end_iso=end_iso,
        )
        analyze_seconds = 60
        template = getattr(daemon._cfg, "smart_trigger_template", None)
        text, session_id = daemon.analyze(analyze_seconds, template=template)
        if (text or "").startswith("Ошибка:") or (text or "").startswith("Error:"):
            log.warning("calendar_auto_listen.analyze_failed", message=(text or "")[:100])
            return
        _notify_analyze_done(session_id, text or "")
    except Exception as e:
        log.debug("calendar_auto_listen.try_analyze_failed", error=str(e))


def _calendar_auto_listen_loop(daemon: VoiceForgeDaemon) -> None:
    """E11 #134: every 5 min, upcoming ≤2 min → listen_start; ended ≥1 min → auto-analyze + notify."""
    if not getattr(daemon._cfg, "calendar_auto_listen", False):
        return
    interval_sec = 300  # 5 min
    last_processed_end: list[str] = []
    while True:
        try:
            time.sleep(interval_sec)
        except Exception:
            break
        if not daemon.is_listening():
            _calendar_try_start_listen(daemon, minutes_ahead=2, log_key="calendar_auto_listen.starting")
        _calendar_auto_listen_try_analyze(daemon, last_processed_end)


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


async def _watchdog_task(stop_event: asyncio.Event) -> None:
    """E5 #128: send WATCHDOG=1 to systemd every 30s so service is not restarted."""
    while True:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=_WATCHDOG_INTERVAL_SEC)
        if stop_event.is_set():
            return
        _sd_notify("WATCHDOG=1")


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
        watchdog_task = asyncio.create_task(_watchdog_task(stop_event))
        try:
            # E5 #128: Type=notify — tell systemd we are ready after D-Bus is up
            _sd_notify("READY=1")
            await stop_event.wait()
        finally:
            watchdog_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog_task
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

    if getattr(daemon._cfg, "calendar_auto_listen", False):
        _calendar_thread = threading.Thread(target=_calendar_auto_listen_loop, args=(daemon,), daemon=True)
        _calendar_thread.start()
        log.info("daemon.calendar_auto_listen_enabled", interval_sec=300)
    elif getattr(daemon._cfg, "calendar_autostart_enabled", False):
        _calendar_thread = threading.Thread(target=_calendar_autostart_loop, args=(daemon,), daemon=True)
        _calendar_thread.start()
        log.info("daemon.calendar_autostart_enabled", minutes=getattr(daemon._cfg, "calendar_autostart_minutes", 5))

    log.info("daemon.starting", pid=os.getpid(), pid_file=str(pid_path))
    stop_event = asyncio.Event()
    loop_holder: list[asyncio.AbstractEventLoop | None] = [None]

    def on_sigterm(*args: object) -> None:
        log.info("daemon.shutting_down_gracefully")
        daemon.listen_stop()  # flush ring buffer, stop capture
        # E5 #128: clean up ring.raw on graceful shutdown (keep on crash for recovery)
        try:
            ring_path = Path(daemon._cfg.get_ring_file_path())
            if ring_path.is_file():
                ring_path.unlink()
                log.debug("daemon.ring_cleaned_up", path=str(ring_path))
        except Exception as e:
            log.debug("daemon.ring_cleanup_skipped", error=str(e))
        pid_path.unlink(missing_ok=True)
        loop = loop_holder[0]
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGTERM, on_sigterm)
    signal.signal(signal.SIGINT, on_sigterm)
    pid_path.write_text(str(os.getpid()))
    atexit.register(lambda: pid_path.unlink(missing_ok=True))

    _run_daemon_loop(iface, daemon, stop_event, pid_path, loop_holder)
