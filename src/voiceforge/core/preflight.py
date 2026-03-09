"""Pre-flight checks: PipeWire, disk space, network (E3 #126)."""

from __future__ import annotations

import shutil
import socket

import structlog

log = structlog.get_logger()


class NetworkUnavailableError(Exception):
    """Raised when LLM API host is unreachable. .i18n_key is the message key."""

    def __init__(self, i18n_key: str) -> None:
        self.i18n_key = i18n_key
        super().__init__(i18n_key)


# Thresholds (bytes)
DISK_WARNING_BYTES = 1 * 1024**3  # 1 GB
DISK_ERROR_BYTES = 200 * 1024**2  # 200 MB
NETWORK_TIMEOUT_SEC = 3

# Model ID prefix -> (host, port) for connectivity check (E6: ollama for zero-config fallback)
_LLM_HOSTS: list[tuple[str, str, int]] = [
    ("anthropic", "api.anthropic.com", 443),
    ("openai", "api.openai.com", 443),
    ("gemini", "generativelanguage.googleapis.com", 443),
    ("ollama", "127.0.0.1", 11434),
]


def check_pipewire() -> str | None:
    """Return None if pw-record is available; else user-facing error message with fix."""
    if shutil.which("pw-record"):
        return None
    return "error.pipewire_not_found"


def check_disk_space(data_dir: str) -> tuple[str | None, str | None]:
    """Check free space under data_dir. Returns (error_message, warning_message).
    error_message: block (e.g. <200MB); warning_message: warn only (e.g. <1GB)."""
    try:
        usage = shutil.disk_usage(data_dir)
        free = usage.free
        if free < DISK_ERROR_BYTES:
            return ("error.no_disk_space", None)
        if free < DISK_WARNING_BYTES:
            return (None, "warning.low_disk_space")
        return (None, None)
    except OSError as e:
        log.warning("preflight.disk_usage_failed", path=data_dir, error=str(e))
        return (None, None)


def check_network_for_llm(model_id: str) -> str | None:
    """Quick socket connect to API host for model_id (timeout 3s).
    Return None if reachable; else i18n key for error (E6: ollama_not_running when using Ollama)."""
    model_lower = (model_id or "").lower()
    matched_prefix: str | None = None
    host_port: tuple[str, int] | None = None
    for prefix, host, port in _LLM_HOSTS:
        if prefix in model_lower:
            matched_prefix = prefix
            host_port = (host, port)
            break
    if not host_port:
        return None
    host, port = host_port
    try:
        sock = socket.create_connection((host, port), timeout=NETWORK_TIMEOUT_SEC)
        sock.close()
        return None
    except OSError as e:
        log.warning("preflight.network_unreachable", host=host, error=str(e))
        return "error.ollama_not_running" if matched_prefix == "ollama" else "error.no_network"
