"""Phase B #61: request tracing (trace_id + structlog)."""

from __future__ import annotations

import re


def test_bind_trace_id_generates_16_hex() -> None:
    """bind_trace_id() with no arg returns 16-char hex."""
    from voiceforge.core.tracing import bind_trace_id, clear_trace_context

    clear_trace_context()
    tid = bind_trace_id()
    assert isinstance(tid, str)
    assert len(tid) == 16
    assert re.match(r"^[a-f0-9]{16}$", tid)


def test_get_trace_id_after_bind() -> None:
    """get_trace_id() returns bound value."""
    from voiceforge.core.tracing import bind_trace_id, clear_trace_context, get_trace_id

    clear_trace_context()
    assert get_trace_id() is None
    tid = bind_trace_id("abc1234567890123")
    assert get_trace_id() == "abc1234567890123"
    assert tid == "abc1234567890123"


def test_clear_trace_context() -> None:
    """clear_trace_context() clears trace_id."""
    from voiceforge.core.tracing import bind_trace_id, clear_trace_context, get_trace_id

    bind_trace_id("deadbeef12345678")
    assert get_trace_id() == "deadbeef12345678"
    clear_trace_context()
    assert get_trace_id() is None


def test_bind_trace_id_uses_provided() -> None:
    """bind_trace_id(trace_id='x') uses provided id (strip, min 1 char)."""
    from voiceforge.core.tracing import bind_trace_id, clear_trace_context, get_trace_id

    clear_trace_context()
    out = bind_trace_id("  custom-id-16ch  ")
    assert out == "custom-id-16ch"
    assert get_trace_id() == "custom-id-16ch"


def test_bind_trace_id_empty_after_strip_generates() -> None:
    """bind_trace_id with whitespace-only generates new id (branch coverage)."""
    from voiceforge.core.tracing import bind_trace_id, clear_trace_context, get_trace_id

    clear_trace_context()
    out = bind_trace_id("   ")
    assert isinstance(out, str)
    assert len(out) == 16
    assert get_trace_id() == out


def test_web_response_includes_x_trace_id(monkeypatch, tmp_path) -> None:
    """GET /api/status response includes X-Trace-Id when tracing is bound."""
    import socket
    import threading
    import urllib.request
    from http.server import HTTPServer

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    from voiceforge.web.server import _VoiceForgeHandler

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = HTTPServer(("127.0.0.1", port), _VoiceForgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
        with urllib.request.urlopen(req, timeout=2) as r:
            assert r.status == 200
            trace_header = r.headers.get("X-Trace-Id")
            assert trace_header is not None
            assert len(trace_header) >= 1
    finally:
        server.shutdown()
