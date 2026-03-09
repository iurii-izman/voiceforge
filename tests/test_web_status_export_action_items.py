"""Targeted tests for server.py status, export, action-items (issue #99 policy batch).

Narrow suite to support removing server.py from coverage omit.
"""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import HTTPServer

import pytest


@dataclass
class _FakeSegment:
    text: str


@dataclass
class _FakeAnalysis:
    action_items: list[dict[str, str]]


class _FakeTranscriptLogExport:
    """Fake log for export tests: session 1 returns detail, others None."""

    def get_session_detail(self, session_id: int):
        if session_id == 1:
            return (
                [_FakeSegment("Hello"), _FakeSegment("World")],
                _FakeAnalysis(action_items=[]),
            )
        return None

    def close(self) -> None:
        # No-op for test fake (S1186).
        pass


class _FakeTranscriptLogActionItemsEmpty:
    """Fake log: from_session has analysis with empty action_items; next has segments."""

    def get_session_detail(self, session_id: int):
        if session_id == 20:
            return (
                [_FakeSegment("Segment")],
                _FakeAnalysis(action_items=[]),
            )
        if session_id == 21:
            return ([_FakeSegment("Done")], None)
        return None

    def close(self) -> None:
        # No-op for test fake (S1186).
        pass


class _FakeTranscriptLogActionItemsSessionNotFound:
    """Fake log: from_session exists, next_session missing."""

    def get_session_detail(self, session_id: int):
        if session_id == 30:
            return (
                [_FakeSegment("x")],
                _FakeAnalysis(action_items=[{"description": "Task"}]),
            )
        return None

    def close(self) -> None:
        # No-op for test fake (S1186).
        pass


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_server_get_export_validation_id_required(monkeypatch, tmp_path) -> None:
    """GET /api/export without id returns 400."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/export?format=md",
            timeout=2,
        ) as _:
            pass
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload["error"]["message"] == "id required and must be numeric"
    else:
        raise AssertionError("expected 400")
    finally:
        server.shutdown()


def test_server_get_export_validation_format(monkeypatch, tmp_path) -> None:
    """GET /api/export with invalid format returns 400."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/export?id=1&format=docx",
            timeout=2,
        ) as _:
            pass
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
        payload = json.loads(exc.read().decode("utf-8"))
        assert "format" in payload["error"]["message"].lower()
    else:
        raise AssertionError("expected 400")
    finally:
        server.shutdown()


def test_server_get_export_session_not_found(monkeypatch, tmp_path) -> None:
    """GET /api/export?id=999&format=md with no session returns 404."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        _FakeTranscriptLogExport,
    )

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/export?id=999&format=md",
            timeout=2,
        ) as _:
            pass
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
        payload = json.loads(exc.read().decode("utf-8"))
        assert "999" in payload["error"]["message"] or "не найдена" in payload["error"]["message"]
    else:
        raise AssertionError("expected 404")
    finally:
        server.shutdown()


def test_server_get_export_md_success(monkeypatch, tmp_path) -> None:
    """GET /api/export?id=1&format=md returns 200 and markdown body."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        _FakeTranscriptLogExport,
    )

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/export?id=1&format=md",
            timeout=2,
        ) as r:
            assert r.status == 200
            assert "text/markdown" in r.headers.get("Content-Type", "")
            body = r.read().decode("utf-8")
            assert "Сессия" in body or "session" in body.lower() or "Hello" in body
    finally:
        server.shutdown()


def test_server_get_status_exception_returns_500(monkeypatch, tmp_path) -> None:
    """When get_status_data raises, GET /api/status returns 500."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers.get_status_data",
        lambda: (_ for _ in ()).throw(RuntimeError("status failed")),
    )

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/status",
            timeout=2,
        ) as _:
            pass
    except urllib.error.HTTPError as exc:
        assert exc.code == 500
        payload = json.loads(exc.read().decode("utf-8"))
        assert "error" in payload and "status failed" in payload["error"].get("message", "")
    else:
        raise AssertionError("expected 500")
    finally:
        server.shutdown()


def test_server_action_items_update_invalid_integers(monkeypatch, tmp_path) -> None:
    """POST /api/action-items/update with non-integer from_session returns 400."""
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
            data=json.dumps({"from_session": "x", "next_session": 11}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read().decode("utf-8"))
            assert "integer" in payload["error"]["message"].lower()
        else:
            raise AssertionError("expected 400")
    finally:
        server.shutdown()


def test_server_action_items_update_session_not_found(monkeypatch, tmp_path) -> None:
    """POST /api/action-items/update when next_session missing returns 404."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        _FakeTranscriptLogActionItemsSessionNotFound,
    )

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/action-items/update",
            data=json.dumps({"from_session": 30, "next_session": 99}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
            payload = json.loads(exc.read().decode("utf-8"))
            assert "99" in payload["error"]["message"]
        else:
            raise AssertionError("expected 404")
    finally:
        server.shutdown()


def test_server_action_items_update_empty_action_items_returns_200(monkeypatch, tmp_path) -> None:
    """POST /api/action-items/update when action_items empty returns 200 with empty updates."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        _FakeTranscriptLogActionItemsEmpty,
    )

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/action-items/update",
            data=json.dumps({"from_session": 20, "next_session": 21}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            assert r.status == 200
            payload = json.loads(r.read().decode("utf-8"))
            assert payload.get("updates") == []
            assert payload.get("cost_usd") == pytest.approx(0.0)
    finally:
        server.shutdown()
