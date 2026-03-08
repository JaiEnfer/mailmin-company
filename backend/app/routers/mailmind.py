from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.pii import redact_pii
from app.core.roles import require_role

from app.integrations.gmail_client import (
    get_message_metadata,
    send_email,
    list_unread,
)
from app.integrations.calendar_client import create_event

from app.models import Approval, Workspace
from app.services.llm import classify_email, draft_reply
from app.services.action_analyzer import analyze_email_for_action
from app.services.store import create_approval, set_approval_status, log_action
from app.services.signature import build_signature

router = APIRouter(prefix="/mailmind", tags=["mailmind"])


def _get_email_text(msg: dict) -> str:
    return (msg.get("body") or msg.get("snippet") or "").strip()


def _parse_email_address(raw: str) -> str:
    if not raw:
        return ""
    if "<" in raw and ">" in raw:
        return raw.split("<", 1)[1].split(">", 1)[0].strip()
    return raw.strip()


def _load_action_payload(a: Approval) -> dict:
    if not a.action_payload:
        return {}
    try:
        return json.loads(a.action_payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid action_payload JSON for this approval")


def _extract_calendar_fields(payload: dict, approval_subject: str = "") -> dict:
    return {
        "title": (payload.get("title") or approval_subject or "Meeting").strip(),
        "start_iso": (payload.get("start_iso") or "").strip(),
        "end_iso": (payload.get("end_iso") or "").strip(),
        "timezone": (payload.get("timezone") or "Europe/Berlin").strip(),
        "attendees": payload.get("attendees", []) or [],
        "description": payload.get("description", "") or "",
    }


def _rebuild_calendar_payload_from_message(
    db: Session,
    workspace_id: int,
    approval: Approval,
) -> dict:
    if not approval.message_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot rebuild calendar payload because message_id is missing.",
        )

    msg = get_message_metadata(db, workspace_id, approval.message_id)
    msg["snippet"] = redact_pii(msg.get("snippet"))

    email_text = _get_email_text(msg)

    classification = classify_email(
        msg.get("from"),
        msg.get("subject"),
        email_text,
    )

    rebuilt = analyze_email_for_action(classification, msg)
    print("REBUILT ACTION DEBUG:", rebuilt)

    if (rebuilt.get("action_type") or "none") != "calendar_create":
        raise HTTPException(
            status_code=400,
            detail="Could not rebuild calendar action from the original email.",
        )

    rebuilt_payload = rebuilt.get("payload") or {}
    fields = _extract_calendar_fields(rebuilt_payload, approval.subject or "Meeting")

    approval.action_payload = json.dumps(
        {
            "title": fields["title"],
            "start_iso": fields["start_iso"],
            "end_iso": fields["end_iso"],
            "timezone": fields["timezone"],
            "attendees": fields["attendees"],
            "description": fields["description"],
        },
        ensure_ascii=False,
    )
    db.commit()
    db.refresh(approval)

    return fields


@router.get("/stats")
def mailmind_stats(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
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
    executed = (
        db.query(Approval)
        .filter(
            Approval.workspace_id == workspace_id,
            Approval.action_type != "none",
            Approval.status.in_(["executed", "sent"]),
        )
        .count()
    )
    noreply = (
        db.query(Approval)
        .filter(Approval.workspace_id == workspace_id, Approval.status == "no_reply")
        .count()
    )

    return {
        "pending": pending,
        "approved": approved,
        "sent": sent,
        "executed": executed,
        "no_reply": noreply,
    }


@router.post("/sync-unread")
def sync_unread(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    unread_items = list_unread(
        db=db,
        workspace_id=workspace_id,
        max_results=limit,
        q="is:unread",
    )

    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    sig = build_signature(ws) if ws else ""

    created = 0
    skipped_existing = 0
    skipped_older_in_thread = 0
    approval_ids: list[int] = []
    message_ids: list[str] = []

    # Keep only the newest unread message per thread
    newest_by_thread: dict[str, dict] = {}

    for it in (unread_items or []):
        message_id = (it or {}).get("id")
        if not message_id:
            continue

        thread_id = ((it or {}).get("thread_id") or (it or {}).get("threadId") or "").strip()
        if not thread_id:
            thread_id = f"msg:{message_id}"

        current_ts = int((it or {}).get("internalDate") or 0)
        existing = newest_by_thread.get(thread_id)

        if not existing:
            newest_by_thread[thread_id] = it
            continue

        existing_ts = int(existing.get("internalDate") or 0)
        if current_ts >= existing_ts:
            newest_by_thread[thread_id] = it

    for thread_id, it in newest_by_thread.items():
        message_id = (it or {}).get("id")
        if not message_id:
            continue

        message_ids.append(message_id)

        # Skip only if THIS EXACT MESSAGE has already been processed
        existing_message_approval = (
            db.query(Approval)
            .filter(
                Approval.workspace_id == workspace_id,
                Approval.message_id == message_id,
            )
            .first()
        )

        if existing_message_approval:
            skipped_existing += 1
            continue

        msg = get_message_metadata(db, workspace_id, message_id)
        msg["snippet"] = redact_pii(msg.get("snippet"))

        email_text = _get_email_text(msg)

        classification = classify_email(
            msg.get("from"),
            msg.get("subject"),
            email_text,
        )

        action = analyze_email_for_action(classification, msg)
        print("ACTION DEBUG:", action)

        action_type = action.get("action_type") or "none"
        action_payload = action.get("payload")
        if action_payload:
            action_payload = json.dumps(action_payload, ensure_ascii=False)

        reply = draft_reply(
            msg.get("from"),
            msg.get("subject"),
            email_text,
        )

        if sig:
            reply = reply.rstrip() + "\n\nBest regards,\n" + sig + "\n"

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
            {
                "approval_id": approval.id,
                "message_id": message_id,
                "thread_id": thread_id,
                "action_type": approval.action_type,
            },
            workspace_id=workspace_id,
        )

    skipped_older_in_thread = max(0, len(unread_items or []) - len(newest_by_thread))

    log_action(
        db,
        "SYNC_UNREAD",
        {
            "fetched": len(unread_items or []),
            "created": created,
            "skipped_existing": skipped_existing,
            "skipped_older_in_thread": skipped_older_in_thread,
        },
        workspace_id=workspace_id,
    )

    return {
        "fetched": len(unread_items or []),
        "created": created,
        "skipped_existing": skipped_existing,
        "skipped_older_in_thread": skipped_older_in_thread,
        "approval_ids": approval_ids,
        "message_ids": message_ids,
    }


@router.get("/approvals")
def approvals_list(status: str | None = None, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    workspace_id = int(user["workspace_id"])
    q = db.query(Approval).filter(Approval.workspace_id == workspace_id).order_by(Approval.id.desc())
    if status:
        q = q.filter(Approval.status == status)
    rows = q.limit(limit).all()
    return {
        "items": [
            {
                "id": a.id,
                "status": a.status,
                "message_id": a.message_id,
                "thread_id": a.thread_id,
                "from": a.from_email,
                "subject": a.subject,
                "draft_reply": a.draft_reply,
                "action_type": a.action_type,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in rows
        ]
    }


@router.post("/approvals/{approval_id}/approve")
def approve(approval_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("admin", "approver"))):
    workspace_id = int(user["workspace_id"])
    a = set_approval_status(db, workspace_id, approval_id, "approved")
    log_action(db, "APPROVED", {"approval_id": approval_id}, workspace_id=workspace_id)
    return {"id": a.id, "status": a.status}


@router.post("/approvals/{approval_id}/reject")
def reject(approval_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("admin", "approver"))):
    workspace_id = int(user["workspace_id"])
    a = set_approval_status(db, workspace_id, approval_id, "rejected")
    log_action(db, "REJECTED", {"approval_id": approval_id}, workspace_id=workspace_id)
    return {"id": a.id, "status": a.status}


@router.post("/approvals/{approval_id}/send")
def send_and_execute(
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

    if a.status == "sent":
        raise HTTPException(status_code=400, detail="This approval was already sent.")

    if a.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Approval status must be 'approved' (current: {a.status})",
        )

    to_email = _parse_email_address(a.from_email or "")

    subject = a.subject or ""
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    event = None
    extra_note = ""

    if a.action_type == "calendar_create":
        payload = _load_action_payload(a)
        fields = _extract_calendar_fields(payload, a.subject or "Meeting")

        if not fields["start_iso"] or not fields["end_iso"]:
            fields = _rebuild_calendar_payload_from_message(db, workspace_id, a)

        if not fields["title"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot create calendar event because title is missing in action payload.",
            )

        if not fields["start_iso"] or not fields["end_iso"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cannot create calendar event because meeting date/time is missing even after re-analysis. "
                    f"start_iso={fields['start_iso']!r}, end_iso={fields['end_iso']!r}, "
                    f"timezone={fields['timezone']!r}"
                ),
            )

        print("SEND CALENDAR PAYLOAD:", {
            "title": fields["title"],
            "start_iso": fields["start_iso"],
            "end_iso": fields["end_iso"],
            "timezone": fields["timezone"],
            "attendees": fields["attendees"],
        })

        event = create_event(
            db=db,
            workspace_id=workspace_id,
            title=fields["title"],
            start_iso=fields["start_iso"],
            end_iso=fields["end_iso"],
            timezone=fields["timezone"],
            attendees=fields["attendees"],
            description=fields["description"],
        )

        try:
            payload["title"] = fields["title"]
            payload["start_iso"] = fields["start_iso"]
            payload["end_iso"] = fields["end_iso"]
            payload["timezone"] = fields["timezone"]
            payload["attendees"] = fields["attendees"]
            payload["description"] = fields["description"]
            payload["event_link"] = event.get("htmlLink")
            a.action_payload = json.dumps(payload, ensure_ascii=False)
            db.commit()
            db.refresh(a)
        except Exception:
            pass

        if event and event.get("htmlLink"):
            extra_note = f"\n\nCalendar event created: {event.get('htmlLink')}\n"

        log_action(
            db,
            "CALENDAR_EVENT_CREATED",
            {"approval_id": a.id, "event": event},
            workspace_id=workspace_id,
        )

    body = (a.draft_reply or "") + extra_note

    sent = send_email(
        db=db,
        workspace_id=workspace_id,
        to_email=to_email,
        subject=subject,
        body=body,
        thread_id=a.thread_id,
        reply_to_message_id=a.message_id,
    )

    a.status = "sent"
    a.sent_message_id = sent.get("id")
    a.sent_thread_id = sent.get("threadId")
    db.commit()
    db.refresh(a)

    log_action(
        db,
        "SENT_EMAIL",
        {"approval_id": a.id, "to": to_email, "sent": sent, "action_type": a.action_type},
        workspace_id=workspace_id,
    )

    return {"id": a.id, "status": a.status, "sent": sent, "event": event}


@router.post("/approvals/{approval_id}/reply")
def send_reply(approval_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("admin", "approver"))):
    workspace_id = int(user["workspace_id"])
    a = db.query(Approval).filter(Approval.id == approval_id, Approval.workspace_id == workspace_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")

    if a.status == "sent":
        raise HTTPException(status_code=400, detail="This approval was already sent.")

    if a.status not in ("approved", "executed"):
        raise HTTPException(status_code=400, detail=f"Status must be approved or executed (current: {a.status})")

    to_email = _parse_email_address(a.from_email or "")

    subject = a.subject or ""
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    extra_note = ""
    if a.action_payload:
        try:
            payload = json.loads(a.action_payload)
            if payload.get("event_link"):
                extra_note = f"\n\nCalendar event created: {payload['event_link']}\n"
        except Exception:
            pass

    body = (a.draft_reply or "") + extra_note

    sent = send_email(
        db=db,
        workspace_id=workspace_id,
        to_email=to_email,
        subject=subject,
        body=body,
        thread_id=a.thread_id,
        reply_to_message_id=a.message_id,
    )

    a.status = "sent"
    a.sent_message_id = sent.get("id")
    a.sent_thread_id = sent.get("threadId")
    db.commit()
    db.refresh(a)

    log_action(db, "SENT_EMAIL", {"approval_id": a.id, "to": to_email, "sent": sent}, workspace_id=workspace_id)

    return {"id": a.id, "status": a.status, "sent": sent}


@router.post("/approvals/{approval_id}/no-reply")
def no_reply(approval_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("admin", "approver"))):
    workspace_id = int(user["workspace_id"])
    a = db.query(Approval).filter(Approval.id == approval_id, Approval.workspace_id == workspace_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")

    if a.status in ("sent", "rejected"):
        raise HTTPException(status_code=400, detail=f"Cannot set no-reply from status: {a.status}")

    a.status = "no_reply"
    db.commit()
    db.refresh(a)
    log_action(db, "NO_REPLY", {"approval_id": a.id, "message_id": a.message_id}, workspace_id=workspace_id)
    return {"id": a.id, "status": a.status}