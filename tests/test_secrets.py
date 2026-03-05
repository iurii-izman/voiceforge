"""Tests for core.secrets: get_api_key, require_api_key, set_env_keys_from_keyring. #56"""

from __future__ import annotations

import os

import pytest

from voiceforge.core.secrets import get_api_key, require_api_key, set_env_keys_from_keyring


def test_get_api_key_returns_none_when_keyring_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_api_key returns None when keyring.get_password raises (e.g. backend unavailable)."""
    import keyring as kr

    def raise_os_error(*args: object, **kwargs: object) -> None:
        raise OSError("keyring unavailable")

    monkeypatch.setattr(kr, "get_password", raise_os_error)
    assert get_api_key("anthropic") is None


def test_get_api_key_returns_none_when_keyring_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_api_key returns None when keyring.get_password returns empty string (or None branch)."""
    import keyring as kr

    monkeypatch.setattr(kr, "get_password", lambda service, name: "")
    assert get_api_key("openai") is None


def test_require_api_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_api_key raises RuntimeError with keyring hint when key is absent."""
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: None,
    )
    with pytest.raises(RuntimeError) as exc_info:
        require_api_key("anthropic")
    assert "anthropic" in str(exc_info.value)
    assert "keyring" in str(exc_info.value).lower()
    assert "voiceforge" in str(exc_info.value).lower()


def test_require_api_key_returns_key_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """require_api_key returns the key when get_api_key returns one."""
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: "sk-test-key",
    )
    assert require_api_key("openai") == "sk-test-key"


def test_set_env_keys_from_keyring_sets_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """set_env_keys_from_keyring sets env vars when unset and keyring has key."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    call_count = 0

    def fake_get(name: str) -> str | None:
        nonlocal call_count
        call_count += 1
        if name == "anthropic":
            return "anthropic-key"
        if name == "openai":
            return None
        if name == "google":
            return "google-key"
        return None

    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", fake_get)
    set_env_keys_from_keyring()
    assert os.environ.get("ANTHROPIC_API_KEY") == "anthropic-key"
    assert os.environ.get("OPENAI_API_KEY") is None or "OPENAI_API_KEY" not in os.environ
    assert os.environ.get("GEMINI_API_KEY") == "google-key"


def test_set_env_keys_from_keyring_skips_when_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """set_env_keys_from_keyring does not overwrite existing env vars."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "already-set")
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: "keyring-would-return",
    )
    set_env_keys_from_keyring()
    assert os.environ["ANTHROPIC_API_KEY"] == "already-set"
