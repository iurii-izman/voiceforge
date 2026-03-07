"""CalDAV poll: events that started in the last N minutes (keyring: caldav_*). Block 79: create event from session (#95)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from voiceforge.core.secrets import get_api_key

log = structlog.get_logger()

_ICAL_DT_FORMAT = "%Y%m%dT%H%M%SZ"
_ISO_UTC_SUFFIX = "+00:00"

# Keyring key names (see keyring-keys-reference.md)
_CALDAV_URL = "caldav_url"
_CALDAV_USERNAME = "caldav_username"
_CALDAV_PASSWORD = "caldav_password"
_CALENDAR_DEPS_HINT = "Install calendar deps: uv sync --extra calendar"


def _dt_to_aware(dt: Any) -> datetime | None:
    """Convert icalendar dtstart/dtend to timezone-aware datetime for comparison."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    # date-only (all-day): treat as start of day UTC for ordering
    try:
        return datetime.combine(dt, datetime.min.time(), tzinfo=UTC)
    except Exception:
        return None


def _event_dict(comp: Any, cal_name: str, start_dt: datetime, end_dt: datetime | None) -> dict[str, Any]:
    """Build one event dict from icalendar component."""
    summary = str(comp.get("SUMMARY", "") or "").strip() or "(no title)"
    return {
        "summary": summary,
        "start_iso": start_dt.isoformat(),
        "end_iso": end_dt.isoformat() if end_dt else "",
        "calendar_name": cal_name,
    }


def _events_from_calendar(cal: Any, start_range: datetime, end_range: datetime, now: datetime) -> list[dict[str, Any]]:
    """Fetch events from one calendar that started in [start_range, now]. For poll_events."""
    out: list[dict[str, Any]] = []
    try:
        events = cal.date_search(start=start_range, end=end_range, compfilter="VEVENT")
    except Exception as e:
        log.warning("caldav.date_search_failed", calendar=cal.name, error=str(e))
        return out
    cal_name = getattr(cal, "name", None) or ""
    for ev in events:
        comp = getattr(ev, "icalendar_component", None)
        if not comp:
            continue
        start_dt = _dt_to_aware(comp.get("DTSTART"))
        if start_dt is None or start_dt < start_range or start_dt > now:
            continue
        end_dt = _dt_to_aware(comp.get("DTEND"))
        out.append(_event_dict(comp, cal_name, start_dt, end_dt))
    return out


def poll_events_started_in_last(minutes: int = 5) -> tuple[list[dict[str, Any]], str | None]:
    """Poll CalDAV for events that started in the last N minutes.

    Reads caldav_url, caldav_username, caldav_password from keyring (service voiceforge).
    Returns (list of event dicts with summary, start_iso, end_iso, calendar_name), or error message.
    """
    url = get_api_key(_CALDAV_URL)
    username = get_api_key(_CALDAV_USERNAME)
    password = get_api_key(_CALDAV_PASSWORD)
    if not url or not username or not password:
        missing = [k for k, v in [(_CALDAV_URL, url), (_CALDAV_USERNAME, username), (_CALDAV_PASSWORD, password)] if not v]
        return [], f"Missing keyring keys: {', '.join(missing)}. Set: keyring set voiceforge <key>"

    try:
        import caldav
    except ImportError:
        return [], _CALENDAR_DEPS_HINT

    now = datetime.now(UTC)
    start_range = now - timedelta(minutes=minutes)
    end_range = now + timedelta(minutes=1)  # small window to include current moment

    out: list[dict[str, Any]] = []
    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        if not calendars:
            log.debug("caldav.no_calendars")
            return [], None
        for cal in calendars:
            out.extend(_events_from_calendar(cal, start_range, end_range, now))
    except Exception as e:
        log.warning("caldav.poll_failed", error=str(e))
        return [], str(e)

    return out, None


def list_calendars() -> tuple[list[dict[str, Any]], str | None]:
    """List CalDAV calendar names (block 58). Returns (list of {name, url}, error)."""
    url = get_api_key(_CALDAV_URL)
    username = get_api_key(_CALDAV_USERNAME)
    password = get_api_key(_CALDAV_PASSWORD)
    if not url or not username or not password:
        missing = [k for k, v in [(_CALDAV_URL, url), (_CALDAV_USERNAME, username), (_CALDAV_PASSWORD, password)] if not v]
        return [], f"Missing keyring keys: {', '.join(missing)}. Set: keyring set voiceforge <key>"

    try:
        import caldav
    except ImportError:
        return [], _CALENDAR_DEPS_HINT

    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        out = [{"name": getattr(cal, "name", None) or "(no name)", "url": getattr(cal, "url", "") or ""} for cal in calendars]
        return out, None
    except Exception as e:
        log.warning("caldav.list_calendars_failed", error=str(e))
        return [], str(e)


def _candidates_from_calendars(client: Any, now: datetime, end_range: datetime) -> list[tuple[datetime, dict[str, Any]]]:
    """Collect (start_dt, event_dict) from all calendars in range."""
    candidates: list[tuple[datetime, dict[str, Any]]] = []
    principal = client.principal()
    calendars = principal.calendars()
    if not calendars:
        return candidates
    for cal in calendars:
        try:
            events = cal.date_search(start=now, end=end_range, compfilter="VEVENT")
        except Exception as e:
            log.warning("caldav.date_search_failed", calendar=getattr(cal, "name", ""), error=str(e))
            continue
        cal_name = getattr(cal, "name", None) or ""
        for ev in events:
            comp = getattr(ev, "icalendar_component", None)
            if not comp:
                continue
            start_dt = _dt_to_aware(comp.get("DTSTART"))
            if start_dt is None:
                continue
            end_dt = _dt_to_aware(comp.get("DTEND"))
            candidates.append((start_dt, _event_dict(comp, cal_name, start_dt, end_dt)))
    return candidates


def get_upcoming_events(hours_ahead: int = 48) -> tuple[list[dict[str, Any]], str | None]:
    """Fetch events that start from now until now+hours_ahead (for dashboard widget).

    Returns (list of event dicts with summary, start_iso, end_iso, calendar_name), or error message.
    """
    url = get_api_key(_CALDAV_URL)
    username = get_api_key(_CALDAV_USERNAME)
    password = get_api_key(_CALDAV_PASSWORD)
    if not url or not username or not password:
        missing = [k for k, v in [(_CALDAV_URL, url), (_CALDAV_USERNAME, username), (_CALDAV_PASSWORD, password)] if not v]
        return [], f"Missing keyring keys: {', '.join(missing)}. Set: keyring set voiceforge <key>"

    try:
        import caldav
    except ImportError:
        return [], _CALENDAR_DEPS_HINT

    now = datetime.now(UTC)
    end_range = now + timedelta(hours=hours_ahead)
    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        candidates = _candidates_from_calendars(client, now, end_range)
        candidates.sort(key=lambda x: x[0])
        return [ev for _, ev in candidates], None
    except Exception as e:
        log.warning("caldav.upcoming_failed", error=str(e))
        return [], str(e)


def get_next_meeting_context(hours_ahead: int = 24) -> tuple[str, str | None]:
    """Get the next calendar event (from now) as a string for LLM context.

    Reads caldav_* from keyring. Returns (context_string, error).
    context_string is e.g. "Next meeting: Standup, 2025-02-25T10:00:00+00:00–10:15" or "".
    """
    url = get_api_key(_CALDAV_URL)
    username = get_api_key(_CALDAV_USERNAME)
    password = get_api_key(_CALDAV_PASSWORD)
    if not url or not username or not password:
        return "", None  # no keyring: skip calendar, no error

    try:
        import caldav
    except ImportError:
        return "", None  # no calendar extra: skip

    now = datetime.now(UTC)
    end_range = now + timedelta(hours=hours_ahead)
    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        candidates = _candidates_from_calendars(client, now, end_range)
        if not candidates:
            return "", None
        candidates.sort(key=lambda x: x[0])
        first = candidates[0][1]
        parts = [f"Next meeting: {first['summary']}", first["start_iso"]]
        if first.get("end_iso"):
            parts.append(first["end_iso"])
        return " — ".join(parts), None
    except Exception as e:
        log.warning("caldav.next_meeting_failed", error=str(e))
        return "", str(e)


def _iso_to_ical_utc(iso_str: str) -> str:
    """Convert ISO datetime string to iCal format YYYYMMDDTHHMMSSZ (UTC)."""
    if not iso_str or not iso_str.strip():
        return ""
    try:
        s = iso_str.strip().replace("Z", _ISO_UTC_SUFFIX)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.strftime(_ICAL_DT_FORMAT)
    except (ValueError, TypeError):
        return ""


def _ical_escape(text: str) -> str:
    """Escape SUMMARY/DESCRIPTION for iCal: backslash, semicolon, comma, newline."""
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def create_event(
    start_iso: str,
    end_iso: str,
    summary: str,
    description: str = "",
    calendar_url: str | None = None,
) -> tuple[str | None, str | None]:
    """Create a CalDAV event (block 79, #95). Returns (event_uid, error).

    Uses keyring caldav_url, caldav_username, caldav_password. If calendar_url is given,
    uses that calendar; otherwise uses the first calendar from principal.
    """
    url = get_api_key(_CALDAV_URL)
    username = get_api_key(_CALDAV_USERNAME)
    password = get_api_key(_CALDAV_PASSWORD)
    if not url or not username or not password:
        missing = [k for k, v in [(_CALDAV_URL, url), (_CALDAV_USERNAME, username), (_CALDAV_PASSWORD, password)] if not v]
        return None, f"Missing keyring keys: {', '.join(missing)}. Set: keyring set voiceforge <key>"

    try:
        import caldav
    except ImportError:
        return None, _CALENDAR_DEPS_HINT

    start_ical = _iso_to_ical_utc(start_iso)
    end_ical = _iso_to_ical_utc(end_iso)
    if not start_ical or not end_ical:
        return None, "Invalid start_iso or end_iso (expected ISO 8601 datetime)"

    uid = f"voiceforge-{uuid.uuid4().hex}@voiceforge"
    summary_esc = _ical_escape((summary or "").strip() or "VoiceForge session")
    desc_esc = _ical_escape((description or "").strip())

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//VoiceForge//create-event//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{start_ical}",
        f"DTSTART:{start_ical}",
        f"DTEND:{end_ical}",
        f"SUMMARY:{summary_esc}",
    ]
    if desc_esc:
        lines.append(f"DESCRIPTION:{desc_esc}")
    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    ical_str = "\r\n".join(lines)

    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        if calendar_url:
            cal = principal.calendar(cal_url=calendar_url)
        else:
            calendars = principal.calendars()
            if not calendars:
                return None, "No CalDAV calendars found"
            cal = calendars[0]
        cal.add_event(ical_str)
        log.info("caldav.create_event", uid=uid, summary=summary_esc[:80])
        return uid, None
    except Exception as e:
        log.warning("caldav.create_event_failed", error=str(e))
        return None, str(e)
