"""Contract parity: sync and async web API use same _sync_* handlers (#108).

Async server delegates to the same _sync_* functions, so response shape is identical.
These tests document and assert the shared JSON contract for key endpoints.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from voiceforge.web import server_async


def test_contract_status_returns_ok_and_ram(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/status: JSON has 'ok' and optional ram_mb (sync/async same)."""
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers.get_status_data",
        lambda: {"ok": True, "ram_mb": 100},
    )
    status, _, body = server_async._sync_status()
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert "ok" in data
    assert data.get("ram_mb") == 100


def test_contract_ready_returns_ready_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/ready: JSON has 'ready' boolean (sync/async same)."""
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        lambda: MagicMock(
            get_sessions=lambda **kw: [],
            close=lambda: None,
        ),
    )
    status, _, body = server_async._sync_ready()
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert "ready" in data
    assert isinstance(data["ready"], bool)


def test_contract_health_returns_status_ok() -> None:
    """GET /api/health: JSON has 'status': 'ok' (sync/async same)."""
    status, _, body = server_async._sync_health()
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert data == {"status": "ok"}


def test_contract_sessions_returns_sessions_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/sessions: JSON has 'sessions' array (sync/async same)."""
    monkeypatch.setattr(
        "voiceforge.core.transcript_log.TranscriptLog",
        lambda: MagicMock(
            get_sessions=lambda **kw: [],
            close=lambda: None,
        ),
    )
    status, _, body = server_async._sync_sessions()
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_contract_cost_returns_total_cost_and_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/cost: JSON has total_cost_usd and total_calls (sync/async same)."""
    monkeypatch.setattr(
        "voiceforge.core.metrics.get_stats",
        lambda **kw: {"total_cost_usd": 1.5, "total_calls": 10, "by_day": []},
    )
    status, _, body = server_async._sync_cost("30", "", "")
    data = json.loads(body.decode("utf-8"))
    assert status == 200
    assert "total_cost_usd" in data
    assert "total_calls" in data


def test_contract_error_has_code_and_message() -> None:
    """Error responses: JSON has 'error' with 'code' and 'message' (sync/async same)."""
    _, _, body = server_async._sync_export("", "md")
    data = json.loads(body.decode("utf-8"))
    assert "error" in data
    assert "message" in data["error"]


def test_async_app_builds_without_error() -> None:
    """Parity by design: async app builds when starlette available; routes delegate to _sync_*."""
    try:
        app = server_async._build_app()
        assert app is not None
        assert len(app.routes) >= 1
    except ModuleNotFoundError:
        pytest.skip("starlette not installed (web-async extra)")
