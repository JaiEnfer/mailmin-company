from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.integrations.gmail_client import list_unread

router = APIRouter(prefix="/gmail", tags=["gmail"])


@router.get("/unread")
def unread(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])
    return list_unread(db, workspace_id)