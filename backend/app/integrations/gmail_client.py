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
        raise RuntimeError("Not authenticated for this workspace. Connect Google in Settings.")
    return build("gmail", "v1", credentials=creds)


def _decode_b64url(data: Optional[str]) -> str:
    if not data:
        return ""
    try:
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_text_from_payload(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body_data = (payload.get("body") or {}).get("data")

    if mime_type == "text/plain" and body_data:
        return _decode_b64url(body_data)

    parts = payload.get("parts") or []
    if parts:
        plain_parts: list[str] = []
        html_parts: list[str] = []

        for part in parts:
            text = _extract_text_from_payload(part)
            if not text:
                continue

            part_type = part.get("mimeType", "")
            if part_type == "text/plain":
                plain_parts.append(text)
            else:
                html_parts.append(text)

        if plain_parts:
            return "\n".join(p for p in plain_parts if p).strip()

        if html_parts:
            return "\n".join(p for p in html_parts if p).strip()

    if body_data:
        return _decode_b64url(body_data)

    return ""


def _headers_to_dict(msg: Dict[str, Any]) -> Dict[str, str]:
    return {
        h["name"]: h["value"]
        for h in msg.get("payload", {}).get("headers", [])
        if h.get("name")
    }


def list_unread(
    db: Session,
    workspace_id: int,
    max_results: int = 10,
    q: Optional[str] = None,
) -> List[Dict[str, Any]]:
    service = get_gmail_service(db, workspace_id)
    query = (q or "is:unread").strip()

    resp = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    messages = resp.get("messages", []) or []

    results: List[Dict[str, Any]] = []
    for m in messages:
        msg_id = m.get("id")
        if not msg_id:
            continue

        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date", "Message-ID", "References"],
        ).execute()

        headers = _headers_to_dict(msg)
        results.append(
            {
                "id": msg.get("id"),
                "threadId": msg.get("threadId"),
                "thread_id": msg.get("threadId"),
                "from": headers.get("From"),
                "to": headers.get("To"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "message_id_header": headers.get("Message-ID"),
                "references": headers.get("References"),
                "snippet": msg.get("snippet"),
                "internalDate": msg.get("internalDate"),
            }
        )

    return results


def get_message_metadata(db: Session, workspace_id: int, message_id: str) -> Dict[str, Any]:
    service = get_gmail_service(db, workspace_id)
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    headers = _headers_to_dict(msg)
    body_text = _extract_text_from_payload(msg.get("payload") or {})

    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "thread_id": msg.get("threadId"),
        "from": headers.get("From"),
        "to": headers.get("To"),
        "subject": headers.get("Subject"),
        "date": headers.get("Date"),
        "message_id_header": headers.get("Message-ID"),
        "references": headers.get("References"),
        "snippet": msg.get("snippet"),
        "body": body_text,
        "internalDate": msg.get("internalDate"),
    }


def read_thread_messages(
    db: Session,
    workspace_id: int,
    thread_id: str,
    max_messages: int = 10,
) -> List[Dict[str, Any]]:
    service = get_gmail_service(db, workspace_id)
    thread = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full",
    ).execute()

    messages = thread.get("messages", []) or []

    normalized: List[Dict[str, Any]] = []
    for msg in messages:
        headers = _headers_to_dict(msg)
        body_text = _extract_text_from_payload(msg.get("payload") or {})

        normalized.append(
            {
                "id": msg.get("id"),
                "threadId": msg.get("threadId"),
                "thread_id": msg.get("threadId"),
                "from": headers.get("From"),
                "to": headers.get("To"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "message_id_header": headers.get("Message-ID"),
                "references": headers.get("References"),
                "snippet": msg.get("snippet"),
                "body": body_text,
                "internalDate": msg.get("internalDate"),
                "labelIds": msg.get("labelIds", []) or [],
            }
        )

    normalized.sort(key=lambda x: int(x.get("internalDate") or 0))
    return normalized[-max_messages:]


def get_message_reply_headers(db: Session, workspace_id: int, message_id: str) -> Dict[str, str]:
    service = get_gmail_service(db, workspace_id)
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["Message-ID", "References"],
    ).execute()

    return _headers_to_dict(msg)


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

    if reply_to_message_id:
        h = get_message_reply_headers(db, workspace_id, reply_to_message_id)
        orig_msgid = h.get("Message-ID")
        if orig_msgid:
            msg["In-Reply-To"] = orig_msgid
            refs = h.get("References")
            msg["References"] = f"{refs} {orig_msgid}".strip() if refs else orig_msgid

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    payload: Dict[str, Any] = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    sent = service.users().messages().send(userId="me", body=payload).execute()
    return {"id": sent.get("id"), "threadId": sent.get("threadId")}


def ensure_unread(db: Session, workspace_id: int, message_id: str) -> None:
    service = get_gmail_service(db, workspace_id)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": ["UNREAD"]},
    ).execute()