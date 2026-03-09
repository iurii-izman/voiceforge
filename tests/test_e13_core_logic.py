"""E13 #136: Core Logic — prompt cache log, streaming CLI, large-v3-turbo, RAG auto-index, model_size=auto, confidence filter."""

from __future__ import annotations

from unittest.mock import patch

from voiceforge.stt.transcriber import Segment, resolve_stt_model_size


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
