from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.pii import redact_pii
from app.core.roles import require_role

from app.integrations.gmail_client import get_message_metadata, send_email
from app.integrations.calendar_client import create_event

from app.models import Approval
from app.services.llm import classify_email, draft_reply
from app.services.action_analyzer import analyze_email_for_action
from app.services.store import create_approval, set_approval_status, log_action

router = APIRouter(prefix="/mailmind", tags=["mailmind"])


@router.get("/suggest-reply")
def suggest_reply(
    message_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    msg = get_message_metadata(db, workspace_id, message_id)
    msg["snippet"] = redact_pii(msg.get("snippet"))

    classification = classify_email(msg.get("from"), msg.get("subject"), msg.get("snippet"))
    reply = draft_reply(msg.get("from"), msg.get("subject"), msg.get("snippet"))

    return {
        "message": msg,
        "classification": classification,
        "draft_reply": reply,
        "needs_approval": True,
    }


@router.post("/queue")
def queue_suggestion(
    message_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    msg = get_message_metadata(db, workspace_id, message_id)
    msg["snippet"] = redact_pii(msg.get("snippet"))

    classification = classify_email(msg.get("from"), msg.get("subject"), msg.get("snippet"))

    # Action analyzer decides what to do (client-flexible)
    action = analyze_email_for_action(classification, msg)
    action_type = action.get("action_type") or "none"
    action_payload = action.get("payload")

    if action_payload:
        action_payload = json.dumps(action_payload, ensure_ascii=False)

    reply = draft_reply(msg.get("from"), msg.get("subject"), msg.get("snippet"))

    # NOTE: create_approval signature assumed:
    # create_approval(db, workspace_id, message, classification, draft_reply, action_type=..., action_payload=...)
    approval = create_approval(
        db,
        workspace_id,
        msg,
        classification,
        reply,
        action_type=action_type,
        action_payload=action_payload,
    )

    log_action(
        db,
        "QUEUED_APPROVAL",
        {
            "approval_id": approval.id,
            "message_id": message_id,
            "action_type": approval.action_type,
        },
        workspace_id=workspace_id,
    )

    return {
        "approval_id": approval.id,
        "status": approval.status,
        "message_id": approval.message_id,
    }


@router.get("/approvals")
def approvals_list(
    status: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    q = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id)
        .order_by(Approval.id.desc())
    )

    if status:
        q = q.filter(Approval.status == status)

    rows = q.limit(limit).all()

    items = []
    for a in rows:
        items.append(
            {
                "id": a.id,
                "status": a.status,
                "message_id": a.message_id,
                "from": getattr(a, "from_email", None),
                "subject": getattr(a, "subject", None),
                "draft_reply": a.draft_reply,
                "action_type": getattr(a, "action_type", None),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    return {"items": items}


@router.post("/approvals/{approval_id}/approve")
def approve(
    approval_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "approver")),
):
    workspace_id = int(user["workspace_id"])

    try:
        a = set_approval_status(db, workspace_id=workspace_id, approval_id=approval_id, status="approved")
        log_action(db, "APPROVED", {"approval_id": approval_id}, workspace_id=workspace_id)
        return {"id": a.id, "status": a.status}
    except ValueError:
        raise HTTPException(status_code=404, detail="Approval not found")


@router.post("/approvals/{approval_id}/reject")
def reject(
    approval_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "approver")),
):
    workspace_id = int(user["workspace_id"])

    try:
        a = set_approval_status(db, workspace_id=workspace_id, approval_id=approval_id, status="rejected")
        log_action(db, "REJECTED", {"approval_id": approval_id}, workspace_id=workspace_id)
        return {"id": a.id, "status": a.status}
    except ValueError:
        raise HTTPException(status_code=404, detail="Approval not found")


@router.post("/approvals/{approval_id}/send")
def send_approved(
    approval_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "approver")),
):
    workspace_id = int(user["workspace_id"])

    a = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.workspace_id == workspace_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "approved":
        raise HTTPException(status_code=400, detail=f"Approval status must be 'approved' (current: {a.status})")

    # Extract email inside <> if present
    to_raw = a.from_email or ""
    to_email = to_raw
    if "<" in to_raw and ">" in to_raw:
        to_email = to_raw.split("<", 1)[1].split(">", 1)[0].strip()

    # Prefix subject with Re:
    subject = a.subject or ""
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    extra_note = ""
    event = None

    # Execute task action if present
    if a.action_type == "calendar_create" and a.action_payload:
        try:
            payload = json.loads(a.action_payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid action_payload JSON for this approval")

        event = create_event(
            db=db,
            workspace_id=workspace_id,
            title=payload["title"],
            start_iso=payload["start_iso"],
            end_iso=payload["end_iso"],
            timezone=payload.get("timezone", "UTC"),
            attendees=payload.get("attendees", []),
            description=payload.get("description", ""),
        )

        # Store event link back into payload (optional but useful)
        try:
            payload["event_link"] = event.get("htmlLink")
            a.action_payload = json.dumps(payload, ensure_ascii=False)
        except Exception:
            pass

        extra_note = f"\n\nCalendar event created: {event.get('htmlLink')}\n"

        log_action(
            db,
            "CALENDAR_EVENT_CREATED",
            {"approval_id": a.id, "event": event},
            workspace_id=workspace_id,
        )

    body = (a.draft_reply or "") + extra_note
    sent = send_email(db=db, workspace_id=workspace_id, to_email=to_email, subject=subject, body=body)

    a.status = "sent"
    a.sent_message_id = sent.get("id")
    a.sent_thread_id = sent.get("threadId")
    db.commit()
    db.refresh(a)

    log_action(
        db,
        "SENT_EMAIL",
        {"approval_id": approval_id, "to": to_email, "sent": sent, "action_type": a.action_type},
        workspace_id=workspace_id,
    )

    return {"id": a.id, "status": a.status, "sent": sent}