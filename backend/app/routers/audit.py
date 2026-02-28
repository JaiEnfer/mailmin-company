from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import AuditLog
from app.core.security import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])
    q = db.query(AuditLog).filter(AuditLog.workspace_id == workspace_id).order_by(AuditLog.id.desc())
    rows = q.limit(limit).all()

    items = []
    for a in rows:
        items.append(
            {
                "id": a.id,
                "action": a.action,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )
    return {"items": items}