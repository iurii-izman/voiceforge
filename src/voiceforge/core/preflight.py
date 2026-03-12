"""Pre-flight checks: PipeWire, disk space, network (E3 #126)."""

from __future__ import annotations

import shutil
import socket
import subprocess

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


def _list_pactl_nodes(kind: str) -> list[str] | None:
    """Return Pulse/PipeWire node names for `sources` or `sinks`, or None if unavailable."""
    pactl = shutil.which("pactl")
    if not pactl:
        return None
    try:
        proc = subprocess.run(  # nosec B603
            [pactl, "list", "short", kind],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    names: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip():
            names.append(parts[1].strip())
    return names


def _list_wpctl_nodes(kind: str) -> list[str] | None:
    """Return PipeWire node names from `wpctl status`, or None if unavailable."""
    wpctl = shutil.which("wpctl")
    if not wpctl:
        return None
    try:
        proc = subprocess.run(  # nosec B603
            [wpctl, "status"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    header = "Sources:" if kind == "sources" else "Sinks:"
    names: list[str] = []
    in_section = False
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not in_section:
            if line.startswith(header):
                in_section = True
            continue
        if not line or line.startswith("Filters:") or line.startswith("Streams:"):
            break
        item = line.lstrip("* ").strip()
        if ". " not in item:
            continue
        _node_id, rest = item.split(". ", 1)
        name = rest.rsplit(" [", 1)[0].strip()
        if name:
            names.append(name)
    return names or None


def _list_audio_nodes(kind: str) -> list[str] | None:
    """Return audio node names using pactl when available, otherwise wpctl."""
    return _list_pactl_nodes(kind) or _list_wpctl_nodes(kind)


def _is_dummy_node(name: str) -> bool:
    """Return True for dummy/null PipeWire nodes that cannot carry real meeting audio."""
    lowered = (name or "").lower()
    return lowered.startswith("auto_null") or lowered.startswith("null")


def check_pipewire() -> str | None:
    """Return None if PipeWire capture looks usable; else user-facing error message key."""
    if not shutil.which("pw-record"):
        return "error.pipewire_not_found"
    sources = _list_audio_nodes("sources")
    sinks = _list_audio_nodes("sinks")
    if sources is None and sinks is None:
        return None
    real_sources = [name for name in (sources or []) if not _is_dummy_node(name)]
    real_sinks = [name for name in (sinks or []) if not _is_dummy_node(name)]
    if not real_sources and not real_sinks:
        return "error.pipewire_no_audio_devices"
    return None


def get_pipewire_fix_key(err_key: str | None) -> str:
    """Return the most helpful follow-up hint key for a PipeWire preflight error."""
    if err_key == "error.pipewire_no_audio_devices":
        return "error.pipewire_devices_fix"
    return "error.pipewire_fix"


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
