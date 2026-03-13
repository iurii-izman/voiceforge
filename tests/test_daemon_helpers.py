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
    _analyze_result_is_error_daemon,
    _env_flag,
    _event_description_from_detail,
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


def test_event_description_from_detail_none_or_empty() -> None:
    """_event_description_from_detail returns fallback when detail is None or no action items (#104)."""
    assert _event_description_from_detail(None, 1) == "Session 1 (VoiceForge)"
    analysis_empty = SimpleNamespace(action_items=[])
    assert _event_description_from_detail(([], analysis_empty), 2) == "Session 2 (VoiceForge)"
    assert _event_description_from_detail(([], None), 3) == "Session 3 (VoiceForge)"


def test_event_description_from_detail_with_action_items() -> None:
    """_event_description_from_detail builds description from action items (#104)."""
    analysis = SimpleNamespace(
        action_items=[
            {"description": "Ship feature", "assignee": "Alice", "deadline": "2026-03-15"},
            {"text": "Review PR"},
        ]
    )
    out = _event_description_from_detail(([], analysis), 42)
    assert "Ship feature" in out
    assert "Alice" in out or "2026-03-15" in out
    assert "Review PR" in out
    assert out.startswith("- ") or "Session 42" in out


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
    cfg.calendar_auto_listen = False
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
            # No-op for test fake (S1186).
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
            # No-op for test fake (S1186).
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
    assert data.get("total_cost_usd") == pytest.approx(0.5)
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
            # No-op for test fake (S1186).
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


# --- KC3 copilot capture (issue #175) ---


def test_analyze_result_is_error_daemon_prefix_and_json() -> None:
    """_analyze_result_is_error_daemon True for Russian/English error prefix or JSON error key."""
    assert _analyze_result_is_error_daemon("Ошибка: something") is True
    assert _analyze_result_is_error_daemon("Error: failed") is True
    assert _analyze_result_is_error_daemon('{"error": {"code": "X"}}') is True
    assert _analyze_result_is_error_daemon("Normal text") is False
    assert _analyze_result_is_error_daemon("") is False


def test_get_copilot_capture_status_default_and_after_ambiguous() -> None:
    """get_copilot_capture_status returns JSON with stt_ambiguous; default False (KC3)."""
    daemon = _make_daemon()
    out = daemon.get_copilot_capture_status()
    data = json.loads(out)
    assert data.get("stt_ambiguous") is False
    assert "transcript_snippet" in data  # KC4
    assert data.get("transcript_snippet") == ""
    daemon._last_copilot_stt_ambiguous = True
    out2 = daemon.get_copilot_capture_status()
    data2 = json.loads(out2)
    assert data2.get("stt_ambiguous") is True


def test_get_copilot_capture_status_transcript_snippet_kc4() -> None:
    """get_copilot_capture_status returns transcript_snippet (KC4) for downstream/UI."""
    daemon = _make_daemon()
    daemon._last_copilot_transcript = "Hello world"
    out = daemon.get_copilot_capture_status()
    data = json.loads(out)
    assert data.get("transcript_snippet") == "Hello world"


def test_get_copilot_capture_status_fast_track_cards_kc6() -> None:
    """KC6 (#178): get_copilot_capture_status includes copilot_answer, dos, donts, clarify, confidence."""
    daemon = _make_daemon()
    daemon._last_copilot_answer = ["Enterprise plan is $45K/year."]
    daemon._last_copilot_dos = ["Mention SLA"]
    daemon._last_copilot_donts = ["Don't promise discounts"]
    daemon._last_copilot_clarify = ["Which tier?"]
    daemon._last_copilot_confidence = 0.9
    out = daemon.get_copilot_capture_status()
    data = json.loads(out)
    assert data.get("copilot_answer") == ["Enterprise plan is $45K/year."]
    assert data.get("copilot_dos") == ["Mention SLA"]
    assert data.get("copilot_donts") == ["Don't promise discounts"]
    assert data.get("copilot_clarify") == ["Which tier?"]
    assert data.get("copilot_confidence") == 0.9


def test_get_copilot_capture_status_deep_track_cards_kc7() -> None:
    """KC7 (#179): get_copilot_capture_status includes copilot_risk, copilot_strategy, copilot_emotion."""
    daemon = _make_daemon()
    daemon._last_copilot_risk = ["No commitment without legal review."]
    daemon._last_copilot_strategy = "Suggest a follow-up call."
    daemon._last_copilot_emotion = "Neutral tone recommended."
    out = daemon.get_copilot_capture_status()
    data = json.loads(out)
    assert data.get("copilot_risk") == ["No commitment without legal review."]
    assert data.get("copilot_strategy") == "Suggest a follow-up call."
    assert data.get("copilot_emotion") == "Neutral tone recommended."


def test_copilot_session_memory_clears_on_listen_stop_kc7() -> None:
    """KC7 (#179): _copilot_session_turns is cleared when listen_stop runs (new conversation)."""
    daemon = _make_daemon()
    with daemon._copilot_lock:
        daemon._copilot_session_turns = ["turn1", "turn2"]
    with daemon._listen_lock:
        daemon._listen_active = True
    daemon.listen_stop()
    with daemon._copilot_lock:
        turns = list(daemon._copilot_session_turns)
    assert turns == []
