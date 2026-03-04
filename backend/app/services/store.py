import json
from sqlalchemy.orm import Session
from app.models import Approval, AuditLog

def log_action(db: Session, action: str, details: dict | None, workspace_id: int):
    row = AuditLog(
        workspace_id=workspace_id,
        action=action,
        details=json.dumps(details or {}, ensure_ascii=False),
    )
    db.add(row)
    db.commit()

def create_approval(
    db: Session,
    workspace_id: int,
    message: dict,
    classification: dict,
    draft_reply: str,
    action_type: str = "none",
    action_payload: str | None = None,
) -> Approval:
    a = Approval(
        message_id=message.get("id"),
        thread_id=message.get("threadId"),
        workspace_id=workspace_id,
        from_email=message.get("from"),
        subject=message.get("subject"),
        snippet=message.get("snippet"),
        classification_label=classification.get("label"),
        classification_confidence=str(classification.get("confidence")),
        classification_reason=classification.get("reason"),
        draft_reply=draft_reply,
        action_type=action_type,
        action_payload=action_payload,
        status="pending",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    log_action(db, "QUEUE_CREATED", {"approval_id": a.id, "message_id": a.message_id}, workspace_id=workspace_id)
    return a

def set_approval_status(db: Session, workspace_id: int, approval_id: int, status: str) -> Approval:
    a = db.query(Approval).filter(Approval.id == approval_id, Approval.workspace_id == workspace_id).first()
    if not a:
        raise ValueError("not found")
    a.status = status
    db.commit()
    db.refresh(a)
    return a