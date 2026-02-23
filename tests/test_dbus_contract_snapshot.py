from __future__ import annotations

import json

from voiceforge.core.dbus_service import DaemonVoiceForgeInterface


def _iface() -> DaemonVoiceForgeInterface:
    return DaemonVoiceForgeInterface(
        analyze_fn=lambda seconds: f"ok-{seconds}",
        status_fn=lambda: "idle",
        listen_start_fn=lambda: None,
        listen_stop_fn=lambda: None,
        is_listening_fn=lambda: False,
        get_sessions_fn=lambda last_n: "[]",
        get_session_detail_fn=lambda session_id: "{}",
        get_settings_fn=lambda: "{}",
        get_indexed_paths_fn=lambda: "[]",
        get_streaming_transcript_fn=lambda: '{"partial":"","finals":[]}',
        swap_model_fn=lambda model_type, model_name: "ok",
        ping_fn=lambda: "pong",
        get_analytics_fn=lambda last: "{}",
        get_api_version_fn=lambda: "1.0",
    )


def test_dbus_capabilities_snapshot_default(monkeypatch) -> None:
    """Default: envelope on (W7)."""
    monkeypatch.delenv("VOICEFORGE_IPC_ENVELOPE", raising=False)
    iface = _iface()
    payload = json.loads(DaemonVoiceForgeInterface.GetCapabilities.__wrapped__(iface))
    assert payload == {"api_version": "1.0", "features": {"envelope_v1": True}}


def test_dbus_capabilities_snapshot_legacy_no_envelope(monkeypatch) -> None:
    """Legacy: VOICEFORGE_IPC_ENVELOPE=0 gives envelope_v1 False."""
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "0")
    iface = _iface()
    payload = json.loads(DaemonVoiceForgeInterface.GetCapabilities.__wrapped__(iface))
    assert payload["features"]["envelope_v1"] is False


def test_dbus_sessions_snapshot_with_envelope(monkeypatch) -> None:
    monkeypatch.setenv("VOICEFORGE_IPC_ENVELOPE", "1")
    iface = _iface()
    payload = json.loads(DaemonVoiceForgeInterface.GetSessions.__wrapped__(iface, 10))
    assert payload["schema_version"] == "1.0"
    assert payload["ok"] is True
    assert payload["data"] == {"sessions": []}
