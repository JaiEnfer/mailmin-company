import os, json
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session
from app.models import GoogleToken, Workspace

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
]

def build_flow(state: Optional[str] = None) -> Flow:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
        raise RuntimeError("Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/GOOGLE_REDIRECT_URI in env")

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

def save_credentials_db(db: Session, workspace_id: int, creds: Credentials):
    token_json = creds.to_json()
    row = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()
    if row:
        row.token_json = token_json
    else:
        row = GoogleToken(workspace_id=workspace_id, token_json=token_json)
        db.add(row)
    db.commit()

def load_credentials_db(db: Session, workspace_id: int) -> Optional[Credentials]:
    row = db.query(GoogleToken).filter(GoogleToken.workspace_id == workspace_id).first()
    if not row:
        return None
    data = json.loads(row.token_json)
    return Credentials.from_authorized_user_info(data)

def set_workspace_google_email(db: Session, workspace_id: int, email: str | None):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if ws:
        ws.google_email = email
        db.commit()