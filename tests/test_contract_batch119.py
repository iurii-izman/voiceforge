"""Focused anti-drift guards for web/API/desktop contract batch #119."""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass

import pytest

from voiceforge.cli.history_helpers import session_not_found_message
from voiceforge.core.dbus_service import DaemonVoiceForgeInterface
from voiceforge.web import server_async


@dataclass
class _FakeSegment:
    start_sec: float
    end_sec: float
    speaker: str
    text: str


@dataclass
class _FakeAnalysis:
    model: str
    questions: list[str]
    answers: list[str]
    recommendations: list[str]
    action_items: list[dict[str, str]]
    cost_usd: float
    template: str | None = None


class _FakeTranscriptLogSessionDetail:
    def get_session_detail(self, session_id: int):
        if session_id == 7:
            return (
                [_FakeSegment(0.0, 2.0, "Speaker 1", "hello")],
                _FakeAnalysis(
                    model="test-model",
                    questions=["Q1"],
                    answers=["A1"],
                    recommendations=["R1"],
                    action_items=[{"description": "Ship it", "status": "open"}],
                    cost_usd=0.25,
                    template="standup",
                ),
            )
        return None

    def close(self) -> None:
        # No-op for test fake (S1186).
        pass


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _iface() -> DaemonVoiceForgeInterface:
    return DaemonVoiceForgeInterface(
        analyze_fn=lambda seconds, template=None: f"ok-{seconds}-{template or 'default'}",
        status_fn=lambda: "idle",
        listen_start_fn=lambda: None,
        listen_stop_fn=lambda: None,
        is_listening_fn=lambda: False,
        optional={
            "get_settings_fn": lambda: json.dumps(
                {
                    "model_size": "small",
                    "default_llm": "anthropic/claude-haiku-4-5",
                    "budget_limit_usd": 75.0,
                    "sample_rate": 16000,
                    "streaming_stt": False,
                    "pii_mode": "ON",
                    "privacy_mode": "ON",
                }
            ),
            "get_session_detail_fn": lambda session_id: json.dumps(
                {
                    "session_id": session_id,
                    "segments": [{"start_sec": 0.0, "end_sec": 1.0, "speaker": "A", "text": "Hi"}],
                    "analysis": {"model": "haiku", "answers": ["Done"], "template": "standup"},
                }
            ),
            "get_streaming_transcript_fn": lambda: json.dumps({"partial": "Hel", "finals": ["Hello"]}),
            "get_session_ids_with_action_items_fn": lambda: "[7, 9]",
            "get_upcoming_events_fn": lambda: '[{"summary":"Daily sync","start_iso":"2026-03-08T10:00:00+00:00"}]',
            "get_analytics_fn": lambda last: json.dumps(
                {"period": last, "total_cost_usd": 1.5, "total_calls": 2, "by_day": [{"date": "2026-03-08"}]}
            ),
            "get_api_version_fn": lambda: "1.0",
        },
    )


def test_sync_and_async_session_detail_payloads_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLogSessionDetail)

    status, _, body = server_async._sync_session_by_id("7")
    data = json.loads(body.decode("utf-8"))

    assert status == 200
    assert data == {
        "session_id": 7,
        "segments": [{"start_sec": 0.0, "end_sec": 2.0, "speaker": "Speaker 1", "text": "hello"}],
        "analysis": {
            "model": "test-model",
            "questions": ["Q1"],
            "answers": ["A1"],
            "recommendations": ["R1"],
            "action_items": [{"description": "Ship it", "status": "open"}],
            "cost_usd": 0.25,
            "template": "standup",
        },
    }


def test_sync_http_session_detail_not_found_matches_async_contract(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLogSessionDetail)

    from http.server import HTTPServer

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/sessions/999", timeout=2):
            raise AssertionError("expected 404")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {
            "error": {
                "code": "NOT_FOUND",
                "message": session_not_found_message(999),
            }
        }
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.mark.asyncio
async def test_async_stream_endpoint_reuses_analyze_validation() -> None:
    try:
        from starlette.testclient import TestClient
    except ModuleNotFoundError:
        pytest.skip("starlette test client not installed")

    app = server_async._build_app()
    with TestClient(app) as client:
        response = client.post("/api/analyze/stream", json={"seconds": 30, "template": "bad"})

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "template must be one of: standup, sprint_review, one_on_one, brainstorm, interview",
        }
    }


def test_dbus_desktop_contract_snapshot_for_envelope_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _iface()

    settings = json.loads(DaemonVoiceForgeInterface.GetSettings.__wrapped__(iface))
    detail = json.loads(DaemonVoiceForgeInterface.GetSessionDetail.__wrapped__(iface, 7))
    streaming = json.loads(DaemonVoiceForgeInterface.GetStreamingTranscript.__wrapped__(iface))
    session_ids = json.loads(DaemonVoiceForgeInterface.GetSessionIdsWithActionItems.__wrapped__(iface))
    events = json.loads(DaemonVoiceForgeInterface.GetUpcomingEvents.__wrapped__(iface))
    analytics = json.loads(DaemonVoiceForgeInterface.GetAnalytics.__wrapped__(iface, "7d"))
    capabilities = json.loads(DaemonVoiceForgeInterface.GetCapabilities.__wrapped__(iface))

    assert settings == {
        "schema_version": "1.0",
        "ok": True,
        "data": {
            "settings": {
                "model_size": "small",
                "default_llm": "anthropic/claude-haiku-4-5",
                "budget_limit_usd": 75.0,
                "sample_rate": 16000,
                "streaming_stt": False,
                "pii_mode": "ON",
                "privacy_mode": "ON",
            }
        },
    }
    assert detail == {
        "schema_version": "1.0",
        "ok": True,
        "data": {
            "session_detail": {
                "session_id": 7,
                "segments": [{"start_sec": 0.0, "end_sec": 1.0, "speaker": "A", "text": "Hi"}],
                "analysis": {"model": "haiku", "answers": ["Done"], "template": "standup"},
            }
        },
    }
    assert streaming == {
        "schema_version": "1.0",
        "ok": True,
        "data": {"streaming_transcript": {"partial": "Hel", "finals": ["Hello"]}},
    }
    assert session_ids == {
        "schema_version": "1.0",
        "ok": True,
        "data": {"session_ids": [7, 9]},
    }
    assert events == {
        "schema_version": "1.0",
        "ok": True,
        "data": {"events": [{"summary": "Daily sync", "start_iso": "2026-03-08T10:00:00+00:00"}]},
    }
    assert analytics == {
        "schema_version": "1.0",
        "ok": True,
        "data": {
            "analytics": {
                "period": "7d",
                "total_cost_usd": 1.5,
                "total_calls": 2,
                "by_day": [{"date": "2026-03-08"}],
            }
        },
    }
    assert capabilities == {
        "api_version": "1.0",
        "features": {"envelope_v1": True},
    }
