"""Push notifications to Telegram when analyze completes (keyring: webhook_telegram, telegram_chat_id)."""

from __future__ import annotations

import json
import logging
import urllib.request

_log = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"
_CONTENT_TYPE_JSON = "application/json; charset=utf-8"
_SERVICE = "voiceforge"


def get_telegram_chat_id() -> str | None:
    """Return chat_id for push notifications from keyring, or None."""
    try:
        import keyring

        out = keyring.get_password(_SERVICE, "telegram_chat_id")
        return out.strip() if out else None
    except Exception as e:
        _log.debug("telegram_notify.get_chat_id failed", error=str(e))
        return None


def set_telegram_chat_id(chat_id: int | str) -> None:
    """Store chat_id in keyring for push notifications (e.g. after /subscribe)."""
    try:
        import keyring

        keyring.set_password(_SERVICE, "telegram_chat_id", str(chat_id))
    except Exception as e:
        _log.warning("telegram_notify.set_chat_id failed", error=str(e))


def notify_analyze_done(session_id: int | None, summary: str) -> None:
    """Send a short message to Telegram when analyze completes. No-op if token or chat_id missing."""
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("webhook_telegram")
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        return
    summary_short = (summary or "")[:400].strip() or "—"
    line = f"Analyze done. Session #{session_id}" if session_id else "Analyze done."
    text = f"{line}\n{summary_short}"
    url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", _CONTENT_TYPE_JSON)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status >= 400:
                _log.warning("telegram_notify.send failed", status=r.status, body=r.read())
    except Exception as e:
        _log.warning("telegram_notify.send error", error=str(e))
