"""Targeted coverage for core/daemon.py (#109).

Helper-level and smoke tests: _streaming_language_hint, _pid_path, _event_start_in_window,
VoiceForgeDaemon get_settings/get_streaming_transcript/get_api_version/get_capabilities,
get_sessions/get_session_detail/get_indexed_paths/search_rag/get_analytics with mocks,
_retention_purge_at_startup, _wire_daemon_iface. Reuses patterns from test_dbus_service,
test_dbus_contract_snapshot, test_coverage_hotspots_batch99.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from voiceforge.core.daemon import (
    PID_FILE_NAME,
    VoiceForgeDaemon,
    _env_flag,
    _event_start_in_window,
    _pid_path,
    _retention_purge_at_startup,
    _streaming_language_hint,
    _wire_daemon_iface,
)
from voiceforge.core.dbus_service import DaemonVoiceForgeInterface

# --- Module-level helpers ---


def test_streaming_language_hint_auto_and_empty() -> None:
    """_streaming_language_hint returns None for auto and empty."""
    assert _streaming_language_hint(SimpleNamespace(language="auto")) is None
    assert _streaming_language_hint(SimpleNamespace(language="")) is None
    assert _streaming_language_hint(SimpleNamespace()) is None


def test_streaming_language_hint_explicit() -> None:
    """_streaming_language_hint returns language when set."""
    assert _streaming_language_hint(SimpleNamespace(language="en")) == "en"
    assert _streaming_language_hint(SimpleNamespace(language="uk")) == "uk"


def test_pid_path_uses_xdg_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """_pid_path uses XDG_RUNTIME_DIR when set."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    p = _pid_path()
    assert str(p) == "/run/user/1000/voiceforge.pid"
    assert p.name == PID_FILE_NAME


def test_pid_path_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """_pid_path falls back to ~/.cache when XDG_RUNTIME_DIR unset."""
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    p = _pid_path()
    assert ".cache" in str(p) or "cache" in str(p)
    assert p.name == PID_FILE_NAME


def test_event_start_in_window_inside() -> None:
    """_event_start_in_window True when event start is in [now, window_end]."""
    now = datetime(2026, 3, 8, 10, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 8, 10, 30, 0, tzinfo=UTC)
    ev = {"start_iso": "2026-03-08T10:15:00+00:00"}
    assert _event_start_in_window(ev, now, end) is True


def test_event_start_in_window_z_suffix() -> None:
    """_event_start_in_window accepts Z suffix (converted to +00:00)."""
    now = datetime(2026, 3, 8, 10, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 8, 10, 30, 0, tzinfo=UTC)
    ev = {"start_iso": "2026-03-08T10:15:00Z"}
    assert _event_start_in_window(ev, now, end) is True


def test_event_start_in_window_before() -> None:
    """_event_start_in_window False when event is before window."""
    now = datetime(2026, 3, 8, 10, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 8, 10, 30, 0, tzinfo=UTC)
    ev = {"start_iso": "2026-03-08T09:00:00+00:00"}
    assert _event_start_in_window(ev, now, end) is False


def test_event_start_in_window_after() -> None:
    """_event_start_in_window False when event is after window."""
    now = datetime(2026, 3, 8, 10, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 8, 10, 30, 0, tzinfo=UTC)
    ev = {"start_iso": "2026-03-08T11:00:00+00:00"}
    assert _event_start_in_window(ev, now, end) is False


def test_event_start_in_window_empty_or_invalid() -> None:
    """_event_start_in_window False for missing or invalid start_iso."""
    now = datetime(2026, 3, 8, 10, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 8, 10, 30, 0, tzinfo=UTC)
    assert _event_start_in_window({}, now, end) is False
    assert _event_start_in_window({"start_iso": ""}, now, end) is False
    assert _event_start_in_window({"start_iso": "not-a-date"}, now, end) is False


# --- VoiceForgeDaemon with mocked Settings/ModelManager ---


def _make_daemon(
    *,
    iface: DaemonVoiceForgeInterface | None = None,
    settings_overrides: dict | None = None,
) -> VoiceForgeDaemon:
    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.stt_backend = "local"
    cfg.default_llm = "claude-3-5-haiku"
    cfg.budget_limit_usd = 10.0
    cfg.smart_trigger = False
    cfg.sample_rate = 16000
    cfg.streaming_stt = False
    cfg.pii_mode = "ON"
    cfg.language = "auto"
    cfg.calendar_autostart_enabled = False
    cfg.calendar_autostart_minutes = 5
    cfg.get_rag_db_path = MagicMock(return_value="/nonexistent/rag.db")
    if settings_overrides:
        for k, v in settings_overrides.items():
            setattr(cfg, k, v)
    with (
        patch("voiceforge.core.daemon.Settings", return_value=cfg),
        patch("voiceforge.core.daemon.ModelManager", return_value=MagicMock()),
        patch("voiceforge.core.daemon.set_model_manager"),
    ):
        return VoiceForgeDaemon(iface=iface)


def test_daemon_get_settings_returns_json() -> None:
    """get_settings returns valid JSON with expected keys."""
    daemon = _make_daemon()
    out = daemon.get_settings()
    data = json.loads(out)
    assert data.get("model_size") == "tiny"
    assert data.get("stt_backend") == "local"
    assert "pii_mode" in data
    assert data.get("privacy_mode") == data.get("pii_mode")


def test_daemon_get_streaming_transcript_default() -> None:
    """get_streaming_transcript returns JSON with partial and finals."""
    daemon = _make_daemon()
    out = daemon.get_streaming_transcript()
    data = json.loads(out)
    assert "partial" in data
    assert "finals" in data
    assert data["partial"] == ""
    assert data["finals"] == []


def test_daemon_get_api_version() -> None:
    """get_api_version returns 1.0."""
    daemon = _make_daemon()
    assert daemon.get_api_version() == "1.0"


def test_daemon_get_capabilities_has_features() -> None:
    """get_capabilities returns JSON with api_version and features."""
    daemon = _make_daemon()
    out = daemon.get_capabilities()
    data = json.loads(out)
    assert data.get("api_version") == "1.0"
    assert "features" in data
    assert data["features"].get("listen") is True
    assert data["features"].get("analyze") is True


def test_daemon_status_calls_main() -> None:
    """status returns get_status_text from main."""
    daemon = _make_daemon()
    with patch("voiceforge.main.get_status_text", return_value="RAM 100 MB"):
        result = daemon.status()
    assert result == "RAM 100 MB"


def test_daemon_get_sessions_empty() -> None:
    """get_sessions returns [] when TranscriptLog returns empty list."""

    class FakeLog:
        def get_sessions(self, last_n: int = 10):
            return []

        def close(self) -> None:
            pass

    daemon = _make_daemon()
    with patch("voiceforge.core.transcript_log.TranscriptLog", FakeLog):
        out = daemon.get_sessions(5)
    assert json.loads(out) == []


def test_daemon_get_session_detail_not_found() -> None:
    """get_session_detail returns {} when session not found."""

    class FakeLog:
        def get_session_detail(self, session_id: int):
            return None

        def close(self) -> None:
            pass

    daemon = _make_daemon()
    with patch("voiceforge.core.transcript_log.TranscriptLog", FakeLog):
        out = daemon.get_session_detail(999)
    assert out == "{}"


def test_daemon_get_indexed_paths_no_db() -> None:
    """get_indexed_paths returns [] when DB file does not exist."""
    daemon = _make_daemon()
    out = daemon.get_indexed_paths()
    assert json.loads(out) == []


def test_daemon_search_rag_empty_query() -> None:
    """search_rag returns [] for empty or whitespace query."""
    daemon = _make_daemon()
    assert daemon.search_rag("") == "[]"
    assert daemon.search_rag("   ") == "[]"


def test_daemon_get_analytics_returns_json() -> None:
    """get_analytics returns JSON from get_stats."""
    daemon = _make_daemon()
    with patch("voiceforge.core.metrics.get_stats", return_value={"total_cost_usd": 0.5, "total_calls": 3}):
        out = daemon.get_analytics("7d")
    data = json.loads(out)
    assert data.get("total_cost_usd") == 0.5
    assert data.get("total_calls") == 3


def test_daemon_get_analytics_fallback_empty_on_error() -> None:
    """get_analytics returns {} on exception."""
    daemon = _make_daemon()
    with patch("voiceforge.core.metrics.get_stats", side_effect=RuntimeError("db gone")):
        out = daemon.get_analytics("30d")
    assert out == "{}"


# --- _retention_purge_at_startup ---


def test_retention_purge_at_startup_no_op_when_zero() -> None:
    """_retention_purge_at_startup does nothing when retention_days is 0."""
    purge_called: list[object] = []

    class FakeLog:
        def purge_before(self, cutoff):
            purge_called.append(cutoff)
            return 0

        def close(self) -> None:
            pass

    cfg = MagicMock()
    cfg.retention_days = 0
    cfg.get_rag_db_path = lambda: "/x"
    with (
        patch("voiceforge.core.daemon.Settings", return_value=cfg),
        patch("voiceforge.core.daemon.ModelManager", return_value=MagicMock()),
        patch("voiceforge.core.daemon.set_model_manager"),
    ):
        daemon = VoiceForgeDaemon(iface=None)
    _retention_purge_at_startup(daemon)
    assert not purge_called


def test_retention_purge_at_startup_calls_purge() -> None:
    """_retention_purge_at_startup calls purge_before when retention_days > 0."""
    purge_called: list[object] = []

    class FakeLog:
        def purge_before(self, cutoff):
            purge_called.append(cutoff)
            return 2

        def close(self) -> None:
            pass

    with patch("voiceforge.core.transcript_log.TranscriptLog", FakeLog):
        cfg = MagicMock()
        cfg.retention_days = 7
        cfg.get_rag_db_path = lambda: "/x"
        with (
            patch("voiceforge.core.daemon.Settings", return_value=cfg),
            patch("voiceforge.core.daemon.ModelManager", return_value=MagicMock()),
            patch("voiceforge.core.daemon.set_model_manager"),
        ):
            daemon = VoiceForgeDaemon(iface=None)
        _retention_purge_at_startup(daemon)
    assert len(purge_called) == 1


# --- _wire_daemon_iface ---


def test_wire_daemon_iface_status_wired() -> None:
    """_wire_daemon_iface wires status so iface._status is daemon.status."""
    iface = DaemonVoiceForgeInterface(
        analyze_fn=lambda s, t: ("", None),
        status_fn=lambda: "idle",
        listen_start_fn=lambda: None,
        listen_stop_fn=lambda: None,
        is_listening_fn=lambda: False,
    )
    daemon = _make_daemon()
    _wire_daemon_iface(iface, daemon)
    with patch("voiceforge.main.get_status_text", return_value="wired-status"):
        assert iface._status() == "wired-status"


def test_daemon_env_flag_already_in_batch99() -> None:
    """_env_flag is covered in test_coverage_hotspots_batch99; smoke here for daemon module."""
    assert _env_flag("NONEXISTENT_VAR_XYZ", default=True) is True
    assert _env_flag("NONEXISTENT_VAR_XYZ", default=False) is False
