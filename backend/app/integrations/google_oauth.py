from __future__ import annotations

import json
from typing import Optional, Dict, Any

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from app.models import GoogleToken

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events"
]

def build_flow(state: Optional[str] = None) -> Flow:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env")

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    return flow


def save_credentials_db(db: Session, workspace_id: int, creds: Credentials) -> None:
    row = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()
    if not row:
        row = GoogleToken(workspace_id=workspace_id)

    row.token = creds.token
    row.refresh_token = creds.refresh_token
    row.token_uri = creds.token_uri
    row.client_id = creds.client_id
    row.client_secret = creds.client_secret
    row.scopes = json.dumps(list(creds.scopes or []))

    db.add(row)
    db.commit()


def load_credentials_db(db: Session, workspace_id: int) -> Optional[Credentials]:
    row = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()
    if not row:
        return None

    scopes = []
    try:
        scopes = json.loads(row.scopes or "[]")
    except Exception:
        scopes = []

    data: Dict[str, Any] = {
        "token": row.token,
        "refresh_token": row.refresh_token,
        "token_uri": row.token_uri,
        "client_id": row.client_id,
        "client_secret": row.client_secret,
        "scopes": scopes,
    }
    return Credentials(**data)