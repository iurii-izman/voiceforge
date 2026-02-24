"""CalDAV poll: events that started in the last N minutes (keyring: caldav_*)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from voiceforge.core.secrets import get_api_key

log = structlog.get_logger()

# Keyring key names (see keyring-keys-reference.md)
_CALDAV_URL = "caldav_url"
_CALDAV_USERNAME = "caldav_username"
_CALDAV_PASSWORD = "caldav_password"


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
        return [], "Install calendar deps: uv sync --extra calendar"

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
            try:
                events = cal.date_search(start=start_range, end=end_range, compfilter="VEVENT")
            except Exception as e:
                log.warning("caldav.date_search_failed", calendar=cal.name, error=str(e))
                continue
            cal_name = getattr(cal, "name", None) or ""
            for ev in events:
                comp = getattr(ev, "icalendar_component", None)
                if not comp:
                    continue
                dtstart = comp.get("DTSTART")
                dtend = comp.get("DTEND")
                start_dt = _dt_to_aware(dtstart)
                end_dt = _dt_to_aware(dtend)
                if start_dt is None:
                    continue
                # Only include events that *started* in [now - minutes, now]
                if start_dt < start_range or start_dt > now:
                    continue
                summary = str(comp.get("SUMMARY", "") or "").strip() or "(no title)"
                out.append(
                    {
                        "summary": summary,
                        "start_iso": start_dt.isoformat(),
                        "end_iso": end_dt.isoformat() if end_dt else "",
                        "calendar_name": cal_name,
                    }
                )
    except Exception as e:
        log.warning("caldav.poll_failed", error=str(e))
        return [], str(e)

    return out, None
