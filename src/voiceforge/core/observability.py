"""Prometheus metrics for production monitoring. Issue #36: latency, cost, errors."""

from __future__ import annotations

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram

# Histograms: duration in seconds
stt_duration_seconds = Histogram(
    "voiceforge_stt_duration_seconds",
    "STT transcription duration",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)
diarization_duration_seconds = Histogram(
    "voiceforge_diarization_duration_seconds",
    "Diarization (pyannote) duration",
    buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 40.0),
)
rag_query_duration_seconds = Histogram(
    "voiceforge_rag_query_duration_seconds",
    "RAG search duration",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Counters
llm_cost_usd_total = Counter(
    "voiceforge_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model"],
)
llm_calls_total = Counter(
    "voiceforge_llm_calls_total",
    "Total LLM calls",
    ["model", "status"],
)
pipeline_errors_total = Counter(
    "voiceforge_pipeline_errors_total",
    "Pipeline errors by step",
    ["step"],
)


def get_registry() -> CollectorRegistry:
    """Return the default registry used for /metrics."""
    return REGISTRY


def record_stt_duration(seconds: float) -> None:
    stt_duration_seconds.observe(seconds)


def record_diarization_duration(seconds: float) -> None:
    diarization_duration_seconds.observe(seconds)


def record_rag_duration(seconds: float) -> None:
    rag_query_duration_seconds.observe(seconds)


def record_pipeline_error(step: str) -> None:
    pipeline_errors_total.labels(step=step).inc()


def record_llm_call(model: str, cost_usd: float, success: bool) -> None:
    status = "success" if success else "error"
    llm_calls_total.labels(model=model, status=status).inc()
    if cost_usd > 0:
        llm_cost_usd_total.labels(model=model).inc(cost_usd)
