"""W10: Unit tests for daemon, streaming, smart_trigger, model_manager (key scenarios with mocks)."""

from __future__ import annotations

import json
from pathlib import Path
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
    assert data["total_cost_usd"] == 0.5


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
    from voiceforge.stt.transcriber import Segment
    from voiceforge.stt.streaming import StreamingTranscriber

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
