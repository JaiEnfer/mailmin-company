from __future__ import annotations

from typing import Dict, Any, List, Optional
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
    service = get_calendar_service(db, workspace_id)

    body: Dict[str, Any] = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
    }

    if attendees:
        body["attendees"] = [{"email": e} for e in attendees]

    created = service.events().insert(calendarId="primary", body=body).execute()
    return {
        "id": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "status": created.get("status"),
    }