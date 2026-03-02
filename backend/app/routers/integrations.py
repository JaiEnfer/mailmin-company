from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import Workspace
from app.integrations.google_oauth import load_credentials_db

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google/status")
def google_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    google_email = getattr(ws, "google_email", None) if ws else None

    connected = False
    try:
        creds = load_credentials_db(db, workspace_id)
        connected = creds is not None
    except Exception:
        connected = False

    return {"connected": connected, "email": google_email}