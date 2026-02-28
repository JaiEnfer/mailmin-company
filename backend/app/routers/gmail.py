from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.integrations.gmail_client import list_unread

router = APIRouter(prefix="/gmail", tags=["gmail"])


@router.get("/unread")
def gmail_unread(workspace_id: int, max_results: int = 10, db: Session = Depends(get_db)):
    return {"items": list_unread(db=db, workspace_id=workspace_id, max_results=max_results)}