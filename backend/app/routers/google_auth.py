from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import requests

from app.core.deps import get_db
from app.core.security import get_current_user
from app.integrations.google_oauth import build_flow, save_credentials_db
from app.services.store import log_action
from app.models import Workspace

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def fetch_google_email(access_token: str) -> str | None:
    """
    Fetch the Google account email for the connected user.
    Uses OAuth2 userinfo endpoint.
    """
    try:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("email")
    except Exception:
        return None


@router.get("/google/start")
def google_start(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    flow = build_flow()

    # ✅ put workspace_id + return path in state
    state = f"{workspace_id}|/dashboard/settings"

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )

    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # "workspace_id|/dashboard/settings"

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    # ✅ parse state (workspace + next path)
    next_path = "/dashboard/settings"
    try:
        if "|" in state:
            ws_part, next_part = state.split("|", 1)
            workspace_id = int(ws_part)
            if next_part.strip():
                next_path = next_part
        else:
            workspace_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    flow = build_flow(state=state)
    flow.fetch_token(code=code)

    creds = flow.credentials

    # ✅ Save tokens
    save_credentials_db(db, workspace_id, creds)

    # ✅ Store google_email on Workspace (sellable UX)
    email = fetch_google_email(creds.token) if creds and creds.token else None
    if email:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if ws:
            ws.google_email = email
            db.commit()

    log_action(
        db,
        "GOOGLE_CONNECTED",
        {"workspace_id": workspace_id, "google_email": email},
        workspace_id=workspace_id,
    )

    # ✅ Redirect back to frontend (instead of showing JSON)
    return RedirectResponse(url=f"{FRONTEND_URL}{next_path}?google=connected")