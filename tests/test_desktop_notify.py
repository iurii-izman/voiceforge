"""E1: Desktop notification (notify-send) — no-op when unavailable."""

from __future__ import annotations

import pytest


def test_notify_analyze_done_no_op_when_notify_send_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When notify-send is not in PATH, notify_analyze_done does nothing and does not raise."""
    monkeypatch.setattr("shutil.which", lambda _: None)
    from voiceforge.core.desktop_notify import notify_analyze_done

    notify_analyze_done("Summary text")
    # No exception; subprocess not called
