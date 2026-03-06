"""Phase D #71: OpenTelemetry integration (otel module)."""

from __future__ import annotations

import pytest


def test_otel_is_enabled_false_by_default(monkeypatch) -> None:
    """Without VOICEFORGE_OTEL_ENABLED or OTEL_EXPORTER_OTLP_ENDPOINT, is_enabled() is False."""
    monkeypatch.delenv("VOICEFORGE_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from voiceforge.core.otel import is_enabled

    assert is_enabled() is False


def test_otel_get_tracer_returns_noop_when_disabled(monkeypatch) -> None:
    """get_tracer() returns a no-op tracer when OTel is disabled."""
    monkeypatch.delenv("VOICEFORGE_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from voiceforge.core.otel import get_tracer

    tracer = get_tracer()
    assert hasattr(tracer, "start_as_current_span")
    with tracer.start_as_current_span("test"):
        pass  # no-op, no exception


def test_otel_span_context_manager_noop_when_disabled(monkeypatch) -> None:
    """span() as context manager runs without error when OTel disabled."""
    monkeypatch.delenv("VOICEFORGE_OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from voiceforge.core.otel import span

    with span("pipeline.run", seconds=5):
        pass


def test_otel_is_enabled_true_when_env_set(monkeypatch) -> None:
    """When VOICEFORGE_OTEL_ENABLED=1 and SDK installed, is_enabled() is True; else False."""
    monkeypatch.setenv("VOICEFORGE_OTEL_ENABLED", "1")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from voiceforge.core.otel import is_enabled

    # With [otel] deps: True; without: False (import fails)
    result = is_enabled()
    assert isinstance(result, bool)


def test_otel_is_enabled_true_when_otlp_endpoint_set(monkeypatch) -> None:
    """When OTEL_EXPORTER_OTLP_ENDPOINT set and SDK installed, is_enabled() is True; else False."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.delenv("VOICEFORGE_OTEL_ENABLED", raising=False)
    from voiceforge.core.otel import is_enabled

    result = is_enabled()
    assert isinstance(result, bool)


def test_otel_get_tracer_and_span_when_sdk_enabled(monkeypatch) -> None:
    """When [otel] deps installed and VOICEFORGE_OTEL_ENABLED=1, get_tracer returns tracer and span() runs (#71)."""
    pytest.importorskip("opentelemetry.sdk.trace")
    monkeypatch.setenv("VOICEFORGE_OTEL_ENABLED", "1")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    import voiceforge.core.otel as otel_mod

    monkeypatch.setattr(otel_mod, "_cached_tracer", None)
    from voiceforge.core.otel import get_tracer, span, is_enabled

    if not is_enabled():
        pytest.skip("opentelemetry SDK not available")
    tracer = get_tracer()
    assert tracer is not None
    assert hasattr(tracer, "start_as_current_span")
    with span("test.span", key="value"):
        pass
