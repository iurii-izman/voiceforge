"""Tests for LLM circuit breaker. Phase B #62."""

from __future__ import annotations

import contextlib
import time

import pytest

from voiceforge.llm.circuit_breaker import (
    STATE_CLOSED,
    STATE_HALF_OPEN,
    STATE_OPEN,
    CircuitBreaker,
    get_circuit_breaker,
    wrap_completion,
)


def test_circuit_breaker_closed_allows_execution() -> None:
    """When state is closed, can_execute returns True."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60.0)
    assert cb.can_execute("model-a") is True
    assert cb.get_state("model-a") == STATE_CLOSED


def test_circuit_breaker_opens_after_threshold_failures() -> None:
    """After failure_threshold consecutive failures, can_execute returns False."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=300.0)
    key = "model-b"
    assert cb.can_execute(key) is True
    cb.record_failure(key)
    cb.record_failure(key)
    assert cb.can_execute(key) is True
    cb.record_failure(key)
    assert cb.get_state(key) == STATE_OPEN
    assert cb.can_execute(key) is False


def test_circuit_breaker_success_resets_failures() -> None:
    """record_success resets state to closed and clears failure count."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=300.0)
    key = "model-c"
    cb.record_failure(key)
    cb.record_failure(key)
    cb.record_success(key)
    assert cb.get_state(key) == STATE_CLOSED
    assert cb.can_execute(key) is True


def test_circuit_breaker_half_open_after_cooldown() -> None:
    """After cooldown, state becomes half_open and one call is allowed."""
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.05)
    key = "model-d"
    cb.record_failure(key)
    cb.record_failure(key)
    assert cb.can_execute(key) is False
    time.sleep(0.06)
    assert cb.can_execute(key) is True
    assert cb.get_state(key) == STATE_HALF_OPEN


def test_circuit_breaker_half_open_failure_opens_again() -> None:
    """On failure in half_open, state goes back to open."""
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.02)
    key = "model-e"
    cb.record_failure(key)
    cb.record_failure(key)
    time.sleep(0.03)
    assert cb.can_execute(key) is True
    cb.record_failure(key)
    assert cb.get_state(key) == STATE_OPEN
    assert cb.can_execute(key) is False


def test_circuit_breaker_get_all_states() -> None:
    """get_all_states returns current state per key."""
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=60.0)
    cb.record_failure("x")
    assert cb.get_all_states() == {"x": STATE_OPEN}
    assert cb.get_state("missing") == STATE_CLOSED


def test_wrap_completion_records_success_and_failure() -> None:
    """Wrapped completion records success on return, failure on exception."""
    cb = get_circuit_breaker()
    ok_key, fail_key = "wrap_ok_key", "wrap_fail_key"

    def fake_completion(**kwargs: object) -> str:
        if kwargs.get("model") == fail_key:
            raise ValueError("simulated")
        return "ok"

    wrapped = wrap_completion(fake_completion)
    wrapped(model=ok_key)
    assert cb.get_state(ok_key) == STATE_CLOSED
    for _ in range(3):
        with contextlib.suppress(ValueError):
            wrapped(model=fail_key)
    assert cb.get_state(fail_key) == STATE_OPEN


def test_wrap_completion_raises_when_circuit_open() -> None:
    """When circuit is open for a model, wrapped completion raises without calling fn."""
    cb = get_circuit_breaker()
    key = "open-model-unique"
    for _ in range(3):
        cb.record_failure(key)
    called: list = []

    def track_completion(**kwargs: object) -> None:
        called.append(kwargs)

    wrapped = wrap_completion(track_completion)
    with pytest.raises(RuntimeError, match="Circuit breaker open"):
        wrapped(model=key)
    assert called == []


def test_get_circuit_breaker_singleton() -> None:
    """get_circuit_breaker returns the same instance."""
    a = get_circuit_breaker()
    b = get_circuit_breaker()
    assert a is b
