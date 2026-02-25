"""W10: Unit tests for daemon, streaming, smart_trigger, model_manager (key scenarios with mocks)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def test_daemon_get_settings_returns_json_with_expected_keys(tmp_path, monkeypatch) -> None:
    """Daemon get_settings() returns JSON containing model_size, default_llm, privacy_mode, pii_mode."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.model_size = "small"
        mock_cfg.default_llm = "anthropic/claude-haiku-4-5"
        mock_cfg.budget_limit_usd = 75.0
        mock_cfg.smart_trigger = False
        mock_cfg.sample_rate = 16000
        mock_cfg.streaming_stt = False
        mock_cfg.pii_mode = "ON"
        mock_settings.return_value = mock_cfg

        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_settings()
    data = json.loads(out)
    assert data["model_size"] == "small"
    assert data["default_llm"] == "anthropic/claude-haiku-4-5"
    assert data["pii_mode"] == "ON"
    assert data["privacy_mode"] == "ON"


def test_daemon_get_analytics_returns_dict(tmp_path, monkeypatch) -> None:
    """Daemon get_analytics() returns JSON object (from get_stats)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.metrics.get_stats") as mock_get_stats:
            mock_get_stats.return_value = {"total_cost_usd": 0.5, "by_day": []}

            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_analytics("7d")
    data = json.loads(out)
    assert "total_cost_usd" in data
    assert data["total_cost_usd"] == pytest.approx(0.5)


def test_smart_trigger_check_returns_false_when_file_missing() -> None:
    """SmartTrigger.check() returns False when ring file does not exist."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    trigger = SmartTrigger(sample_rate=16000)
    assert trigger.check("/nonexistent/ring.pcm") is False


def test_smart_trigger_check_returns_false_when_file_too_small(tmp_path) -> None:
    """SmartTrigger.check() returns False when ring file has insufficient samples."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * 1000)
    trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0, min_silence_sec=3.0)
    assert trigger.check(str(ring)) is False


def test_model_manager_get_stt_and_llm_ids() -> None:
    """ModelManager returns config model_size and default_llm."""
    from voiceforge.core.model_manager import ModelManager

    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.default_llm = "openai/gpt-4o-mini"
    mgr = ModelManager(cfg)
    assert mgr.get_stt_model_size() == "tiny"
    assert mgr.get_llm_model_id() == "openai/gpt-4o-mini"


def test_model_manager_set_get_global() -> None:
    """set_model_manager / get_model_manager roundtrip."""
    from voiceforge.core.model_manager import get_model_manager, set_model_manager

    set_model_manager(None)
    assert get_model_manager() is None
    obj = MagicMock()
    set_model_manager(obj)
    assert get_model_manager() is obj
    set_model_manager(None)


def test_streaming_transcriber_class_exists() -> None:
    """StreamingTranscriber exists and has expected interface."""
    from voiceforge.stt import streaming

    assert hasattr(streaming, "StreamingTranscriber")


def test_streaming_transcriber_passes_language_to_transcribe() -> None:
    """StreamingTranscriber passes language hint to transcriber.transcribe (Roadmap #9/#7)."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=1.0, text="hello", language="ru", confidence=0.95),
    ]
    chunks: list[tuple[object, object]] = []

    def on_final(seg: object) -> None:
        chunks.append(("final", seg))

    stream = StreamingTranscriber(
        mock_transcriber,
        sample_rate=16000,
        language="ru",
        on_final=on_final,
    )
    audio = np.zeros(200, dtype=np.float32)
    stream.process_chunk(audio, start_offset_sec=0.0)

    mock_transcriber.transcribe.assert_called_once()
    call_kw = mock_transcriber.transcribe.call_args[1]
    assert call_kw.get("language") == "ru"
    assert len(chunks) == 1
    assert chunks[0][0] == "final"


# --- Daemon: more coverage for get_streaming_transcript, get_api_version, get_capabilities, get_sessions/get_session_detail/get_indexed_paths (exception/no file) ---


def test_daemon_get_streaming_transcript_returns_json(tmp_path, monkeypatch) -> None:
    """Daemon get_streaming_transcript() returns JSON with partial and finals."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_streaming_transcript()
    data = json.loads(out)
    assert "partial" in data
    assert "finals" in data
    assert data["partial"] == ""
    assert data["finals"] == []


def test_daemon_get_api_version_and_capabilities(tmp_path, monkeypatch) -> None:
    """Daemon get_api_version() and get_capabilities() return expected strings."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
    assert daemon.get_api_version() == "1.0"
    caps = json.loads(daemon.get_capabilities())
    assert caps["api_version"] == "1.0"
    assert "listen" in caps["features"]
    assert caps["features"]["listen"] is True


def test_daemon_get_sessions_returns_empty_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_sessions() returns [] when TranscriptLog fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.transcript_log.TranscriptLog", side_effect=RuntimeError("no db")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_sessions(10)
    assert out == "[]"


def test_daemon_get_session_detail_returns_empty_obj_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_session_detail() returns {} when TranscriptLog fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.transcript_log.TranscriptLog", side_effect=RuntimeError("no db")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_session_detail(1)
    assert out == "{}"


def test_daemon_get_indexed_paths_returns_empty_when_no_db(tmp_path, monkeypatch) -> None:
    """Daemon get_indexed_paths() returns [] when RAG DB file does not exist."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.get_rag_db_path.return_value = str(tmp_path / "nonexistent_rag.db")
        mock_settings.return_value = mock_cfg
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_indexed_paths()
    assert out == "[]"


def test_daemon_get_analytics_returns_empty_obj_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_analytics() returns {} when get_stats fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.metrics.get_stats", side_effect=RuntimeError("no metrics")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_analytics("7d")
    assert out == "{}"


# --- SmartTrigger: VAD no segments, cooldown, and fired path (mocked) ---


def test_smart_trigger_check_returns_false_when_vad_returns_no_segments(tmp_path) -> None:
    """SmartTrigger.check() returns False when VAD returns no speech segments."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    # File large enough for min_speech + min_silence
    min_samples = int(16000 * (30.0 + 3.0)) * 2
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * min_samples)
    with patch("faster_whisper.vad.get_speech_timestamps", return_value=[]):
        trigger = SmartTrigger(sample_rate=16000)
        assert trigger.check(str(ring)) is False


def test_smart_trigger_check_returns_false_when_speech_too_short(tmp_path) -> None:
    """SmartTrigger.check() returns False when total speech duration < min_speech_sec."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    min_samples = int(16000 * (30.0 + 3.0)) * 2
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * min_samples)
    # Segments that sum to 10s speech (less than 30s)
    with patch(
        "faster_whisper.vad.get_speech_timestamps",
        return_value=[{"start": 0, "end": 160000}],
    ):
        trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0)
        assert trigger.check(str(ring)) is False


def test_smart_trigger_check_returns_true_when_conditions_met(tmp_path) -> None:
    """SmartTrigger.check() returns True when enough speech, silence, and past cooldown."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    # 35s of "audio" (33s speech + 2s trailing would fail silence; we need 33s speech + 4s silence)
    n_samples = 16000 * 37
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * n_samples)
    # Speech 0..33s, then silence 33..37s (4s)
    with patch(
        "faster_whisper.vad.get_speech_timestamps",
        return_value=[{"start": 0, "end": 33 * 16000}],
    ):
        trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0, min_silence_sec=3.0, cooldown_sec=0.0)
        assert trigger.check(str(ring)) is True


# --- Streaming: process_chunk empty, feed + flush (mocked) ---


def test_streaming_process_chunk_empty_array_no_call(tmp_path) -> None:
    """StreamingTranscriber.process_chunk() with empty array does not call transcriber."""
    from voiceforge.stt.streaming import StreamingTranscriber

    mock_transcriber = MagicMock()
    stream = StreamingTranscriber(mock_transcriber, sample_rate=16000)
    stream.process_chunk(np.array([], dtype=np.float32), start_offset_sec=0.0)
    mock_transcriber.transcribe.assert_not_called()


def test_streaming_feed_flushes_when_buffer_full() -> None:
    """StreamingTranscriber.feed() flushes chunk when buffer duration >= chunk_duration."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=1.0, text="hi", language="en", confidence=0.9),
    ]
    finals: list[object] = []

    def on_final(seg: object) -> None:
        finals.append(seg)

    stream = StreamingTranscriber(
        mock_transcriber,
        sample_rate=16000,
        chunk_duration_sec=2.0,
        overlap_sec=0.5,
        on_final=on_final,
    )
    # Feed 2.5s of audio so one chunk is flushed
    n_samples = int(16000 * 2.5)
    stream.feed(np.zeros(n_samples, dtype=np.float32))
    assert mock_transcriber.transcribe.called
    assert len(finals) >= 1
