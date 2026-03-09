from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import HTTPServer


@dataclass
class _FakeSegment:
    text: str


@dataclass
class _FakeAnalysis:
    action_items: list[dict[str, str]]


class _FakeTranscriptLog:
    def get_session_detail(self, session_id: int):
        if session_id == 10:
            return ([_FakeSegment("Discuss roadmap")], _FakeAnalysis(action_items=[{"description": "Ship fix"}]))
        if session_id == 11:
            return ([_FakeSegment("Fix shipped and verified")], None)
        return None

    def close(self) -> None:
        return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _install_action_items_fakes(monkeypatch):
    saved_payloads: list[dict[str, str]] = []

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLog)

    def _fake_update_action_item_statuses(action_items, transcript_next, model, pii_mode):
        assert action_items == [{"description": "Ship fix"}]
        assert transcript_next == "Fix shipped and verified"
        assert model == "test-model"
        assert pii_mode == "off"

        class _Response:
            def __init__(self) -> None:
                self.updates = [type("Update", (), {"id": 0, "status": "done"})()]

        return (_Response(), 0.42)

    monkeypatch.setattr("voiceforge.llm.router.update_action_item_statuses", _fake_update_action_item_statuses)
    monkeypatch.setattr(
        "voiceforge.main._get_config",
        lambda: type("Cfg", (), {"default_llm": "test-model", "pii_mode": "off"})(),
    )
    monkeypatch.setattr("voiceforge.main._load_action_item_status", lambda: {})
    monkeypatch.setattr("voiceforge.main._save_action_item_status", lambda data: saved_payloads.append(data.copy()))
    return saved_payloads


def test_sync_web_action_items_update_happy_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    saved_payloads = _install_action_items_fakes(monkeypatch)

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/action-items/update",
            data=json.dumps({"from_session": 10, "next_session": 11}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            assert response.status == 200
            payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()

    assert payload == {
        "from_session": 10,
        "next_session": 11,
        "updates": [{"id": 0, "status": "done"}],
        "cost_usd": 0.42,
    }
    assert saved_payloads == [{"10:0": "done"}]


def test_sync_web_action_items_update_returns_nested_error_envelope(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/action-items/update",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read().decode("utf-8"))
        else:
            raise AssertionError("expected 400 response")
    finally:
        server.shutdown()

    assert payload == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "from_session and next_session required",
        }
    }


def test_async_action_items_update_matches_sync_contract(monkeypatch) -> None:
    saved_payloads = _install_action_items_fakes(monkeypatch)

    from voiceforge.web.server_async import _CONTENT_TYPE_JSON, _sync_action_items_update

    status, content_type, body = _sync_action_items_update({"from_session": 10, "next_session": 11})
    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert content_type == _CONTENT_TYPE_JSON
    assert payload == {
        "from_session": 10,
        "next_session": 11,
        "updates": [{"id": 0, "status": "done"}],
        "cost_usd": 0.42,
    }
    assert saved_payloads == [{"10:0": "done"}]


def test_async_action_items_update_returns_nested_error_envelope() -> None:
    from voiceforge.web.server_async import _CONTENT_TYPE_JSON, _sync_action_items_update

    status, content_type, body = _sync_action_items_update({})
    payload = json.loads(body.decode("utf-8"))

    assert status == 400
    assert content_type == _CONTENT_TYPE_JSON
    assert payload == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "from_session and next_session required",
        }
    }
