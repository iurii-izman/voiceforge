"""keyring integration — get_api_key, require_api_key, set_env_keys_from_keyring."""

from __future__ import annotations

import inspect
import os

import structlog

log = structlog.get_logger()

_SERVICE = "voiceforge"


def _caller_name() -> str:
    """E17 #140: Module/caller name for audit log (skip this module and metrics)."""
    for frame_info in inspect.stack()[2:6]:
        try:
            name = frame_info.frame.f_globals.get("__name__", "")
            if name and "voiceforge.core.secrets" not in name:
                return name or "unknown"
        except Exception:
            pass
    return "unknown"


def get_api_key(name: str) -> str | None:
    """Get API key from gnome-keyring. Returns None if not found or keyring unavailable.
    E17 #140: Every read is logged to structlog and metrics.db api_key_access table."""
    try:
        import keyring

        value = keyring.get_password(_SERVICE, name) or None
    except Exception as exc:
        log.debug("keyring.get_failed", name=name, error=str(exc))
        value = None
    try:
        from voiceforge.core.metrics import log_api_key_access

        log_api_key_access(key_name=name, operation="read", caller=_caller_name())
    except Exception as e:
        log.debug("api_key.audit_log_failed", name=name, error=str(e))
    return value


def require_api_key(name: str) -> str:
    """Get API key; raise RuntimeError with setup instructions if absent.

    Args:
        name: Key name (anthropic, openai, google, huggingface, …).

    Raises:
        RuntimeError: If key not found in keyring.
    """
    key = get_api_key(name)
    if not key:
        raise RuntimeError(f"API key '{name}' not found in keyring.\nRun: keyring set {_SERVICE} {name}")
    return key


def set_env_keys_from_keyring() -> None:
    """Populate LiteLLM-standard env vars from keyring if not already set.

    Covers ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY.
    Safe to call multiple times; skips already-set variables.
    """
    _mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GEMINI_API_KEY",
    }
    for name, env_var in _mapping.items():
        if not os.environ.get(env_var):
            key = get_api_key(name)
            if key:
                os.environ[env_var] = key
