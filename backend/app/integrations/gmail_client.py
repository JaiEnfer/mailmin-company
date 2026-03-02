from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import List, Dict, Any

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


def list_unread(db: Session, workspace_id: int, max_results: int = 10) -> List[Dict[str, Any]]:
    service = get_gmail_service(db, workspace_id)

    resp = service.users().messages().list(
        userId="me",
        q="is:unread:inbox",
        maxResults=max_results,
    ).execute()

    messages = resp.get("messages", [])
    results: List[Dict[str, Any]] = []

    for m in messages:
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()

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


def send_email(db: Session, workspace_id: int, to_email: str, subject: str, body: str) -> dict:
    service = get_gmail_service(db, workspace_id)

    msg = EmailMessage()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    sent = service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    return {"id": sent.get("id"), "threadId": sent.get("threadId")}