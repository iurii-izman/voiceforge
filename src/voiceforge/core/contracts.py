"""Shared CLI/IPC contract helpers."""

from __future__ import annotations

import json
from typing import Any


class BudgetExceeded(Exception):
    """Raised when daily LLM budget limit is exceeded (#38)."""

    def __init__(self, message: str = "Daily LLM budget exceeded") -> None:
        self.message = message
        super().__init__(message)


CLI_SCHEMA_VERSION = "1.0"
IPC_SCHEMA_VERSION = "1.0"


def build_error_payload(
    *,
    schema_version: str,
    code: str,
    message: str,
    retryable: bool = False,
    category: str = "runtime",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "category": category,
            "details": details or {},
        },
    }
    return payload


def build_success_payload(*, schema_version: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "ok": True,
        "data": data,
    }


def build_cli_error_payload(
    code: str,
    message: str,
    retryable: bool = False,
    category: str = "runtime",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_error_payload(
        schema_version=CLI_SCHEMA_VERSION,
        code=code,
        message=message,
        retryable=retryable,
        category=category,
        details=details,
    )


def build_cli_success_payload(data: dict[str, Any]) -> dict[str, Any]:
    return build_success_payload(schema_version=CLI_SCHEMA_VERSION, data=data)


def build_ipc_error_json(
    code: str,
    message: str,
    retryable: bool = False,
    category: str = "runtime",
    details: dict[str, Any] | None = None,
) -> str:
    return json.dumps(
        build_error_payload(
            schema_version=IPC_SCHEMA_VERSION,
            code=code,
            message=message,
            retryable=retryable,
            category=category,
            details=details,
        ),
        ensure_ascii=False,
    )


def build_ipc_success_json(data: dict[str, Any]) -> str:
    return json.dumps(build_success_payload(schema_version=IPC_SCHEMA_VERSION, data=data), ensure_ascii=False)


def wrap_ipc_json_payload(key: str, payload: str) -> str:
    """Wrap JSON-like payload into an IPC envelope while preserving parsed data."""
    try:
        parsed = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return build_ipc_success_json({key: payload})
    return build_ipc_success_json({key: parsed})


def extract_error_message(payload: str, legacy_prefix: str = "Ошибка:") -> str | None:
    """Return user-facing error message from legacy text or structured envelope."""
    try:
        parsed = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return payload if payload.startswith(legacy_prefix) else None
    if not isinstance(parsed, dict):
        return payload if payload.startswith(legacy_prefix) else None
    if isinstance(parsed.get("error"), dict):
        err = parsed["error"]
        return str(err.get("message") or "Ошибка выполнения.")
    return payload if payload.startswith(legacy_prefix) else None
