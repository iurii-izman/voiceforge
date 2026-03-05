"""Tests for core/dbus_service (#56): helpers and interfaces without real D-Bus bus)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceforge.core.dbus_service import (
    DaemonVoiceForgeInterface,
    VoiceForgeAppInterface,
    run_dbus_service,
)


# --- Helpers (test via public behaviour or import private for unit coverage) ---


def test_env_flag_default_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """_env_flag returns default when var unset."""
    import voiceforge.core.dbus_service as m

    monkeypatch.delenv("VOICEFORGE_IPC_ENVELOPE", raising=False)
    assert m._env_flag("VOICEFORGE_IPC_ENVELOPE", default=False) is False
    assert m._env_flag("VOICEFORGE_IPC_ENVELOPE", default=True) is True


def test_env_flag_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """_env_flag returns True for 1, true, yes, on."""
    import voiceforge.core.dbus_service as m

    for val in ("1", "true", "yes", "on", "TRUE"):
        monkeypatch.setenv("VF_TEST_FLAG", val)
        assert m._env_flag("VF_TEST_FLAG", default=False) is True


def test_env_flag_false_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """_env_flag returns False for 0, false, empty, other."""
    import voiceforge.core.dbus_service as m

    for val in ("0", "false", "", "x", "no"):
        monkeypatch.setenv("VF_TEST_FLAG", val)
        assert m._env_flag("VF_TEST_FLAG", default=True) is False


def test_analyze_result_is_error_russian_prefix() -> None:
    """_analyze_result_is_error True for 'Ошибка:' prefix."""
    import voiceforge.core.dbus_service as m

    assert m._analyze_result_is_error("Ошибка: something") is True
    assert m._analyze_result_is_error("Ok result") is False


def test_analyze_result_is_error_json_error() -> None:
    """_analyze_result_is_error True for JSON with 'error' key."""
    import voiceforge.core.dbus_service as m

    assert m._analyze_result_is_error('{"error":{"code":"X","message":"Y"}}') is True
    assert m._analyze_result_is_error('{"data":"ok"}') is False


def test_make_ipc_error_returns_valid_json() -> None:
    """_make_ipc_error returns JSON with error code and message."""
    import voiceforge.core.dbus_service as m

    out = m._make_ipc_error("TEST_CODE", "test message", retryable=True)
    data = json.loads(out)
    assert data.get("ok") is False
    assert data.get("error", {}).get("code") == "TEST_CODE"
    assert data.get("error", {}).get("message") == "test message"
    assert data.get("error", {}).get("retryable") is True


def test_make_ipc_success_returns_valid_json() -> None:
    """_make_ipc_success returns JSON with data."""
    import voiceforge.core.dbus_service as m

    out = m._make_ipc_success({"text": "hello"})
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("data", {}).get("text") == "hello"


def test_analyze_ipc_return_success_path() -> None:
    """_analyze_ipc_return returns success envelope when not error."""
    import voiceforge.core.dbus_service as m

    out = m._analyze_ipc_return("some text result", is_error=False)
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("data", {}).get("text") == "some text result"


def test_analyze_ipc_return_error_json() -> None:
    """_analyze_ipc_return parses error JSON and returns IPC error."""
    import voiceforge.core.dbus_service as m

    err = '{"error":{"code":"X","message":"Y","retryable":true}}'
    out = m._analyze_ipc_return(err, is_error=True)
    data = json.loads(out)
    assert data.get("ok") is False
    assert data.get("error", {}).get("code") == "X"
    assert data.get("error", {}).get("message") == "Y"


# --- VoiceForgeAppInterface (call via __wrapped__ like test_dbus_contract_snapshot) ---


def test_app_interface_analyze_invalid_seconds() -> None:
    """Analyze returns error for seconds < 1 or > ANALYZE_MAX_SECONDS."""
    iface = VoiceForgeAppInterface()

    async def run() -> None:
        out0 = await VoiceForgeAppInterface.Analyze.__wrapped__(iface, 0)
        out3601 = await VoiceForgeAppInterface.Analyze.__wrapped__(iface, 3601)
        assert "INVALID_SECONDS" in out0
        assert "INVALID_SECONDS" in out3601

    asyncio.run(run())


def test_app_interface_analyze_not_configured() -> None:
    """Analyze returns NOT_CONFIGURED when analyze_fn is None."""
    iface = VoiceForgeAppInterface()

    async def run() -> None:
        out = await VoiceForgeAppInterface.Analyze.__wrapped__(iface, 30)
        assert "NOT_CONFIGURED" in out

    asyncio.run(run())


def test_app_interface_analyze_with_callback() -> None:
    """Analyze returns result from analyze_fn."""

    def analyze_fn(seconds: int) -> str:
        return f"analyzed {seconds}s"

    iface = VoiceForgeAppInterface(analyze_fn=analyze_fn)

    async def run() -> None:
        out = await VoiceForgeAppInterface.Analyze.__wrapped__(iface, 30)
        assert "analyzed 30s" in out

    asyncio.run(run())


def test_app_interface_toggle_without_callback() -> None:
    """Toggle returns 'ok' when toggle_fn is None."""
    iface = VoiceForgeAppInterface()
    assert VoiceForgeAppInterface.Toggle.__wrapped__(iface) == "ok"


def test_app_interface_toggle_with_callback() -> None:
    """Toggle returns value from toggle_fn."""
    iface = VoiceForgeAppInterface(toggle_fn=lambda: "listening")
    assert VoiceForgeAppInterface.Toggle.__wrapped__(iface) == "listening"


def test_app_interface_status_without_callback() -> None:
    """Status returns 'idle' when status_fn is None."""
    iface = VoiceForgeAppInterface()
    assert VoiceForgeAppInterface.Status.__wrapped__(iface) == "idle"


def test_app_interface_status_with_callback() -> None:
    """Status returns value from status_fn."""
    iface = VoiceForgeAppInterface(status_fn=lambda: "recording")
    assert VoiceForgeAppInterface.Status.__wrapped__(iface) == "recording"


# --- DaemonVoiceForgeInterface (sync methods via __wrapped__) ---


def _daemon_iface(**optional: object) -> DaemonVoiceForgeInterface:
    return DaemonVoiceForgeInterface(
        analyze_fn=lambda s, t: f"ok-{s}",
        status_fn=lambda: "idle",
        listen_start_fn=lambda: None,
        listen_stop_fn=lambda: None,
        is_listening_fn=lambda: False,
        optional=optional or None,
    )


def test_daemon_status_with_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    """Status with envelope returns IPC success JSON."""
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _daemon_iface()
    out = DaemonVoiceForgeInterface.Status.__wrapped__(iface)
    data = json.loads(out)
    assert data.get("ok") is True
    assert data.get("data", {}).get("text") == "idle"


def test_daemon_get_sessions_no_callback_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """GetSessions without callback returns [] in envelope."""
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _daemon_iface()
    out = DaemonVoiceForgeInterface.GetSessions.__wrapped__(iface, 5)
    data = json.loads(out)
    assert data.get("data", {}).get("sessions") == []


def test_daemon_get_settings_with_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    """GetSettings with callback returns wrapped payload."""
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _daemon_iface(get_settings_fn=lambda: '{"model_size":"tiny"}')
    out = DaemonVoiceForgeInterface.GetSettings.__wrapped__(iface)
    data = json.loads(out)
    assert data.get("data", {}).get("settings", {}).get("model_size") == "tiny"


def test_daemon_ping_no_callback_returns_pong() -> None:
    """Ping without callback returns 'pong'."""
    iface = _daemon_iface()
    assert DaemonVoiceForgeInterface.Ping.__wrapped__(iface) == "pong"


def test_daemon_analyze_invalid_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Analyze with invalid template returns INVALID_TEMPLATE error."""

    async def run() -> None:
        iface = _daemon_iface()
        out = await DaemonVoiceForgeInterface.Analyze.__wrapped__(iface, 30, "bad_template")
        assert "INVALID_TEMPLATE" in out

    asyncio.run(run())


def test_daemon_analyze_ok_with_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    """Analyze success path returns IPC success with text."""

    async def run() -> None:
        monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
        iface = _daemon_iface()
        out = await DaemonVoiceForgeInterface.Analyze.__wrapped__(iface, 30, "")
        data = json.loads(out)
        assert data.get("ok") is True
        assert "ok-30" in str(data.get("data", {}).get("text", ""))

    asyncio.run(run())


def test_daemon_get_session_detail_get_indexed_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """GetSessionDetail and GetIndexedPaths with callbacks return wrapped payload."""
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _daemon_iface(
        get_session_detail_fn=lambda sid: '{"segments":[]}',
        get_indexed_paths_fn=lambda: '["/a","/b"]',
    )
    out_detail = DaemonVoiceForgeInterface.GetSessionDetail.__wrapped__(iface, 1)
    out_paths = DaemonVoiceForgeInterface.GetIndexedPaths.__wrapped__(iface)
    assert json.loads(out_detail).get("data", {}).get("session_detail", {}).get("segments") == []
    assert json.loads(out_paths).get("data", {}).get("indexed_paths") == ["/a", "/b"]


def test_daemon_get_api_version_and_capabilities_with_callbacks() -> None:
    """GetApiVersion/GetCapabilities with callbacks return callback result."""
    iface = _daemon_iface(
        get_api_version_fn=lambda: "2.0",
        get_capabilities_fn=lambda: '{"api_version":"2.0","features":{"x":true}}',
    )
    assert DaemonVoiceForgeInterface.GetApiVersion.__wrapped__(iface) == "2.0"
    out = DaemonVoiceForgeInterface.GetCapabilities.__wrapped__(iface)
    assert "2.0" in out
    assert "x" in out


# --- run_dbus_service (mocked bus, no real D-Bus) ---


def test_run_dbus_service_mocked_bus() -> None:
    """run_dbus_service with mocked MessageBus runs and exits."""
    from voiceforge.core.dbus_service import run_dbus_service

    mock_bus = MagicMock()
    mock_bus.export = MagicMock()
    mock_bus.request_name = AsyncMock(return_value=None)
    mock_bus.wait_for_disconnect = AsyncMock(return_value=None)
    mock_bus.disconnect = MagicMock()

    with patch("voiceforge.core.dbus_service.MessageBus") as mb:
        mb.return_value.connect = AsyncMock(return_value=mock_bus)
        asyncio.run(run_dbus_service())

    mock_bus.export.assert_called_once()
    mock_bus.request_name.assert_called_once()
    mock_bus.wait_for_disconnect.assert_called_once()
