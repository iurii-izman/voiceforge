"""keyring integration — get_api_key, require_api_key, set_env_keys_from_keyring."""

from __future__ import annotations

import os

import structlog

log = structlog.get_logger()

_SERVICE = "voiceforge"


def get_api_key(name: str) -> str | None:
    """Get API key from gnome-keyring. Returns None if not found or keyring unavailable."""
    try:
        import keyring

        return keyring.get_password(_SERVICE, name) or None
    except Exception as exc:
        log.debug("keyring.get_failed", name=name, error=str(exc))
        return None


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
