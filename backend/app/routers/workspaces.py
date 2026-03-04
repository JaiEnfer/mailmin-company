from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.roles import require_role
from app.models import Workspace

router = APIRouter(prefix="/workspace", tags=["workspace"])

class WorkspaceUpdate(BaseModel):
    timezone: str | None = None
    default_meeting_duration_minutes: int | None = None
    company_tone: str | None = None
    auto_execute_actions: bool | None = None

    company_display_name: str | None = None
    company_email: str | None = None
    company_address: str | None = None
    company_phone: str | None = None
    signature_style: str | None = None   # "team"|"name"|"minimal"
    signature_name: str | None = None


@router.get("/me")
def me(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    ws = db.query(Workspace).filter(Workspace.id == int(user["workspace_id"])).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "id": ws.id,
        "name": ws.name,
        "timezone": ws.timezone,
        "default_meeting_duration_minutes": ws.default_meeting_duration_minutes,
        "company_tone": ws.company_tone,
        "auto_execute_actions": ws.auto_execute_actions,
        "google_email": None,
        "company_display_name": ws.company_display_name,
        "company_email": ws.company_email,
        "company_address": ws.company_address,
        "company_phone": ws.company_phone,
        "signature_style": ws.signature_style,
        "signature_name": ws.signature_name,
    }

@router.post("/me")
def update_me(
    payload: WorkspaceUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Only update provided fields
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ws, k, v)

    db.commit()
    db.refresh(ws)

    return {
        "id": ws.id,
        "name": ws.name,
        "timezone": ws.timezone,
        "default_meeting_duration_minutes": ws.default_meeting_duration_minutes,
        "company_tone": ws.company_tone,
        "auto_execute_actions": ws.auto_execute_actions,
        "google_email": getattr(ws, "google_email", None),

        "company_display_name": getattr(ws, "company_display_name", None),
        "company_email": getattr(ws, "company_email", None),
        "company_address": getattr(ws, "company_address", None),
        "company_phone": getattr(ws, "company_phone", None),
        "signature_style": getattr(ws, "signature_style", None),
        "signature_name": getattr(ws, "signature_name", None),
    }