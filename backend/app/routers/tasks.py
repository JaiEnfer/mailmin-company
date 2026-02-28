from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.integrations.calendar_client import create_event
from app.services.store import log_action

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/calendar/create")
def calendar_create(
    workspace_id: int,
    title: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "UTC",
    attendees: str = "",
    description: str = "",
    db: Session = Depends(get_db),
):
    attendee_list = [a.strip() for a in attendees.split(",") if a.strip()] if attendees else []

    event = create_event(
        db=db,
        workspace_id=workspace_id,
        title=title,
        start_iso=start_iso,
        end_iso=end_iso,
        timezone=timezone,
        attendees=attendee_list,
        description=description,
    )

    log_action(db, "CALENDAR_EVENT_CREATED", {"event": event, "title": title}, workspace_id=workspace_id)
    return {"event": event}