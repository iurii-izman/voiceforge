"""Tests for core/telegram_notify (coverage #56). Mocks keyring and urllib."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from voiceforge.core import telegram_notify


def test_get_telegram_chat_id_returns_none_when_keyring_empty() -> None:
    with patch("keyring.get_password", return_value=None):
        assert telegram_notify.get_telegram_chat_id() is None


def test_get_telegram_chat_id_returns_stripped_value() -> None:
    with patch("keyring.get_password", return_value=" 12345 \n"):
        assert telegram_notify.get_telegram_chat_id() == "12345"


def test_get_telegram_chat_id_handles_exception() -> None:
    with patch("keyring.get_password", side_effect=RuntimeError("keyring unavailable")):
        assert telegram_notify.get_telegram_chat_id() is None


def test_set_telegram_chat_id_calls_keyring() -> None:
    with patch("keyring.set_password") as sp:
        telegram_notify.set_telegram_chat_id(12345)
        sp.assert_called_once_with("voiceforge", "telegram_chat_id", "12345")


def test_notify_analyze_done_no_op_without_token() -> None:
    with patch("voiceforge.core.secrets.get_api_key", return_value=None):
        with patch("voiceforge.core.telegram_notify.get_telegram_chat_id", return_value="123"):
            telegram_notify.notify_analyze_done(1, "summary")
    with patch("voiceforge.core.secrets.get_api_key", return_value="token"):
        with patch("voiceforge.core.telegram_notify.get_telegram_chat_id", return_value=None):
            telegram_notify.notify_analyze_done(1, "summary")


def test_notify_analyze_done_sends_request_when_configured() -> None:
    req_captured = []

    class Cm:
        def __enter__(self):
            return type("R", (), {"status": 200})()
        def __exit__(self, *a):
            return None

    def capture_request(req, timeout=10):
        req_captured.append(req)
        return Cm()

    with patch("voiceforge.core.secrets.get_api_key", return_value="fake_token"):
        with patch("voiceforge.core.telegram_notify.get_telegram_chat_id", return_value="999"):
            with patch("voiceforge.core.telegram_notify.urllib.request.urlopen", side_effect=capture_request):
                telegram_notify.notify_analyze_done(42, "Done.")
    assert len(req_captured) == 1
    assert "sendMessage" in req_captured[0].full_url
    assert b"999" in req_captured[0].data
    assert b"Session #42" in req_captured[0].data or b"#42" in req_captured[0].data
