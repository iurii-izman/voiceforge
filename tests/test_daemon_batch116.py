"""Behavioral coverage batch for core.daemon (#116)."""

from __future__ import annotations

import asyncio
import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from conftest import raise_when_called

from voiceforge.core.daemon import (
    VoiceForgeDaemon,
    _calendar_try_start_listen,
    _cancel_purge_then_service_reraise,
    _run_one_retention_purge,
    _sd_notify,
    _watchdog_task,
)
from voiceforge.core.dbus_service import DaemonVoiceForgeInterface


def _make_daemon(
    *,
    iface: DaemonVoiceForgeInterface | None = None,
    settings_overrides: dict[str, object] | None = None,
) -> VoiceForgeDaemon:
    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.stt_backend = "local"
    cfg.default_llm = "anthropic/claude-haiku"
    cfg.budget_limit_usd = 10.0
    cfg.smart_trigger = False
    cfg.sample_rate = 16000
    cfg.streaming_stt = False
    cfg.pii_mode = "ON"
    cfg.language = "auto"
    cfg.calendar_autostart_enabled = False
    cfg.calendar_autostart_minutes = 5
    cfg.ring_seconds = 30
    cfg.monitor_source = "monitor"
    cfg.ring_persist_interval_sec = 1.0
    cfg.analyze_timeout_sec = 30.0
    cfg.retention_days = 0
    cfg.get_rag_db_path = MagicMock(return_value="/nonexistent/rag.db")
    cfg.get_ring_file_path = MagicMock(return_value="/tmp/voiceforge-ring.raw")
    if settings_overrides:
        for key, value in settings_overrides.items():
            setattr(cfg, key, value)
    with (
        patch("voiceforge.core.daemon.Settings", return_value=cfg),
        patch("voiceforge.core.daemon.ModelManager", return_value=MagicMock()),
        patch("voiceforge.core.daemon.set_model_manager"),
    ):
        return VoiceForgeDaemon(iface=iface)


class _FakeThread:
    def __init__(self, target=None, daemon=False, args=()) -> None:
        self.target = target
        self.daemon = daemon
        self.args = args
        self.started = False
        self.join_calls: list[float | None] = []

    def start(self) -> None:
        self.started = True

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(timeout)


def test_daemon_analyze_success_logs_session_and_emits_chunks(monkeypatch) -> None:
    chunks: list[str] = []
    iface = SimpleNamespace(StreamingAnalysisChunk=lambda chunk: chunks.append(chunk))
    daemon = _make_daemon(iface=iface)

    def fake_run_analyze_pipeline(seconds, template=None, stream_callback=None):
        assert template == "standup"
        stream_callback("part-1")
        stream_callback(None)
        return (
            "analysis text",
            [SimpleNamespace(text="segment")],
            {
                "model": "anthropic/claude-haiku",
                "questions": ["Q1"],
                "answers": ["A1"],
                "recommendations": ["R1"],
                "action_items": [{"description": "Ship"}],
                "cost_usd": 0.12,
                "template": template,
            },
        )

    logged: dict[str, object] = {}

    class FakeLogDb:
        def log_session(self, **kwargs):
            logged.update(kwargs)
            return 42

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr("voiceforge.main.run_analyze_pipeline", fake_run_analyze_pipeline)
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)

    text, session_id = daemon.analyze(30, template="standup")

    assert text == "analysis text"
    assert session_id == 42
    assert chunks == ["part-1", ""]
    assert logged["duration_sec"] == pytest.approx(30.0)
    assert logged["template"] == "standup"


def test_daemon_analyze_returns_text_when_log_session_fails(monkeypatch) -> None:
    daemon = _make_daemon()
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr("voiceforge.main.run_analyze_pipeline", lambda *args, **kwargs: ("ok", ["s"], {"model": "m"}))
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", raise_when_called(RuntimeError("db down")))
    monkeypatch.setattr("voiceforge.core.daemon.log.warning", lambda *args, **kwargs: warnings.append((args, kwargs)))

    text, session_id = daemon.analyze(10)

    assert text == "ok"
    assert session_id is None
    assert warnings and warnings[0][0][0] == "daemon.analyze.log_failed"


def test_daemon_listen_start_and_stop_manage_threads(monkeypatch) -> None:
    created_threads: list[_FakeThread] = []

    def fake_thread(*args, **kwargs):
        thread = _FakeThread(*args, **kwargs)
        created_threads.append(thread)
        return thread

    daemon = _make_daemon(settings_overrides={"smart_trigger": True})
    monkeypatch.setattr("voiceforge.core.daemon.threading.Thread", fake_thread)

    daemon.listen_start()

    assert daemon.is_listening() is True
    assert len(created_threads) == 3
    assert all(thread.started for thread in created_threads)

    daemon._streaming_thread = _FakeThread()
    daemon.listen_stop()

    assert daemon.is_listening() is False
    assert daemon._listen_thread is None
    assert daemon._trigger_thread is None
    assert daemon._dbus_emitter_thread is None
    assert daemon._streaming_thread is None
    assert daemon._streaming_capture is None


def test_daemon_dbus_streaming_emitter_loop_handles_queue_item(monkeypatch) -> None:
    emitted: list[tuple[str, str, int, bool]] = []
    daemon = _make_daemon(
        iface=SimpleNamespace(
            TranscriptChunk=lambda *args: emitted.append(args) or daemon._dbus_emitter_stop.set()  # type: ignore[name-defined]
        )
    )
    daemon._streaming_chunk_queue.put(("hello", "SPEAKER_01", 1.25, True))

    daemon._dbus_streaming_emitter_loop()

    assert emitted == [("hello", "SPEAKER_01", 1250, True)]


def test_daemon_dbus_streaming_emitter_loop_logs_errors(monkeypatch) -> None:
    daemon = _make_daemon(iface=SimpleNamespace(TranscriptChunk=lambda *args: None))

    def fake_get(timeout):
        daemon._dbus_emitter_stop.set()
        raise RuntimeError("queue boom")

    monkeypatch.setattr(daemon._streaming_chunk_queue, "get", fake_get)
    errors: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr("voiceforge.core.daemon.log.error", lambda *args, **kwargs: errors.append((args, kwargs)))

    daemon._dbus_streaming_emitter_loop()

    assert errors and errors[0][0][0] == "dbus.emitter.failed"


def test_daemon_dbus_streaming_emitter_loop_without_iface_warns(monkeypatch) -> None:
    daemon = _make_daemon(iface=None)
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr("voiceforge.core.daemon.log.warning", lambda *args, **kwargs: warnings.append((args, kwargs)))

    daemon._dbus_streaming_emitter_loop()

    assert warnings and warnings[0][0][0] == "dbus.emitter.no_interface"


def test_daemon_get_session_detail_and_search_transcripts_success(monkeypatch) -> None:
    class FakeLogDb:
        def get_session_detail(self, session_id):
            return (
                [SimpleNamespace(start_sec=0.0, end_sec=1.0, speaker="S1", text="hello")],
                SimpleNamespace(
                    model="m",
                    questions=["q"],
                    answers=["a"],
                    recommendations=["r"],
                    action_items=[{"description": "ship"}],
                    cost_usd=0.1,
                ),
            )

        def search_transcripts(self, query, limit):
            return [(3, "text", 1.0, 2.0, "snippet")]

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)
    daemon = _make_daemon()

    detail = json.loads(daemon.get_session_detail(3))
    hits = json.loads(daemon.search_transcripts("hello", limit=99))

    assert detail["segments"][0]["speaker"] == "S1"
    assert detail["analysis"]["action_items"] == [{"description": "ship"}]
    assert hits == [{"session_id": 3, "text": "text", "start_sec": 1.0, "end_sec": 2.0, "snippet": "snippet"}]


def test_daemon_search_transcripts_failure_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", raise_when_called(RuntimeError("fts down")))
    daemon = _make_daemon()
    assert daemon.search_transcripts("hello") == "[]"


def test_daemon_search_rag_get_ids_and_upcoming_events_success(monkeypatch, tmp_path) -> None:
    rag_db = tmp_path / "rag.db"
    rag_db.write_text("placeholder")
    daemon = _make_daemon(settings_overrides={"get_rag_db_path": lambda: str(rag_db)})

    search_results = [
        SimpleNamespace(chunk_id=1, content="chunk", source="/tmp/doc", page=2, chunk_index=0, timestamp="t", score=0.9876543)
    ]

    class FakeLogDb:
        def get_session_ids_with_action_items(self):
            return [1, 3, 5]

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr(
        "voiceforge.core.pipeline._get_cached_searcher",
        lambda db_path: SimpleNamespace(search=lambda query, top_k: search_results),
    )
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)
    monkeypatch.setattr("voiceforge.calendar.get_upcoming_events", lambda hours_ahead=48: ([{"summary": "Demo"}], None))

    rag_hits = json.loads(daemon.search_rag(" roadmap ", top_k=50))
    ids = json.loads(daemon.get_session_ids_with_action_items())
    events = json.loads(daemon.get_upcoming_events(24))

    assert rag_hits[0]["score"] == pytest.approx(0.987654)
    assert ids == [1, 3, 5]
    assert events == [{"summary": "Demo"}]


def test_daemon_upcoming_events_skip_and_create_event_paths(monkeypatch) -> None:
    class FakeLogDb:
        def get_session_meta(self, session_id):
            return ("2026-03-08T10:00:00+00:00", "2026-03-08T11:00:00+00:00", 3600)

        def get_session_detail(self, session_id):
            return ([], SimpleNamespace(action_items=[{"description": "Ship release"}]))

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    monkeypatch.setattr("voiceforge.calendar.get_upcoming_events", lambda hours_ahead=48: ([], "calendar disabled"))
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)
    monkeypatch.setattr("voiceforge.calendar.create_event", lambda **kwargs: ("uid-123", None))
    daemon = _make_daemon()

    assert daemon.get_upcoming_events() == "[]"
    success = json.loads(daemon.create_event_from_session(5, " https://calendar.example "))
    assert success["ok"] is True
    assert success["data"]["event_uid"] == "uid-123"

    monkeypatch.setattr("voiceforge.calendar.create_event", lambda **kwargs: (None, "caldav failed"))
    error = json.loads(daemon.create_event_from_session(5))
    assert error["error"]["code"] == "VF023"


def test_daemon_create_event_from_session_not_found_and_exception(monkeypatch) -> None:
    class MissingLogDb:
        def get_session_meta(self, session_id):
            return None

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    daemon = _make_daemon()
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", MissingLogDb)
    not_found = json.loads(daemon.create_event_from_session(99))
    assert not_found["error"]["code"] == "VF001"

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", raise_when_called(RuntimeError("db broken")))
    failure = json.loads(daemon.create_event_from_session(99))
    assert failure["error"]["code"] == "VF023"


def test_daemon_streaming_partial_and_final_update_state(monkeypatch) -> None:
    daemon = _make_daemon()

    daemon._streaming_on_partial("partial text")
    daemon._streaming_on_partial("")
    daemon._streaming_on_final(SimpleNamespace(text="final text", start=1.0, end=2.5))
    daemon._streaming_on_final(SimpleNamespace(text="   ", start=0.0, end=0.0))

    data = json.loads(daemon.get_streaming_transcript())
    assert data["partial"] == "partial text"
    assert data["finals"] == [{"text": "final text", "start": 1.0, "end": 2.5}]


def test_daemon_streaming_loop_short_circuits_without_capture_or_imports(monkeypatch) -> None:
    daemon = _make_daemon()
    daemon._streaming_capture = None
    daemon._streaming_loop()

    daemon._streaming_capture = SimpleNamespace(get_chunk=lambda seconds: (None, None))
    with patch.dict(sys.modules, {"voiceforge.stt": None, "voiceforge.stt.streaming": None}):
        daemon._streaming_loop()


def test_daemon_streaming_loop_processes_chunk_and_logs_failure(monkeypatch) -> None:
    processed: list[tuple[object, float]] = []
    warnings: list[tuple[tuple[object, ...], dict[str, object]]] = []
    daemon = _make_daemon(settings_overrides={"sample_rate": 4})
    daemon._streaming_capture = SimpleNamespace(
        calls=0,
        get_chunk=lambda seconds: (SimpleNamespace(size=4), None),
    )

    class FakeStop:
        def __init__(self) -> None:
            self.calls = 0

        def is_set(self) -> bool:
            return self.calls > 0

        def wait(self, timeout=None) -> bool:
            self.calls += 1
            return self.calls > 1

    daemon._streaming_stop = FakeStop()
    fake_stream = SimpleNamespace(process_chunk=lambda mic, start_offset_sec=0.0: processed.append((mic, start_offset_sec)))
    monkeypatch.setattr("voiceforge.core.daemon._streaming_language_hint", lambda cfg: "en")
    monkeypatch.setattr("voiceforge.core.daemon.log.warning", lambda *args, **kwargs: warnings.append((args, kwargs)))

    with patch.dict(
        sys.modules,
        {
            "voiceforge.stt": SimpleNamespace(get_transcriber_for_config=lambda cfg: "tx"),
            "voiceforge.stt.streaming": SimpleNamespace(StreamingTranscriber=lambda *args, **kwargs: fake_stream),
        },
    ):
        daemon._streaming_loop()

    assert len(processed) == 1
    assert processed[0][0].size == 4
    assert processed[0][1] == pytest.approx(0.0)

    daemon._streaming_capture = SimpleNamespace(get_chunk=raise_when_called(RuntimeError("capture fail")))
    daemon._streaming_stop = FakeStop()
    with patch.dict(
        sys.modules,
        {
            "voiceforge.stt": SimpleNamespace(get_transcriber_for_config=lambda cfg: "tx"),
            "voiceforge.stt.streaming": SimpleNamespace(StreamingTranscriber=lambda *args, **kwargs: fake_stream),
        },
    ):
        daemon._streaming_loop()
    assert warnings and warnings[-1][0][0] == "daemon.streaming_stt.failed"


def test_daemon_listen_loop_handles_import_error_and_persists_ring(monkeypatch, tmp_path) -> None:
    daemon = _make_daemon(
        settings_overrides={
            "get_ring_file_path": lambda: str(tmp_path / "ring.raw"),
            "ring_seconds": 4,
            "ring_persist_interval_sec": 1.0,
            "streaming_stt": False,
        }
    )
    daemon._listen_active = True
    with patch.dict(sys.modules, {"voiceforge.audio.capture": None}):
        daemon._listen_loop()
    assert daemon.is_listening() is False

    class FakeMic:
        size = 4

        @staticmethod
        def tobytes() -> bytes:
            return b"abcd"

    class FakeCapture:
        def __init__(self, **kwargs) -> None:
            self.started = False
            self.stopped = False

        def start(self) -> None:
            self.started = True

        def get_chunk(self, seconds):
            return (FakeMic(), None)

        def stop(self) -> None:
            self.stopped = True

    class FakeStop:
        def __init__(self) -> None:
            self.calls = 0

        def wait(self, timeout=None) -> bool:
            self.calls += 1
            return self.calls > 1

        def set(self) -> None:
            self.calls = 2

    daemon = _make_daemon(
        settings_overrides={
            "get_ring_file_path": lambda: str(tmp_path / "ring.raw"),
            "ring_seconds": 4,
            "ring_persist_interval_sec": 1.0,
            "streaming_stt": False,
        }
    )
    daemon._listen_stop = FakeStop()
    monkeypatch.setattr("voiceforge.core.daemon.time.monotonic", lambda: 10.0)
    with patch.dict(sys.modules, {"voiceforge.audio.capture": SimpleNamespace(AudioCapture=FakeCapture)}):
        daemon._listen_loop()

    assert (tmp_path / "ring.raw").read_bytes() == b"abcd"


@pytest.mark.asyncio
async def test_run_one_retention_purge_and_cancel_helper(monkeypatch) -> None:
    purged: list[object] = []

    class FakeLogDb:
        def purge_before(self, cutoff):
            purged.append(cutoff)
            return 3

        def close(self) -> None:
            # No-op for test fake (S1186).
            pass

    daemon = _make_daemon(settings_overrides={"retention_days": 7})
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", FakeLogDb)

    count, cutoff = await _run_one_retention_purge(daemon)
    assert count == 3
    assert cutoff is not None
    assert purged

    class _Task:
        def __init__(self, *, raises_cancel: bool) -> None:
            self.raises_cancel = raises_cancel
            self.cancelled = False

        def cancel(self) -> None:
            self.cancelled = True

        def __await__(self):
            async def _inner():
                if self.raises_cancel:
                    raise asyncio.CancelledError()
                return None

            return _inner().__await__()

    purge_task = _Task(raises_cancel=True)
    service_task = _Task(raises_cancel=True)
    with pytest.raises(asyncio.CancelledError):
        await _cancel_purge_then_service_reraise(purge_task, service_task)
    assert purge_task.cancelled is True
    assert service_task.cancelled is True


def test_calendar_autostart_try_start_starts_only_for_window(monkeypatch) -> None:
    import datetime as dt

    daemon = _make_daemon()
    started: list[int] = []
    daemon.listen_start = lambda: started.append(1)
    monkeypatch.setattr(
        "voiceforge.calendar.get_upcoming_events",
        lambda hours_ahead=1: ([{"start_iso": "2026-03-08T10:10:00+00:00"}], None),
    )
    fake_now = SimpleNamespace(
        now=lambda tz=None: dt.datetime(2026, 3, 8, 10, 0, tzinfo=tz),
        fromisoformat=dt.datetime.fromisoformat,
    )
    monkeypatch.setattr("voiceforge.core.daemon.datetime", fake_now)

    _calendar_try_start_listen(daemon, 15)
    assert started == [1]

    monkeypatch.setattr("voiceforge.calendar.get_upcoming_events", lambda hours_ahead=1: ([], None))
    _calendar_try_start_listen(daemon, 15)
    assert started == [1]


# --- E5 #128: Daemon hardening (watchdog, shutdown, ring cleanup) ---


def test_sd_notify_no_socket_returns_false(monkeypatch) -> None:
    """Without NOTIFY_SOCKET, _sd_notify does nothing and returns False."""
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    assert _sd_notify("READY=1") is False
    assert _sd_notify("WATCHDOG=1") is False


def test_sd_notify_with_invalid_socket_returns_false(monkeypatch) -> None:
    """With NOTIFY_SOCKET set to non-existent path, _sd_notify fails and returns False."""
    monkeypatch.setenv("NOTIFY_SOCKET", "/nonexistent/notify.sock")
    assert _sd_notify("WATCHDOG=1") is False


@pytest.mark.asyncio
async def test_watchdog_task_stops_on_event() -> None:
    """_watchdog_task runs until stop_event is set."""
    stop = asyncio.Event()
    task = asyncio.create_task(_watchdog_task(stop))
    await asyncio.sleep(0.05)
    stop.set()
    await task  # completes normally when stop is set
