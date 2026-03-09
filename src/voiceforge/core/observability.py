"""Prometheus metrics for production monitoring. Issue #36: latency, cost, errors. E15 #138: cost anomaly, data dir free."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import structlog
from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram

log = structlog.get_logger()

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
pipeline_step2_total_seconds = Histogram(
    "voiceforge_pipeline_step2_total_seconds",
    "Step2 parallel (diarization + RAG + PII) total duration (#100 stage-level metric)",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 60.0),
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
# Circuit breaker state per model (0=closed, 1=half_open, 2=open). #62
llm_circuit_breaker_state = Gauge(
    "voiceforge_llm_circuit_breaker_state",
    "LLM circuit breaker state (0=closed, 1=half_open, 2=open)",
    ["model"],
)
# E15 #138: cost anomaly (1 if today > threshold × 7-day average)
llm_cost_anomaly = Gauge(
    "voiceforge_llm_cost_anomaly",
    "1 if today LLM cost exceeds cost_anomaly_multiplier × 7-day average",
)
# E15 #138: free bytes on data directory filesystem (for low-disk alert)
data_dir_free_bytes = Gauge(
    "voiceforge_data_dir_free_bytes",
    "Free bytes on VoiceForge data directory filesystem",
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


def record_pipeline_step2_total(seconds: float) -> None:
    """Record step2 (diarization + RAG + PII) total duration. #100."""
    pipeline_step2_total_seconds.observe(seconds)


def record_pipeline_error(step: str) -> None:
    pipeline_errors_total.labels(step=step).inc()


def record_llm_call(model: str, cost_usd: float, success: bool) -> None:
    status = "success" if success else "error"
    llm_calls_total.labels(model=model, status=status).inc()
    if cost_usd > 0:
        llm_cost_usd_total.labels(model=model).inc(cost_usd)


def set_circuit_breaker_states(states: dict[str, int]) -> None:
    """Update circuit breaker gauge from get_circuit_breaker().get_all_states(). #62"""
    for model, state in states.items():
        llm_circuit_breaker_state.labels(model=model).set(state)


def _data_dir_path() -> Path:
    """VoiceForge data directory (parent of metrics.db)."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge"


def update_data_dir_free_bytes() -> None:
    """E15 #138: set voiceforge_data_dir_free_bytes from disk usage of data dir."""
    try:
        path = _data_dir_path()
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        data_dir_free_bytes.set(float(usage.free))
    except OSError as e:
        log.warning("observability.data_dir_usage_failed", path=str(_data_dir_path()), error=str(e))
        data_dir_free_bytes.set(-1.0)


def update_cost_anomaly() -> None:
    """E15 #138: set llm_cost_anomaly (1 if today > multiplier × 7-day avg), log warning when anomaly."""
    try:
        from voiceforge.core.config import Settings
        from voiceforge.core.metrics import get_cost_today, get_stats

        today = get_cost_today()
        stats_7 = get_stats(7)
        total_7 = stats_7.get("total_cost_usd") or 0.0
        avg_7 = total_7 / 7.0 if total_7 else 0.0
        cfg = Settings()
        threshold = cfg.cost_anomaly_multiplier * avg_7
        if avg_7 > 0 and today > threshold:
            llm_cost_anomaly.set(1.0)
            log.warning(
                "observability.cost_anomaly",
                cost_today=today,
                avg_7d=round(avg_7, 4),
                threshold=round(threshold, 4),
                multiplier=cfg.cost_anomaly_multiplier,
            )
        else:
            llm_cost_anomaly.set(0.0)
    except Exception as e:
        log.warning("observability.cost_anomaly_failed", error=str(e))
        llm_cost_anomaly.set(-1.0)
