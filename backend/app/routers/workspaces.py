from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.roles import require_role
from app.models import Workspace

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/me")
def get_workspace_me(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {
        "id": ws.id,
        "name": ws.name,
        "timezone": ws.timezone,
        "default_meeting_duration_minutes": ws.default_meeting_duration_minutes,
        "company_tone": ws.company_tone,
        "auto_execute_actions": ws.auto_execute_actions,
    }


@router.post("/me")
def update_workspace_me(
    timezone: str | None = None,
    default_meeting_duration_minutes: int | None = None,
    company_tone: str | None = None,
    auto_execute_actions: bool | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if timezone is not None:
        ws.timezone = timezone
    if default_meeting_duration_minutes is not None:
        ws.default_meeting_duration_minutes = default_meeting_duration_minutes
    if company_tone is not None:
        ws.company_tone = company_tone
    if auto_execute_actions is not None:
        ws.auto_execute_actions = auto_execute_actions

    db.commit()
    db.refresh(ws)

    return {
        "id": ws.id,
        "name": ws.name,
        "timezone": ws.timezone,
        "default_meeting_duration_minutes": ws.default_meeting_duration_minutes,
        "company_tone": ws.company_tone,
        "auto_execute_actions": ws.auto_execute_actions,
    }