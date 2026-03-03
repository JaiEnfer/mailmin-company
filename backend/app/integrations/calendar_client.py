from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_oauth import load_credentials_db


def get_calendar_service(db: Session, workspace_id: int):
    creds = load_credentials_db(db, workspace_id)
    if not creds:
        raise RuntimeError("Not authenticated for this workspace. Reconnect Google OAuth.")
    return build("calendar", "v3", credentials=creds)


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
    """
    Creates a Calendar event on the connected Google account's PRIMARY calendar.
    Adds a Google Meet link and invites attendees (if provided).
    Note: conflict checking should happen BEFORE calling this (Step 2).
    """
    service = get_calendar_service(db, workspace_id)

    body: Dict[str, Any] = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
    }

    if attendees:
        # keep only non-empty strings
        clean = [e.strip() for e in attendees if isinstance(e, str) and e.strip()]
        if clean:
            body["attendees"] = [{"email": e} for e in clean]

    # ✅ Create Google Meet link
    body["conferenceData"] = {
        "createRequest": {
            "requestId": f"mm-{workspace_id}-{int(datetime.utcnow().timestamp())}",
            "conferenceSolutionKey": {"type": "hangoutsMeet"},
        }
    }

    created = service.events().insert(
        calendarId="primary",
        body=body,
        conferenceDataVersion=1,  # <-- REQUIRED for Meet link
        sendUpdates="all" if attendees else "none",  # email invites if attendees exist
    ).execute()

    meet_link = None
    try:
        meet_link = (
            created.get("conferenceData", {})
            .get("entryPoints", [{}])[0]
            .get("uri")
        )
    except Exception:
        meet_link = None

    return {
        "id": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "status": created.get("status"),
        "meetLink": meet_link,
    }

def is_time_free(
    db: Session,
    workspace_id: int,
    start_iso: str,
    end_iso: str,
    timezone: str = "UTC",
) -> bool:
    """
    Returns True if primary calendar has no conflicts in that window.
    """
    service = get_calendar_service(db, workspace_id)

    body = {
        "timeMin": start_iso,
        "timeMax": end_iso,
        "timeZone": timezone,
        "items": [{"id": "primary"}],
    }

    resp = service.freebusy().query(body=body).execute()
    calendars = resp.get("calendars", {})
    primary = calendars.get("primary", {})
    busy = primary.get("busy", []) or []
    return len(busy) == 0