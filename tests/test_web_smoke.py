"""Minimal smoke tests for Web UI (coverage for new-code check)."""

from __future__ import annotations

import socket
import threading
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
    finally:
        server.shutdown()
