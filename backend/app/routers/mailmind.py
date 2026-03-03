from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.pii import redact_pii
from app.core.roles import require_role

from app.integrations.gmail_client import get_message_metadata, send_email, list_unread, ensure_unread
from app.integrations.calendar_client import create_event

from app.models import Approval
from app.services.llm import classify_email, draft_reply
from app.services.action_analyzer import analyze_email_for_action
from app.services.store import create_approval, set_approval_status, log_action

router = APIRouter(prefix="/mailmind", tags=["mailmind"])


@router.get("/stats")
def mailmind_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Small stats endpoint for the dashboard overview."""
    workspace_id = int(user["workspace_id"])

    pending = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id, Approval.status == "pending")
        .count()
    )
    approved = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id, Approval.status == "approved")
        .count()
    )
    sent = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id, Approval.status == "sent")
        .count()
    )

    return {"pending": pending, "approved": approved, "sent": sent}


@router.post("/sync-unread")
def sync_unread(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    
    workspace_id = int(user["workspace_id"])

    unread = list_unread(db=db, workspace_id=workspace_id, max_results=limit, q="is:unread")

    # list_unread() might return either:
    # 1) {"items": [...]}  OR  2) [...]
    if isinstance(unread, dict):
        items = unread.get("items", []) or []
    elif isinstance(unread, list):
        items = unread
    else:
        items = []

    created = 0
    skipped_existing = 0
    approval_ids: list[int] = []
    message_ids: list[str] = []

    for it in items:
        if isinstance(it, str):
            message_id = it
        else:
            message_id = (it or {}).get("id")

        if not message_id:
            continue

        message_ids.append(message_id)

        
        exists = (
            db.query(Approval)
            .filter(Approval.workspace_id == workspace_id, Approval.message_id == message_id)
            .first()
        )
        if exists:
            skipped_existing += 1
            continue

        msg = get_message_metadata(db, workspace_id, message_id)
        msg["snippet"] = redact_pii(msg.get("snippet"))

        classification = classify_email(msg.get("from"), msg.get("subject"), msg.get("snippet"))

        action = analyze_email_for_action(classification, msg)
        action_type = action.get("action_type") or "none"
        action_payload = action.get("payload")

        if action_payload:
            action_payload = json.dumps(action_payload, ensure_ascii=False)

        reply = draft_reply(msg.get("from"), msg.get("subject"), msg.get("snippet"))

        approval = create_approval(
            db,
            workspace_id,
            msg,
            classification,
            reply,
            action_type=action_type,
            action_payload=action_payload,
        )

        created += 1
        approval_ids.append(approval.id)

        log_action(
            db,
            "SYNC_QUEUED_APPROVAL",
            {"approval_id": approval.id, "message_id": message_id, "action_type": approval.action_type},
            workspace_id=workspace_id,
        )

    log_action(
        db,
        "SYNC_UNREAD",
        {"fetched": len(items), "created": created, "skipped_existing": skipped_existing},
        workspace_id=workspace_id,
    )

    return {
        "fetched": len(items),
        "created": created,
        "skipped_existing": skipped_existing,
        "approval_ids": approval_ids,
        "message_ids": message_ids,
    }


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

    if not message_id or message_id.strip() == "":
        raise HTTPException(status_code=400, detail="Invalid message_id")

    # Prevent duplicates
    exists = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id, Approval.message_id == message_id)
        .first()
    )
    if exists:
        return {
            "approval_id": exists.id,
            "status": exists.status,
            "message_id": exists.message_id,
            "duplicate": True,
        }

    msg = get_message_metadata(db, workspace_id, message_id)
    msg["snippet"] = redact_pii(msg.get("snippet"))

    classification = classify_email(msg.get("from"), msg.get("subject"), msg.get("snippet"))

    action = analyze_email_for_action(classification, msg)
    action_type = action.get("action_type") or "none"
    action_payload = action.get("payload")

    if action_payload:
        action_payload = json.dumps(action_payload, ensure_ascii=False)

    reply = draft_reply(msg.get("from"), msg.get("subject"), msg.get("snippet"))

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
        {"approval_id": approval.id, "message_id": message_id, "action_type": approval.action_type},
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
def execute_action(
    approval_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "approver")),
):
    """
    Execute the approved action ONLY (no email send).
    Keeps original email unread because we do not modify labels.
    """
    workspace_id = int(user["workspace_id"])

    a = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.workspace_id == workspace_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Approval status must be 'approved' (current: {a.status})",
        )

    event = None

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

        # store event link back into payload
        try:
            payload["event_link"] = event.get("htmlLink")
            a.action_payload = json.dumps(payload, ensure_ascii=False)
        except Exception:
            pass

        
        log_action(
            db,
            "CALENDAR_EVENT_CREATED",
            {"approval_id": a.id, "event": event},
            workspace_id=workspace_id,
        )

    # Mark as executed even if there was no action (keeps flow consistent)
    a.status = "executed"
    db.commit()
    db.refresh(a)

    log_action(
        db,
        "EXECUTED_ACTION",
        {"approval_id": a.id, "action_type": a.action_type, "event": event},
        workspace_id=workspace_id,
    )

    return {"id": a.id, "status": a.status, "executed": {"action_type": a.action_type, "event": event}}

@router.post("/approvals/{approval_id}/reply")
def send_reply(
    approval_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "approver")),
):
    """
    Send the draft reply ONLY (no task execution).
    Keeps original email unread because we do not modify labels.
    """
    workspace_id = int(user["workspace_id"])

    a = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.workspace_id == workspace_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")

    # allow replying when approved OR executed
    if a.status not in ("approved", "executed"):
        raise HTTPException(
            status_code=400,
            detail=f"Approval status must be 'approved' or 'executed' (current: {a.status})",
        )

    # Extract email inside <> if present
    to_raw = a.from_email or ""
    to_email = to_raw
    if "<" in to_raw and ">" in to_raw:
        to_email = to_raw.split("<", 1)[1].split(">", 1)[0].strip()

    subject = a.subject or ""
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    extra_note = ""
    if a.action_payload:
        try:
            payload = json.loads(a.action_payload)
            link = payload.get("event_link")
            if link:
                extra_note = f"\n\nCalendar event created: {link}\n"
        except Exception:
            pass
    

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
        {"approval_id": approval_id, "to": to_email, "sent": sent},
        workspace_id=workspace_id,
    )

    # Force original message to remain unread (replying may mark thread read)
    try:
        if a.message_id:
            ensure_unread(db, workspace_id, a.message_id)
    except Exception:
        pass

    return {"id": a.id, "status": a.status, "sent": sent}


@router.post("/approvals/{approval_id}/no-reply")
def no_reply(
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

    # Human decision: can be done from pending/approved/executed
    if a.status in ("sent", "rejected"):
        raise HTTPException(status_code=400, detail=f"Cannot set no-reply from status: {a.status}")

    # Force the original email to remain unread
    try:
        if a.message_id:
            ensure_unread(db, workspace_id, a.message_id)
    except Exception:
        # Don't fail the operation if Gmail modify fails (but in prod we want it working)
        pass

    a.status = "no_reply"
    db.commit()
    db.refresh(a)

    log_action(
        db,
        "NO_REPLY",
        {"approval_id": a.id, "message_id": a.message_id},
        workspace_id=workspace_id,
    )

    return {"id": a.id, "status": a.status}