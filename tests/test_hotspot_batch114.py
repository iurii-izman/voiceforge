"""Focused regression tests for hotspot decomposition batch #114."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from voiceforge.web import server_async


class _FakeResponse:
    def __init__(self, body, status_code, media_type) -> None:
        self.body = body
        self.status_code = status_code
        self.media_type = media_type
        self.headers: dict[str, str] = {}


class _FakeJsonRequest:
    def __init__(self, payload=None, *, exc: Exception | None = None) -> None:
        self._payload = payload
        self._exc = exc

    async def json(self):
        if self._exc is not None:
            raise self._exc
        return self._payload


@pytest.mark.asyncio
async def test_server_async_response_helpers_wrap_sync_result() -> None:
    response = await server_async._to_thread_response(
        _FakeResponse,
        lambda value: (201, "text/plain", f"ok:{value}".encode()),
        "x",
    )

    assert response.status_code == 201
    assert response.media_type == "text/plain"
    assert response.body == b"ok:x"


@pytest.mark.asyncio
async def test_server_async_json_request_to_response_handles_invalid_json() -> None:
    response = await server_async._json_request_to_response(
        _FakeJsonRequest(exc=ValueError("bad json")),
        _FakeResponse,
        lambda data: (200, server_async._CONTENT_TYPE_JSON, b"{}"),
    )

    assert response.status_code == 400
    assert json.loads(response.body.decode("utf-8")) == {"error": {"code": "BAD_REQUEST", "message": "invalid JSON"}}


@pytest.mark.asyncio
async def test_server_async_json_request_to_response_passes_payload() -> None:
    response = await server_async._json_request_to_response(
        _FakeJsonRequest(payload={"seconds": 15}),
        _FakeResponse,
        lambda data: (200, server_async._CONTENT_TYPE_JSON, json.dumps(data).encode("utf-8")),
    )

    assert response.status_code == 200
    assert json.loads(response.body.decode("utf-8")) == {"seconds": 15}


def test_main_emit_success_and_calendar_helpers(monkeypatch) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    main._emit_success("text", {"ok": True}, "plain text")
    main._emit_success("json", {"ok": True}, "ignored")
    main._calendar_poll_emit("text", 5, [])
    main._calendar_poll_emit("text", 5, [{"summary": "Demo", "start_iso": "2026-03-08T10:00:00+00:00"}])
    main._calendar_poll_emit("json", 5, [{"summary": "Demo", "start_iso": "2026-03-08T10:00:00+00:00"}])
    main._calendar_create_emit("text", "uid-1")
    main._calendar_create_emit("json", "uid-2")

    assert echoed[0] == ("plain text", False)
    json_payload = json.loads(echoed[1][0])
    assert json_payload["ok"] is True
    assert json_payload["data"] == {"ok": True}
    assert "нет событий" in echoed[2][0].lower() or "no events" in echoed[2][0].lower()
    assert any("Demo" in message for message, _ in echoed)
    assert any("uid-1" in message for message, _ in echoed)
    assert any(json.loads(message)["data"] == {"event_uid": "uid-2"} for message, _ in echoed if message.startswith("{"))


def test_main_status_and_calendar_commands_reuse_helpers(monkeypatch) -> None:
    from voiceforge import main

    emits: list[tuple[str, tuple[object, ...]]] = []
    monkeypatch.setattr(main, "_emit_success", lambda output, data, text: emits.append(("status", (output, data, text))))
    monkeypatch.setattr(main, "get_doctor_data", lambda: {"doctor": True})
    monkeypatch.setattr(main, "get_doctor_text", lambda: "doctor")
    monkeypatch.setattr(main, "get_status_data", lambda: {"status": True})
    monkeypatch.setattr(main, "get_status_text", lambda: "status")
    monkeypatch.setattr(main, "get_status_detailed_data", lambda budget: {"budget": budget})
    monkeypatch.setattr(main, "get_status_detailed_text", lambda budget: f"detailed {budget}")
    monkeypatch.setattr(main, "_get_config", lambda: SimpleNamespace(budget_limit_usd=12.5))

    main.status(output="json", doctor=True, detailed=False)
    main.status(output="text", doctor=False, detailed=True)
    main.status(output="text", doctor=False, detailed=False)

    assert emits == [
        ("status", ("json", {"doctor": True}, "doctor")),
        ("status", ("text", {"budget": 12.5}, "detailed 12.5")),
        ("status", ("text", {"status": True}, "status")),
    ]

    calendar_calls: list[tuple[str, tuple[object, ...]]] = []
    monkeypatch.setattr(
        main, "_calendar_poll_emit", lambda output, minutes, events: calendar_calls.append(("poll", (output, minutes, events)))
    )
    monkeypatch.setattr(
        main, "_calendar_create_emit", lambda output, event_uid: calendar_calls.append(("create", (output, event_uid)))
    )
    monkeypatch.setattr("voiceforge.calendar.poll_events_started_in_last", lambda minutes: ([{"summary": "Demo"}], None))
    monkeypatch.setattr("voiceforge.calendar.create_event", lambda **kwargs: ("uid-42", None))

    class _FakeLogDb:
        def get_session_meta(self, session_id: int):
            return ("2026-03-08T10:00:00+00:00", "2026-03-08T11:00:00+00:00", 3600)

        def get_session_detail(self, session_id: int):
            return ([], None)

        def close(self) -> None:
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeLogDb)

    main.calendar_poll(minutes=5, output="json")
    main.calendar_create_from_session(session_id=7, calendar_url=None, output="text")

    assert calendar_calls == [
        ("poll", ("json", 5, [{"summary": "Demo"}])),
        ("create", ("text", "uid-42")),
    ]
