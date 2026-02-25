"""D3 (#48): calendar context for analyze — get_next_meeting_context, pipeline inject."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest


def test_get_next_meeting_context_missing_keyring_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """When CalDAV keyring keys are missing, returns empty string and no error."""
    from voiceforge.calendar.caldav_poll import get_next_meeting_context

    monkeypatch.setattr(
        "voiceforge.calendar.caldav_poll.get_api_key",
        lambda name: None,
    )
    ctx, err = get_next_meeting_context(hours_ahead=24)
    assert ctx == ""
    assert err is None


def test_get_next_meeting_context_with_mock_event_returns_formatted(monkeypatch: pytest.MonkeyPatch) -> None:
    """With mocked CalDAV returning one event, context string contains summary and times."""
    from voiceforge.calendar.caldav_poll import get_next_meeting_context

    def fake_get_api_key(name: str) -> str | None:
        if name == "caldav_url":
            return "https://example.com/dav"
        if name == "caldav_username":
            return "user"
        if name == "caldav_password":
            return "secret"
        return None

    start_dt = datetime(2025, 2, 25, 10, 0, 0, tzinfo=UTC)
    end_dt = datetime(2025, 2, 25, 10, 30, 0, tzinfo=UTC)
    mock_comp = MagicMock()
    mock_comp.get.side_effect = lambda k, default=None: {"DTSTART": start_dt, "DTEND": end_dt, "SUMMARY": "Standup"}.get(
        k, default or ""
    )
    mock_ev = MagicMock(icalendar_component=mock_comp)

    mock_cal = MagicMock()
    mock_cal.name = "Work"
    mock_cal.date_search = MagicMock(return_value=[mock_ev])

    mock_principal = MagicMock()
    mock_principal.calendars = MagicMock(return_value=[mock_cal])
    mock_client = MagicMock()
    mock_client.principal = MagicMock(return_value=mock_principal)

    mock_caldav_module = MagicMock()
    mock_caldav_module.DAVClient = MagicMock(return_value=mock_client)

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", fake_get_api_key)
    with patch.dict(sys.modules, {"caldav": mock_caldav_module}):
        ctx, err = get_next_meeting_context(hours_ahead=24)
    assert err is None
    assert "Next meeting:" in ctx
    assert "Standup" in ctx
    assert "2025-02-25" in ctx
