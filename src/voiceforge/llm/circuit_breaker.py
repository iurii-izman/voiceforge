"""Circuit breaker for LLM providers. Phase B #62: skip provider on consecutive failures."""

from __future__ import annotations

import threading
import time
from typing import Any

import structlog

log = structlog.get_logger()

# States for Prometheus gauge: 0=closed, 1=half_open, 2=open
STATE_CLOSED = 0
STATE_HALF_OPEN = 1
STATE_OPEN = 2


class _CircuitState:
    """Per-key state: closed / open / half_open, failure count, last failure time."""

    __slots__ = ("state", "consecutive_failures", "last_failure_ts")

    def __init__(self) -> None:
        self.state = STATE_CLOSED
        self.consecutive_failures = 0
        self.last_failure_ts: float = 0.0


class CircuitBreaker:
    """
    Circuit breaker per provider/model key.
    After failure_threshold consecutive failures, state becomes open for cooldown_seconds.
    Then half_open: one trial allowed; success -> closed, failure -> open again.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._states: dict[str, _CircuitState] = {}
        self._lock = threading.Lock()

    def can_execute(self, key: str) -> bool:
        """
        Return True if a call is allowed for this key.
        If open and past cooldown, transition to half_open and allow one call.
        """
        with self._lock:
            state = self._states.get(key)
            if state is None:
                return True
            now = time.monotonic()
            if state.state == STATE_CLOSED:
                return True
            if state.state == STATE_OPEN:
                if now - state.last_failure_ts >= self._cooldown_seconds:
                    state.state = STATE_HALF_OPEN
                    log.info(
                        "llm.circuit_breaker.half_open",
                        key=key,
                        cooldown_seconds=self._cooldown_seconds,
                    )
                    return True
                return False
            # half_open: allow exactly one trial
            return True

    def record_success(self, key: str) -> None:
        """Record successful call; reset state to closed."""
        with self._lock:
            state = self._states.get(key)
            if state is None:
                return
            prev = state.state
            state.state = STATE_CLOSED
            state.consecutive_failures = 0
            if prev != STATE_CLOSED:
                log.info("llm.circuit_breaker.closed", key=key)

    def record_failure(self, key: str) -> None:
        """Record failed call; increment count; open if threshold reached."""
        with self._lock:
            now = time.monotonic()
            if key not in self._states:
                self._states[key] = _CircuitState()
            state = self._states[key]
            state.consecutive_failures += 1
            state.last_failure_ts = now
            if state.consecutive_failures >= self._failure_threshold:
                state.state = STATE_OPEN
                log.warning(
                    "llm.circuit_breaker.open",
                    key=key,
                    consecutive_failures=state.consecutive_failures,
                    cooldown_seconds=self._cooldown_seconds,
                )
            elif state.state == STATE_HALF_OPEN:
                state.state = STATE_OPEN
                log.warning(
                    "llm.circuit_breaker.open_after_half_open",
                    key=key,
                    cooldown_seconds=self._cooldown_seconds,
                )

    def get_state(self, key: str) -> int:
        """Return current state for key: STATE_CLOSED, STATE_HALF_OPEN, or STATE_OPEN."""
        with self._lock:
            state = self._states.get(key)
            return state.state if state else STATE_CLOSED

    def get_all_states(self) -> dict[str, int]:
        """Return copy of key -> state for metrics."""
        with self._lock:
            return {k: s.state for k, s in self._states.items()}


# Module-level singleton for LLM calls
_breaker: CircuitBreaker | None = None
_breaker_lock = threading.Lock()


def get_circuit_breaker() -> CircuitBreaker:
    """Return the global circuit breaker instance."""
    global _breaker
    with _breaker_lock:
        if _breaker is None:
            _breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=300.0)
        return _breaker


def _completion_with_breaker(completion_fn: Any, **kwargs: Any) -> Any:
    """
    Wrapper for litellm completion: check breaker for model, record success/failure.
    Raises so that Instructor can try fallback when circuit is open.
    """
    model = kwargs.get("model") or ""
    breaker = get_circuit_breaker()
    if not breaker.can_execute(model):
        log.warning("llm.circuit_breaker.skip", model=model)
        raise RuntimeError(f"Circuit breaker open for model {model}") from None
    try:
        out = completion_fn(**kwargs)
        breaker.record_success(model)
        return out
    except Exception:
        breaker.record_failure(model)
        raise


def wrap_completion(completion_fn: Any) -> Any:
    """Return a completion function wrapped with circuit breaker (for use with Instructor)."""
    def wrapped(**kwargs: Any) -> Any:
        return _completion_with_breaker(completion_fn, **kwargs)
    return wrapped
