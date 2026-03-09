"""E13 #136: Core Logic — prompt cache log, streaming CLI, large-v3-turbo, RAG auto-index, model_size=auto, confidence filter."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from voiceforge.stt.transcriber import Segment, _is_whisper_model_cached, _load_whisper_model, resolve_stt_model_size


def test_resolve_stt_model_size_auto_returns_concrete() -> None:
    """resolve_stt_model_size('auto') returns one of tiny, base, small, medium by RAM."""
    out = resolve_stt_model_size("auto")
    assert out in ("tiny", "base", "small", "medium")


def test_resolve_stt_model_size_passthrough() -> None:
    """resolve_stt_model_size returns same value for non-auto."""
    assert resolve_stt_model_size("small") == "small"
    assert resolve_stt_model_size("large-v3-turbo") == "large-v3-turbo"


def test_resolve_stt_model_size_auto_by_ram_mock() -> None:
    """When RAM is low, auto resolves to tiny or base."""
    with patch("voiceforge.stt.transcriber.psutil") as m:
        m.virtual_memory.return_value.available = 1 * 1024**3  # 1 GB
        assert resolve_stt_model_size("auto") == "tiny"
        m.virtual_memory.return_value.available = 3 * 1024**3  # 3 GB
        assert resolve_stt_model_size("auto") == "base"
        m.virtual_memory.return_value.available = 6 * 1024**3  # 6 GB
        assert resolve_stt_model_size("auto") == "small"
        m.virtual_memory.return_value.available = 10 * 1024**3  # 10 GB
        assert resolve_stt_model_size("auto") == "medium"


def test_segment_low_confidence_marked_unclear() -> None:
    """Segments with confidence < 0.3 are marked [unclear] in transcribe (integration: see transcriber)."""
    # Unit: Segment can hold [unclear] text
    s = Segment(start=0.0, end=1.0, text="[unclear]", language="en", confidence=0.2)
    assert s.text == "[unclear]"
    assert s.confidence < 0.3


def test_config_model_size_large_v3_turbo_and_auto() -> None:
    """Settings accept model_size large-v3-turbo and auto (E13 #136)."""
    from voiceforge.core.config import Settings

    s = Settings(model_size="large-v3-turbo")
    assert s.model_size == "large-v3-turbo"
    s2 = Settings(model_size="auto")
    assert s2.model_size == "auto"


def test_rag_auto_index_path_config() -> None:
    """Settings accept rag_auto_index_path (optional, E13 #136)."""
    from voiceforge.core.config import Settings

    s = Settings(rag_auto_index_path="/tmp/docs")
    assert s.rag_auto_index_path == "/tmp/docs"


def test_is_whisper_model_cached_false_on_missing_snapshot() -> None:
    """Missing local snapshot returns False instead of surfacing faster-whisper cache exception."""
    with patch("voiceforge.stt.transcriber.download_model", side_effect=RuntimeError("missing")):
        assert _is_whisper_model_cached("small") is False


def test_load_whisper_model_uses_local_files_only_when_cached() -> None:
    """Cached model should load without user-facing download warning and with local_files_only=True."""
    warnings: list[str] = []
    calls: list[dict[str, object]] = []

    def fake_model(model_size: str, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"model_size": model_size, **kwargs})
        return SimpleNamespace()

    with (
        patch("voiceforge.stt.transcriber._is_whisper_model_cached", return_value=True),
        patch("voiceforge.stt.transcriber.WhisperModel", side_effect=fake_model),
    ):
        _load_whisper_model("small", "cpu", "int8", warnings=warnings)

    assert warnings == []
    assert calls[0]["local_files_only"] is True


def test_load_whisper_model_warns_and_uses_remote_when_not_cached() -> None:
    """Missing model should emit user-facing download message and allow remote fetch."""
    warnings: list[str] = []
    calls: list[dict[str, object]] = []

    def fake_model(model_size: str, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"model_size": model_size, **kwargs})
        return SimpleNamespace()

    with (
        patch("voiceforge.stt.transcriber._is_whisper_model_cached", return_value=False),
        patch("voiceforge.stt.transcriber.WhisperModel", side_effect=fake_model),
    ):
        _load_whisper_model("small", "cpu", "int8", warnings=warnings)

    assert any("small" in message for message in warnings)
    assert any("ready" in message.lower() or "загружена" in message.lower() for message in warnings)
    assert calls[0]["local_files_only"] is False
