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


def _normalize_datetime(value: str, timezone: str) -> str:
    """
    Normalize any incoming value into a timezone-aware ISO datetime
    in the requested timezone.
    """
    if not value or not value.strip():
        raise ValueError("Datetime value is required.")

    raw = value.strip()

    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    # Date-only input -> midnight in requested timezone
    if "T" not in raw:
        dt = datetime.fromisoformat(raw)
        dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=tz)
        return dt.isoformat()

    dt = datetime.fromisoformat(raw)

    # If naive, assume it is already in the requested timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        # Convert aware datetime into requested timezone
        dt = dt.astimezone(tz)

    return dt.isoformat()


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

    start_dt = _normalize_datetime(start_iso, timezone)
    end_dt = _normalize_datetime(end_iso, timezone)

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

    print("Google Calendar create_event body:", body)

    created = service.events().insert(
        calendarId="primary",
        body=body,
        sendUpdates="all" if attendees else "none",
    ).execute()

    return {
        "id": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "status": created.get("status"),
    }