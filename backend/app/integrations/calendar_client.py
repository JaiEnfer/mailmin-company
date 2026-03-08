from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_oauth import load_credentials_db


def get_calendar_service(db: Session, workspace_id: int):
    creds = load_credentials_db(db, workspace_id)
    if not creds:
        raise RuntimeError("Not authenticated for this workspace. Connect Google in Settings.")
    return build("calendar", "v3", credentials=creds)


def _safe_zoneinfo(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except Exception:
        return ZoneInfo("UTC")


def _normalize_datetime(value: str, timezone: str) -> str:
    """
    Normalize incoming date/datetime into a timezone-aware ISO datetime string
    in the requested timezone.
    Supports:
      - 2026-03-11
      - 2026-03-11T10:00:00
      - 2026-03-11T10:00:00Z
      - 2026-03-11T10:00:00+01:00
    """
    if not value or not value.strip():
        raise ValueError("Datetime value is required.")

    raw = value.strip()
    tz = _safe_zoneinfo(timezone)

    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    # Date-only input -> midnight in requested timezone
    if "T" not in raw:
        dt = datetime.fromisoformat(raw)
        dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=tz)
        return dt.isoformat()

    dt = datetime.fromisoformat(raw)

    # Naive datetime -> assume requested timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        # Aware datetime -> convert into requested timezone
        dt = dt.astimezone(tz)

    return dt.isoformat()


def _build_event_body(
    title: str,
    start_iso: str,
    end_iso: str,
    timezone: str,
    attendees: Optional[List[str]] = None,
    description: str = "",
) -> Dict[str, Any]:
    start_dt = _normalize_datetime(start_iso, timezone)
    end_dt = _normalize_datetime(end_iso, timezone)

    start_obj = datetime.fromisoformat(start_dt)
    end_obj = datetime.fromisoformat(end_dt)

    if end_obj <= start_obj:
        raise ValueError(
            f"End must be after start. start_dt={start_dt}, end_dt={end_dt}"
        )

    body: Dict[str, Any] = {
        "summary": title,
        "description": description or "",
        "start": {
            "dateTime": start_dt,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_dt,
            "timeZone": timezone,
        },
    }

    if attendees:
        body["attendees"] = [{"email": e} for e in attendees if e]

    return body


def _normalize_event_response(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": event.get("id"),
        "htmlLink": event.get("htmlLink"),
        "status": event.get("status"),
        "summary": event.get("summary"),
    }


def is_time_free(
    db: Session,
    workspace_id: int,
    start_iso: str,
    end_iso: str,
    timezone: str = "UTC",
) -> bool:
    service = get_calendar_service(db, workspace_id)

    start_dt = _normalize_datetime(start_iso, timezone)
    end_dt = _normalize_datetime(end_iso, timezone)

    body = {
        "timeMin": start_dt,
        "timeMax": end_dt,
        "timeZone": timezone,
        "items": [{"id": "primary"}],
    }

    resp = service.freebusy().query(body=body).execute()
    busy = resp.get("calendars", {}).get("primary", {}).get("busy", []) or []
    return len(busy) == 0


def create_event(
    db: Session,
    workspace_id: int,
    title: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "UTC",
    attendees: Optional[List[str]] = None,
    description: str = "",
) -> Dict[str, Any]:
    service = get_calendar_service(db, workspace_id)

    body = _build_event_body(
        title=title,
        start_iso=start_iso,
        end_iso=end_iso,
        timezone=timezone,
        attendees=attendees,
        description=description,
    )

    print("Google Calendar create_event body:", body)

    created = service.events().insert(
        calendarId="primary",
        body=body,
        sendUpdates="all" if attendees else "none",
    ).execute()

    return _normalize_event_response(created)


def update_event(
    db: Session,
    workspace_id: int,
    event_id: str,
    title: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "UTC",
    attendees: Optional[List[str]] = None,
    description: str = "",
) -> Dict[str, Any]:
    if not event_id:
        raise ValueError("event_id is required for update_event")

    service = get_calendar_service(db, workspace_id)

    body = _build_event_body(
        title=title,
        start_iso=start_iso,
        end_iso=end_iso,
        timezone=timezone,
        attendees=attendees,
        description=description,
    )

    print("Google Calendar update_event body:", {
        "event_id": event_id,
        "body": body,
    })

    updated = service.events().patch(
        calendarId="primary",
        eventId=event_id,
        body=body,
        sendUpdates="all" if attendees else "none",
    ).execute()

    return _normalize_event_response(updated)


def cancel_event(
    db: Session,
    workspace_id: int,
    event_id: str,
) -> Dict[str, Any]:
    if not event_id:
        raise ValueError("event_id is required for cancel_event")

    service = get_calendar_service(db, workspace_id)

    print("Google Calendar cancel_event:", {"event_id": event_id})

    service.events().delete(
        calendarId="primary",
        eventId=event_id,
        sendUpdates="all",
    ).execute()

    return {
        "id": event_id,
        "htmlLink": None,
        "status": "cancelled",
        "summary": None,
    }