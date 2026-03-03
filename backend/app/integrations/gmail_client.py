from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.integrations.google_oauth import load_credentials_db


def get_gmail_service(db: Session, workspace_id: int):
    creds = load_credentials_db(db, workspace_id)
    if not creds:
        raise RuntimeError(
            "Not authenticated for this workspace. Visit /auth/google/start?workspace_id=... first."
        )
    return build("gmail", "v1", credentials=creds)


def list_unread(
    db: Session,
    workspace_id: int,
    max_results: int = 10,
    q: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns unread messages metadata.
    Default is "is:unread" (across all inbox tabs), because many emails land in Promotions/Updates.
    You can pass q="is:unread in:inbox" if you want inbox-only behavior.
    """
    service = get_gmail_service(db, workspace_id)

    query = (q or "is:unread").strip()

    resp = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results,
        )
        .execute()
    )

    messages = resp.get("messages", []) or []
    results: List[Dict[str, Any]] = []

    for m in messages:
        msg_id = m.get("id")
        if not msg_id:
            continue

        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        results.append(
            {
                "id": msg.get("id"),
                "threadId": msg.get("threadId"),
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg.get("snippet"),
            }
        )

    return results


def get_message_metadata(db: Session, workspace_id: int, message_id: str) -> Dict[str, Any]:
    service = get_gmail_service(db, workspace_id)
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "To", "Subject", "Date"],
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "from": headers.get("From"),
        "subject": headers.get("Subject"),
        "date": headers.get("Date"),
        "snippet": msg.get("snippet"),
    }

def get_message_reply_headers(db: Session, workspace_id: int, message_id: str) -> Dict[str, str]:
    service = get_gmail_service(db, workspace_id)
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["Message-ID", "Message-Id", "References", "In-Reply-To"],
    ).execute()

    headers = {}
    for h in msg.get("payload", {}).get("headers", []) or []:
        name = (h.get("name") or "").strip().lower()
        val = (h.get("value") or "").strip()
        if name and val:
            headers[name] = val
    return headers


def send_email(
    db: Session,
    workspace_id: int,
    to_email: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    reply_to_message_id: Optional[str] = None,
) -> dict:
    service = get_gmail_service(db, workspace_id)

    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    # Threading headers for replies (more reliable than threadId alone)
    if reply_to_message_id:
        h = get_message_reply_headers(db, workspace_id, reply_to_message_id)
        orig_msgid = h.get("message-id")
        if orig_msgid:
            msg["In-Reply-To"] = orig_msgid
            refs = h.get("References")
            msg["References"] = (refs + " " + orig_msgid).strip() if refs else orig_msgid

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    payload: Dict[str, Any] = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id  # ✅ reply in same chain

    sent = service.users().messages().send(
        userId="me",
        body=payload,
    ).execute()

    return {"id": sent.get("id"), "threadId": sent.get("threadId")}
    
def ensure_unread(db: Session, workspace_id: int, message_id: str) -> None:
    """
    Force the original email to remain unread by re-adding the UNREAD label.
    Requires gmail.modify scope.
    """
    service = get_gmail_service(db, workspace_id)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": ["UNREAD"]},
    ).execute()