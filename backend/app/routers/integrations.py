from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import Workspace, GoogleToken
from app.services.store import log_action

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google/status")
def google_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    tok = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()

    connected = bool(tok and tok.token_json)
    email = None

    # Prefer workspace.google_email if present
    if ws is not None:
        email = getattr(ws, "google_email", None)

    return {"connected": connected, "email": email}


@router.post("/google/disconnect")
def google_disconnect(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    # delete saved tokens
    tok = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()
    if tok:
        db.delete(tok)

    # clear stored google_email on workspace (if column exists)
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if ws is not None and hasattr(ws, "google_email"):
        ws.google_email = None

    db.commit()

    log_action(
        db,
        "GOOGLE_DISCONNECTED",
        {"workspace_id": workspace_id},
        workspace_id=workspace_id,
    )

    return {"ok": True, "connected": False}