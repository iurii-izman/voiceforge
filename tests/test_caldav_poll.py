"""Tests for calendar/caldav_poll (#56): poll_events, helpers, coverage."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest


def test_dt_to_aware_none() -> None:
    """_dt_to_aware(None) returns None."""
    from voiceforge.calendar.caldav_poll import _dt_to_aware

    assert _dt_to_aware(None) is None


def test_dt_to_aware_naive_datetime() -> None:
    """_dt_to_aware(naive datetime) returns UTC-aware."""
    from voiceforge.calendar.caldav_poll import _dt_to_aware

    naive = datetime(2025, 3, 4, 10, 0, 0)
    out = _dt_to_aware(naive)
    assert out is not None
    assert out.tzinfo is UTC
    assert out.year == 2025 and out.month == 3 and out.day == 4


def test_dt_to_aware_aware_datetime() -> None:
    """_dt_to_aware(aware datetime) returns unchanged."""
    from voiceforge.calendar.caldav_poll import _dt_to_aware

    aware = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    assert _dt_to_aware(aware) == aware


def test_dt_to_aware_date_only() -> None:
    """_dt_to_aware(date) returns start of day UTC."""
    from voiceforge.calendar.caldav_poll import _dt_to_aware

    d = date(2025, 3, 4)
    out = _dt_to_aware(d)
    assert out is not None
    assert out.date() == d
    assert out.tzinfo is UTC
    assert out.hour == 0 and out.minute == 0


def test_event_dict_with_end() -> None:
    """_event_dict builds dict with summary, start_iso, end_iso, calendar_name."""
    from voiceforge.calendar.caldav_poll import _event_dict

    start = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    end = datetime(2025, 3, 4, 10, 30, 0, tzinfo=UTC)
    comp = MagicMock()
    comp.get = lambda k, default=None: {"SUMMARY": "Standup"}.get(k, default or "")
    out = _event_dict(comp, "Work", start, end)
    assert out["summary"] == "Standup"
    assert "2025-03-04" in out["start_iso"]
    assert "2025-03-04" in out["end_iso"]
    assert out["calendar_name"] == "Work"


def test_event_dict_no_title() -> None:
    """_event_dict uses '(no title)' when SUMMARY empty."""
    from voiceforge.calendar.caldav_poll import _event_dict

    start = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    comp = MagicMock()
    comp.get = lambda k, default=None: None
    out = _event_dict(comp, "Cal", start, None)
    assert out["summary"] == "(no title)"
    assert out["end_iso"] == ""


def test_events_from_calendar_date_search_raises() -> None:
    """_events_from_calendar returns [] when date_search raises."""
    from voiceforge.calendar.caldav_poll import _events_from_calendar

    cal = MagicMock()
    cal.name = "Work"
    cal.date_search = MagicMock(side_effect=RuntimeError("network"))
    start = datetime(2025, 3, 4, 9, 0, 0, tzinfo=UTC)
    end = datetime(2025, 3, 4, 11, 0, 0, tzinfo=UTC)
    now = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    out = _events_from_calendar(cal, start, end, now)
    assert out == []


def test_events_from_calendar_event_in_range() -> None:
    """_events_from_calendar includes event when start in [start_range, now]."""
    from voiceforge.calendar.caldav_poll import _events_from_calendar

    start_range = datetime(2025, 3, 4, 9, 0, 0, tzinfo=UTC)
    end_range = datetime(2025, 3, 4, 11, 0, 0, tzinfo=UTC)
    now = datetime(2025, 3, 4, 10, 5, 0, tzinfo=UTC)
    ev_start = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    ev_end = datetime(2025, 3, 4, 10, 30, 0, tzinfo=UTC)
    comp = MagicMock()
    comp.get = lambda k, default=None: {"DTSTART": ev_start, "DTEND": ev_end, "SUMMARY": "Meet"}.get(k, default or "")
    mock_ev = MagicMock(icalendar_component=comp)
    cal = MagicMock()
    cal.name = "Work"
    cal.date_search = MagicMock(return_value=[mock_ev])
    out = _events_from_calendar(cal, start_range, end_range, now)
    assert len(out) == 1
    assert out[0]["summary"] == "Meet"
    assert "2025-03-04" in out[0]["start_iso"]


def test_events_from_calendar_skips_no_component() -> None:
    """_events_from_calendar skips event when icalendar_component is None."""
    from voiceforge.calendar.caldav_poll import _events_from_calendar

    cal = MagicMock()
    cal.name = "Work"
    mock_ev = MagicMock(icalendar_component=None)
    cal.date_search = MagicMock(return_value=[mock_ev])
    start = datetime(2025, 3, 4, 9, 0, 0, tzinfo=UTC)
    end = datetime(2025, 3, 4, 11, 0, 0, tzinfo=UTC)
    now = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    out = _events_from_calendar(cal, start, end, now)
    assert out == []


def test_poll_events_missing_keyring(monkeypatch: pytest.MonkeyPatch) -> None:
    """poll_events_started_in_last returns ([], error) when keyring keys missing."""
    from voiceforge.calendar.caldav_poll import poll_events_started_in_last

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", lambda name: None)
    events, err = poll_events_started_in_last(minutes=5)
    assert events == []
    assert err is not None
    assert "Missing keyring" in err


def test_poll_events_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """poll_events_started_in_last returns ([], msg) when caldav not installed."""
    import builtins

    from voiceforge.calendar import caldav_poll

    def fake_key(name: str) -> str:
        if name == "caldav_url":
            return "https://x/"
        if name == "caldav_username":
            return "u"
        return "p"

    monkeypatch.setattr(caldav_poll, "get_api_key", fake_key)
    orig_import = builtins.__import__

    def fail_caldav(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if name == "caldav":
            raise ImportError("No module named 'caldav'")
        return orig_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=fail_caldav):
        events, err = caldav_poll.poll_events_started_in_last(minutes=5)
    assert events == []
    assert err is not None
    assert "calendar" in err.lower() or "caldav" in err.lower()


def test_poll_events_no_calendars(monkeypatch: pytest.MonkeyPatch) -> None:
    """poll_events_started_in_last returns ([], None) when principal has no calendars."""
    from voiceforge.calendar.caldav_poll import poll_events_started_in_last

    def fake_key(name: str) -> str:
        if name == "caldav_url":
            return "https://x/"
        if name == "caldav_username":
            return "u"
        return "p"

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", fake_key)
    mock_principal = MagicMock()
    mock_principal.calendars = MagicMock(return_value=[])
    mock_client = MagicMock()
    mock_client.principal = MagicMock(return_value=mock_principal)
    mock_caldav = MagicMock()
    mock_caldav.DAVClient = MagicMock(return_value=mock_client)
    with patch.dict(sys.modules, {"caldav": mock_caldav}):
        events, err = poll_events_started_in_last(minutes=5)
    assert events == []
    assert err is None


def test_poll_events_client_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """poll_events_started_in_last returns ([], error) when client.principal() raises."""
    from voiceforge.calendar.caldav_poll import poll_events_started_in_last

    def fake_key(name: str) -> str:
        if name == "caldav_url":
            return "https://x/"
        if name == "caldav_username":
            return "u"
        return "p"

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", fake_key)
    mock_client = MagicMock()
    mock_client.principal = MagicMock(side_effect=ConnectionError("refused"))
    mock_caldav = MagicMock()
    mock_caldav.DAVClient = MagicMock(return_value=mock_client)
    with patch.dict(sys.modules, {"caldav": mock_caldav}):
        events, err = poll_events_started_in_last(minutes=5)
    assert events == []
    assert err is not None
    assert "refused" in err


def test_poll_events_success_with_event(monkeypatch: pytest.MonkeyPatch) -> None:
    """poll_events_started_in_last returns (events, None) when calendars return one event in range."""
    from datetime import timedelta

    from voiceforge.calendar.caldav_poll import poll_events_started_in_last

    def fake_key(name: str) -> str:
        if name == "caldav_url":
            return "https://x/"
        if name == "caldav_username":
            return "u"
        return "p"

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", fake_key)
    now = datetime.now(UTC)
    start_dt = now - timedelta(minutes=2)
    end_dt = now + timedelta(minutes=30)
    comp = MagicMock()
    comp.get = lambda k, default=None: {"DTSTART": start_dt, "DTEND": end_dt, "SUMMARY": "Sync"}.get(k, default or "")
    mock_ev = MagicMock(icalendar_component=comp)
    mock_cal = MagicMock()
    mock_cal.name = "Work"
    mock_cal.date_search = MagicMock(return_value=[mock_ev])
    principal = MagicMock()
    principal.calendars = MagicMock(return_value=[mock_cal])
    mock_client = MagicMock()
    mock_client.principal = MagicMock(return_value=principal)
    mock_caldav = MagicMock()
    mock_caldav.DAVClient = MagicMock(return_value=mock_client)
    with patch.dict(sys.modules, {"caldav": mock_caldav}):
        events, err = poll_events_started_in_last(minutes=5)
    assert err is None
    assert len(events) == 1
    assert events[0]["summary"] == "Sync"


def test_candidates_from_calendars_no_calendars() -> None:
    """_candidates_from_calendars returns [] when no calendars."""
    from voiceforge.calendar.caldav_poll import _candidates_from_calendars

    client = MagicMock()
    client.principal = MagicMock(return_value=MagicMock(calendars=MagicMock(return_value=[])))
    now = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    end = datetime(2025, 3, 4, 12, 0, 0, tzinfo=UTC)
    out = _candidates_from_calendars(client, now, end)
    assert out == []


def test_candidates_from_calendars_one_event() -> None:
    """_candidates_from_calendars returns list of (start_dt, event_dict)."""
    from voiceforge.calendar.caldav_poll import _candidates_from_calendars

    start_dt = datetime(2025, 3, 4, 11, 0, 0, tzinfo=UTC)
    end_dt = datetime(2025, 3, 4, 11, 30, 0, tzinfo=UTC)
    comp = MagicMock()
    comp.get = lambda k, default=None: {"DTSTART": start_dt, "DTEND": end_dt, "SUMMARY": "Sync"}.get(k, default or "")
    mock_ev = MagicMock(icalendar_component=comp)
    mock_cal = MagicMock()
    mock_cal.name = "Work"
    mock_cal.date_search = MagicMock(return_value=[mock_ev])
    principal = MagicMock()
    principal.calendars = MagicMock(return_value=[mock_cal])
    client = MagicMock()
    client.principal = MagicMock(return_value=principal)
    now = datetime(2025, 3, 4, 10, 0, 0, tzinfo=UTC)
    end_range = datetime(2025, 3, 4, 14, 0, 0, tzinfo=UTC)
    out = _candidates_from_calendars(client, now, end_range)
    assert len(out) == 1
    assert out[0][0] == start_dt
    assert out[0][1]["summary"] == "Sync"


# --- create_event (block 79, #95) ---


def test_iso_to_ical_utc_valid() -> None:
    """_iso_to_ical_utc converts ISO string to YYYYMMDDTHHMMSSZ."""
    from voiceforge.calendar.caldav_poll import _iso_to_ical_utc

    assert _iso_to_ical_utc("2025-03-07T10:00:00+00:00") == "20250307T100000Z"
    assert _iso_to_ical_utc("2025-03-07T10:00:00Z") == "20250307T100000Z"


def test_iso_to_ical_utc_invalid() -> None:
    """_iso_to_ical_utc returns '' for invalid or empty input."""
    from voiceforge.calendar.caldav_poll import _iso_to_ical_utc

    assert _iso_to_ical_utc("") == ""
    assert _iso_to_ical_utc("not-a-date") == ""


def test_ical_escape() -> None:
    """_ical_escape escapes backslash, semicolon, comma, newline."""
    from voiceforge.calendar.caldav_poll import _ical_escape

    assert _ical_escape("a;b,c") == "a\\;b\\,c"
    assert _ical_escape("a\nb") == "a\\nb"
    assert _ical_escape("a\\b") == "a\\\\b"


def test_create_event_missing_keyring(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_event returns (None, error) when keyring keys missing (#95)."""
    from voiceforge.calendar.caldav_poll import create_event

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", lambda name: None)
    uid, err = create_event("2025-03-07T10:00:00Z", "2025-03-07T11:00:00Z", "Test", "")
    assert uid is None
    assert err is not None
    assert "keyring" in err.lower() or "missing" in err.lower()


def test_create_event_invalid_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_event returns (None, error) for invalid start/end ISO."""
    from voiceforge.calendar.caldav_poll import create_event

    monkeypatch.setattr(
        "voiceforge.calendar.caldav_poll.get_api_key",
        lambda n: "x" if n in ("caldav_url", "caldav_username", "caldav_password") else None,
    )
    uid, err = create_event("", "2025-03-07T11:00:00Z", "Test", "")
    assert uid is None
    assert err is not None
    assert "invalid" in err.lower() or "start" in err.lower() or "end" in err.lower()


def test_create_event_success_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_event returns (uid, None) when cal.add_event succeeds (#95)."""
    pytest.importorskip("caldav")
    from voiceforge.calendar.caldav_poll import create_event

    def fake_key(name: str) -> str | None:
        if name == "caldav_url":
            return "https://cal.example.com"
        if name == "caldav_username":
            return "user"
        return "secret"

    monkeypatch.setattr("voiceforge.calendar.caldav_poll.get_api_key", fake_key)
    mock_cal = MagicMock()
    mock_principal = MagicMock()
    mock_principal.calendars = MagicMock(return_value=[mock_cal])
    mock_principal.calendar = MagicMock(return_value=mock_cal)
    mock_client = MagicMock()
    mock_client.principal = MagicMock(return_value=mock_principal)

    def fake_dav_client(*args: object, **kwargs: object) -> MagicMock:
        return mock_client

    with patch("caldav.DAVClient", fake_dav_client):
        uid, err = create_event(
            "2025-03-07T10:00:00Z",
            "2025-03-07T11:00:00Z",
            "VoiceForge session 1",
            "Action items here",
        )
    assert err is None
    assert uid is not None
    assert "voiceforge-" in uid and "@voiceforge" in uid
    mock_cal.add_event.assert_called_once()
    call_ical = mock_cal.add_event.call_args[0][0]
    assert "BEGIN:VEVENT" in call_ical
    assert "DTSTART:20250307T100000Z" in call_ical
    assert "SUMMARY:" in call_ical
    assert "DESCRIPTION:" in call_ical
