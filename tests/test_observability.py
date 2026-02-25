"""Tests for core/observability (Prometheus metrics). Issue #36."""

from __future__ import annotations

from voiceforge.core import observability


def test_record_stt_duration() -> None:
    observability.record_stt_duration(2.5)
    # No raise; metric registered in default REGISTRY


def test_record_diarization_duration() -> None:
    observability.record_diarization_duration(5.0)


def test_record_rag_duration() -> None:
    observability.record_rag_duration(0.1)


def test_record_pipeline_error() -> None:
    observability.record_pipeline_error("stt")
    observability.record_pipeline_error("rag")


def test_record_llm_call() -> None:
    observability.record_llm_call("anthropic/claude-haiku-4-5", 0.001, success=True)
    observability.record_llm_call("openai/gpt-4o-mini", 0.0, success=False)


def test_metrics_expose_voiceforge_metrics() -> None:
    """Generate_latest returns bytes containing our metric names."""
    from prometheus_client import generate_latest

    body = generate_latest()
    assert isinstance(body, bytes)
    text = body.decode("utf-8")
    assert "voiceforge_stt_duration_seconds" in text or "voiceforge_llm_calls_total" in text
