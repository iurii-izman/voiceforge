"""Minimal smoke tests for Web UI (coverage for new-code check)."""

from __future__ import annotations

import socket
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_web_index_and_status(monkeypatch, tmp_path) -> None:
    """GET / and GET /api/status return 200 and expected content."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as r:
            assert r.status == 200
            body = r.read().decode("utf-8")
            assert "VoiceForge" in body
            assert "Анализ" in body or "analyze" in body.lower()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=2) as r:
            assert r.status == 200
            body = r.read().decode("utf-8")
            data = __import__("json").loads(body)
            assert "ram" in data or "cost_today" in data
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/cost", timeout=2) as r:
            assert r.status == 200
            body = r.read().decode("utf-8")
            data = __import__("json").loads(body)
            assert "total_cost_usd" in data or "by_day" in data
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            assert r.status == 200
            data = __import__("json").loads(r.read().decode("utf-8"))
            assert data.get("status") == "ok"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/ready", timeout=2) as r:
            assert r.status == 200
            data = __import__("json").loads(r.read().decode("utf-8"))
            assert data.get("ready") is True
    finally:
        server.shutdown()


def test_web_telegram_webhook_no_token_returns_503(monkeypatch, tmp_path) -> None:
    """Without webhook_telegram in keyring, POST /api/telegram/webhook returns 503 (ADR-0005)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", lambda name: None)

    from voiceforge.web.server import _VoiceForgeHandler

    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/telegram/webhook",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.HTTPError as e:
            assert e.code == 503
            body = e.read().decode("utf-8")
            assert "webhook_telegram" in body or "ok" in body
        else:
            raise AssertionError("expected 503")
    finally:
        server.shutdown()
