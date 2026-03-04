"""Request tracing: trace_id in structlog context (Phase B #61)."""

from __future__ import annotations

import uuid

import structlog.contextvars


def bind_trace_id(trace_id: str | None = None) -> str:
    """Bind a trace_id to the current context. Use for each request/command/pipeline run.
    If trace_id is None, generates a new one (16-char hex). Returns the trace_id used."""
    tid = (trace_id or uuid.uuid4().hex[:16]).strip()
    if not tid:
        tid = uuid.uuid4().hex[:16]
    structlog.contextvars.bind_contextvars(trace_id=tid)
    return tid


def clear_trace_context() -> None:
    """Clear context-local structlog context (e.g. at start of request)."""
    structlog.contextvars.clear_contextvars()


def get_trace_id() -> str | None:
    """Return current trace_id from context, or None if not set."""
    return structlog.contextvars.get_contextvars().get("trace_id")
