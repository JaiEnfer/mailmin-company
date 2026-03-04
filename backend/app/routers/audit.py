from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
def list_audit(limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    workspace_id = int(user["workspace_id"])
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": a.id,
                "action": a.action,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ]
    }