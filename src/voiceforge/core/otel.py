"""OpenTelemetry integration (Phase D #71). Optional: enable via VOICEFORGE_OTEL_ENABLED=1 or OTEL_EXPORTER_OTLP_ENDPOINT."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

__all__ = ["get_tracer", "is_enabled", "span"]

_cached_tracer: Any | None = None


def _env_enabled() -> bool:
    return os.environ.get("VOICEFORGE_OTEL_ENABLED", "").strip() in ("1", "true", "yes") or bool(
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    )


def is_enabled() -> bool:
    """True if OTel is configured (env) and SDK is available."""
    if not _env_enabled():
        return False
    try:
        from opentelemetry import trace  # noqa: F401
    except ImportError:
        return False
    return True


class _NoOpSpan:
    """No-op span when OTel is disabled; avoids branching in callers."""

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        # Intentional no-op: no span to end when OTel disabled (Sonar S1186).
        pass


class _NoOpTracer:
    """No-op tracer when OTel disabled; start_as_current_span yields without creating a real span."""

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs: Any) -> Iterator[Any]:
        yield None  # Intentional: no real span when OTel disabled (Sonar S1186).


def _create_tracer() -> Any:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return _NoOpTracer()

    resource = Resource.create({"service.name": "voiceforge"})
    provider = TracerProvider(resource=resource)

    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    except ImportError:
        pass

    trace.set_tracer_provider(provider)
    return trace.get_tracer("voiceforge", "0.2.0")


def get_tracer() -> Any:
    """Return OTel Tracer (or no-op if disabled/unavailable). Service name: voiceforge."""
    global _cached_tracer
    if _cached_tracer is not None:
        return _cached_tracer
    if not _env_enabled():
        _cached_tracer = _NoOpTracer()
        return _cached_tracer
    _cached_tracer = _create_tracer()
    return _cached_tracer


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    """Context manager: create a span when OTel is enabled, else no-op."""
    tr = get_tracer()
    if isinstance(tr, _NoOpTracer):
        yield None
        return
    attrs = {k: v for k, v in attributes.items() if v is not None} or None
    with tr.start_as_current_span(name, attributes=attrs) as s:
        yield s
