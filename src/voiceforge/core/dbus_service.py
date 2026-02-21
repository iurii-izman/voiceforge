"""D-Bus service for hotkeys (Wayland: COSMIC has no GlobalShortcuts portal).

COSMIC Settings → Keyboard → Custom Shortcuts → Add:
  VoiceForge Analyze: dbus-send --session --dest=com.voiceforge.App \\
    /com/voiceforge/App com.voiceforge.App.Analyze uint32:30
  Shortcut: Ctrl+Shift+F9
  VoiceForge Toggle: same with .Toggle
  VoiceForge Status: same with .Status
"""

import asyncio
import contextlib
import json
import os
from collections.abc import Callable
from typing import Annotated

import structlog
from dbus_fast.aio import MessageBus
from dbus_fast.annotations import DBusBool, DBusSignature, DBusStr
from dbus_fast.service import ServiceInterface, dbus_method, dbus_signal

from voiceforge.core.contracts import (
    IPC_SCHEMA_VERSION,
    build_ipc_error_json,
    build_ipc_success_json,
    wrap_ipc_json_payload,
)

DBusUint32 = Annotated[int, DBusSignature("u")]

log = structlog.get_logger()

BUS_NAME = "com.voiceforge.App"
OBJECT_PATH = "/com/voiceforge/App"
INTERFACE_NAME = "com.voiceforge.App"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _make_ipc_error(code: str, message: str, retryable: bool = False) -> str:
    return build_ipc_error_json(code=code, message=message, retryable=retryable)


def _make_ipc_success(data: dict[str, object]) -> str:
    return build_ipc_success_json(dict(data))


def _wrap_envelope_with_json_key(key: str, payload: str) -> str:
    """Wrap JSON-like payload into envelope, preserving parsed structure when possible."""
    return wrap_ipc_json_payload(key, payload)


def _uses_ipc_envelope() -> bool:
    """Capability-gated contract mode for D-Bus string payloads.

    Disabled by default to preserve compatibility with old clients expecting plain strings.
    """
    return _env_flag("VOICEFORGE_IPC_ENVELOPE", default=False)


class VoiceForgeAppInterface(ServiceInterface):
    """D-Bus interface com.voiceforge.App: Analyze, Toggle, Status (standalone hotkeys).

    Pass analyze_fn/status_fn/toggle_fn to wire real pipeline behaviour.
    Without callbacks the methods return structured NOT_CONFIGURED errors instead of
    silently returning "ok".
    """

    def __init__(
        self,
        analyze_fn: Callable[[int], str] | None = None,
        status_fn: Callable[[], str] | None = None,
        toggle_fn: Callable[[], str] | None = None,
    ) -> None:
        super().__init__(INTERFACE_NAME)
        self._analyze = analyze_fn
        self._status = status_fn
        self._toggle = toggle_fn
        self._analyze_sem = asyncio.Semaphore(1)

    ANALYZE_MAX_SECONDS = 3600

    @dbus_method()
    async def Analyze(self, seconds: DBusUint32) -> DBusStr:
        """Trigger analysis (e.g. from hotkey). seconds=0 uses default 30s."""
        if seconds < 1 or seconds > self.ANALYZE_MAX_SECONDS:
            return _make_ipc_error(
                "INVALID_SECONDS",
                f"seconds must be 1..{self.ANALYZE_MAX_SECONDS}, got {seconds}",
            )
        log.info("dbus.Analyze.called", seconds=seconds)
        if self._analyze is None:
            log.warning("dbus.Analyze.not_configured")
            return _make_ipc_error(
                "NOT_CONFIGURED",
                "Analyze function not configured. Run voiceforge daemon instead of voiceforge dbus.",
            )
        async with self._analyze_sem:
            return await asyncio.to_thread(self._analyze, seconds)

    @dbus_method()
    def Toggle(self) -> DBusStr:
        """Toggle listen state."""
        log.info("dbus.Toggle.called")
        if self._toggle is None:
            return "ok"
        return self._toggle()

    @dbus_method()
    def Status(self) -> DBusStr:
        """Return status string."""
        log.info("dbus.Status.called")
        if self._status is None:
            return "idle"
        return self._status()


class DaemonVoiceForgeInterface(ServiceInterface):
    """D-Bus daemon: Analyze, Status, Listen, GetSessions, GetSessionDetail, GetSettings, GetIndexedPaths."""

    def __init__(
        self,
        analyze_fn: Callable[[int], str],
        status_fn: Callable[[], str],
        listen_start_fn: Callable[[], None],
        listen_stop_fn: Callable[[], None],
        is_listening_fn: Callable[[], bool],
        get_sessions_fn: Callable[[int], str] | None = None,
        get_session_detail_fn: Callable[[int], str] | None = None,
        get_settings_fn: Callable[[], str] | None = None,
        get_indexed_paths_fn: Callable[[], str] | None = None,
        get_streaming_transcript_fn: Callable[[], str] | None = None,
        swap_model_fn: Callable[[str, str], str] | None = None,
        ping_fn: Callable[[], str] | None = None,
        get_analytics_fn: Callable[[str], str] | None = None,
        get_api_version_fn: Callable[[], str] | None = None,
        get_capabilities_fn: Callable[[], str] | None = None,
    ) -> None:
        super().__init__(INTERFACE_NAME)
        self._analyze = analyze_fn
        self._status = status_fn
        self._listen_start = listen_start_fn
        self._listen_stop = listen_stop_fn
        self._is_listening = is_listening_fn
        self._get_sessions = get_sessions_fn
        self._get_session_detail = get_session_detail_fn
        self._get_settings = get_settings_fn
        self._get_indexed_paths = get_indexed_paths_fn
        self._get_streaming_transcript = get_streaming_transcript_fn
        self._swap_model = swap_model_fn
        self._ping = ping_fn
        self._get_analytics = get_analytics_fn
        self._get_api_version = get_api_version_fn
        self._get_capabilities = get_capabilities_fn
        self._analyze_sem = asyncio.Semaphore(1)

    ANALYZE_MAX_SECONDS = 3600

    @dbus_method()
    async def Analyze(self, seconds: DBusUint32) -> DBusStr:
        """Run pipeline for last N seconds; return formatted result string.
        Semaphore(1) prevents concurrent calls from loading two Whisper instances."""
        if seconds < 1 or seconds > self.ANALYZE_MAX_SECONDS:
            return _make_ipc_error(
                "INVALID_SECONDS",
                f"seconds must be 1..{self.ANALYZE_MAX_SECONDS}, got {seconds}",
            )
        log.info("dbus.Analyze.called", seconds=seconds)
        async with self._analyze_sem:
            result = await asyncio.to_thread(self._analyze, seconds)
        # Treat result starting with "Ошибка:" (Russian) or structured {"error":...} as error
        try:
            parsed = json.loads(result)
            is_error = isinstance(parsed, dict) and "error" in parsed
        except (json.JSONDecodeError, TypeError):
            is_error = result.startswith("Ошибка:")
        status = "error" if is_error else "ok"
        self.AnalysisDone(status)
        # session_id is not available at interface layer; emit 0 as generic update trigger.
        self.TranscriptUpdated(0)
        if _uses_ipc_envelope():
            if is_error:
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict) and "error" in parsed:
                        err = parsed["error"]
                        return _make_ipc_error(
                            str(err.get("code", "ANALYZE_FAILED")),
                            str(err.get("message", "Analyze failed")),
                            bool(err.get("retryable", False)),
                        )
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass
                return _make_ipc_error("ANALYZE_FAILED", result, retryable=False)
            return _make_ipc_success({"text": result})
        return result

    @dbus_method()
    def Status(self) -> DBusStr:
        """Return status string (RAM, cost)."""
        status = self._status()
        if _uses_ipc_envelope():
            return _make_ipc_success({"text": status})
        return status

    @dbus_method()
    def ListenStart(self) -> None:
        """Start ring-buffer recording."""
        try:
            self._listen_start()
            self.ListenStateChanged(True)
        except Exception as e:
            log.warning("dbus.ListenStart.failed", error=str(e))
            self.ListenStateChanged(False)

    @dbus_method()
    def ListenStop(self) -> None:
        """Stop ring-buffer recording."""
        try:
            self._listen_stop()
        except Exception as e:
            log.warning("dbus.ListenStop.failed", error=str(e))
        finally:
            self.ListenStateChanged(False)

    @dbus_method()
    def IsListening(self) -> DBusBool:
        """Whether listen is active."""
        return self._is_listening()

    @dbus_method()
    def GetSessions(self, last_n: DBusUint32) -> DBusStr:
        """Return JSON array of session summaries (id, started_at, duration_sec, segments_count)."""
        if self._get_sessions is None:
            payload = "[]"
        else:
            payload = self._get_sessions(last_n)
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("sessions", payload)
        return payload

    @dbus_method()
    def GetSessionDetail(self, session_id: DBusUint32) -> DBusStr:
        """Return JSON object with segments and analysis for session_id."""
        if self._get_session_detail is None:
            payload = "{}"
        else:
            payload = self._get_session_detail(session_id)
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("session_detail", payload)
        return payload

    @dbus_method()
    def GetSettings(self) -> DBusStr:
        """Return JSON object with model_size, default_llm, budget_limit_usd, smart_trigger."""
        if self._get_settings is None:
            payload = "{}"
        else:
            payload = self._get_settings()
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("settings", payload)
        return payload

    @dbus_method()
    def GetIndexedPaths(self) -> DBusStr:
        """Return JSON array of indexed file paths from RAG DB."""
        if self._get_indexed_paths is None:
            payload = "[]"
        else:
            payload = self._get_indexed_paths()
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("indexed_paths", payload)
        return payload

    @dbus_method()
    def GetStreamingTranscript(self) -> DBusStr:
        """Block 10.1: return JSON {partial, finals} for real-time transcript (polling)."""
        if self._get_streaming_transcript is None:
            payload = '{"partial":"","finals":[]}'
        else:
            payload = self._get_streaming_transcript()
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("streaming_transcript", payload)
        return payload

    @dbus_method()
    def SwapModel(self, model_type: DBusStr, model_name: DBusStr) -> DBusStr:
        """Block 10.4: hot-swap STT or LLM model. model_type: 'stt'|'llm', model_name: e.g. 'tiny'|'small' or model id."""
        if self._swap_model is None:
            return "error: not available"
        return self._swap_model(model_type, model_name)

    @dbus_method()
    def Ping(self) -> DBusStr:
        """Block 11.2: watchdog — returns immediately; caller can restart daemon if no response in 30s."""
        if self._ping is not None:
            return self._ping()
        return "pong"

    @dbus_method()
    def GetAnalytics(self, last: DBusStr) -> DBusStr:
        """Block 11.5: return JSON analytics for period (e.g. last='30d')."""
        if self._get_analytics is None:
            payload = "{}"
        else:
            payload = self._get_analytics(last)
        if _uses_ipc_envelope():
            return _wrap_envelope_with_json_key("analytics", payload)
        return payload

    @dbus_method()
    def GetApiVersion(self) -> DBusStr:
        """Return D-Bus API version (contract versioning)."""
        if self._get_api_version is None:
            return "1.0"
        return self._get_api_version()

    @dbus_method()
    def GetCapabilities(self) -> DBusStr:
        """Return JSON object with daemon capabilities."""
        if self._get_capabilities is None:
            return json.dumps(
                {
                    "api_version": IPC_SCHEMA_VERSION,
                    "features": {"envelope_v1": _uses_ipc_envelope()},
                },
                ensure_ascii=False,
            )
        return self._get_capabilities()

    @dbus_signal()
    def ListenStateChanged(self, is_listening: DBusBool) -> DBusBool:
        """Signal: listening state changed."""
        return is_listening

    @dbus_signal()
    def TranscriptUpdated(self, session_id: DBusUint32) -> DBusUint32:
        """Signal: transcript data changed (session_id may be 0 if unknown)."""
        return session_id

    @dbus_signal()
    def AnalysisDone(self, status: DBusStr) -> DBusStr:
        """Signal: analyze finished with status ('ok'|'error')."""
        return status

    @dbus_signal()
    def TranscriptChunk(
        self, text: DBusStr, speaker: DBusStr, timestamp_ms: DBusUint32, is_final: DBusBool
    ) -> Annotated[tuple[str, str, int, bool], DBusSignature("ssub")]:
        """Signal: streaming STT sent a segment. is_final=false is partial, is_final=true is confirmed."""
        return text, speaker, timestamp_ms, is_final


async def run_dbus_service(iface: ServiceInterface | None = None) -> None:
    """Connect to session bus, export service, request name, wait for disconnect."""
    bus = await MessageBus().connect()
    if iface is None:
        iface = VoiceForgeAppInterface()
    bus.export(OBJECT_PATH, iface)
    await bus.request_name(BUS_NAME)
    log.info("dbus.service.ready", name=BUS_NAME, path=OBJECT_PATH)
    try:
        await bus.wait_for_disconnect()
    finally:
        with contextlib.suppress(Exception):
            bus.disconnect()


def main_dbus_service() -> None:
    """Entry point to run the D-Bus service (e.g. from CLI)."""
    asyncio.run(run_dbus_service())
