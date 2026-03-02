from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import requests

from app.core.deps import get_db
from app.core.security import get_current_user
from app.integrations.google_oauth import build_flow, save_credentials_db
from app.services.store import log_action

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.models import Workspace

router = APIRouter(prefix="/auth", tags=["auth"])

# IMPORTANT: Set this in Render to your Vercel domain, e.g. https://mailmind.vercel.app
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/google/start")
def google_start(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Starts Google OAuth. We store workspace_id in OAuth state.
    Optional: ?next=/dashboard/settings to decide where frontend should land after callback.
    """
    workspace_id = int(user["workspace_id"])
    next_path = request.query_params.get("next", "/dashboard/settings")

    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        # We pack workspace_id + next_path into state.
        # Format: "<workspace_id>|<next_path>"
        state=f"{workspace_id}|{next_path}",
    )
    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receives Google OAuth callback, saves credentials for the workspace,
    then redirects user back to frontend (never returns JSON).
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # "<workspace_id>|<next_path>"

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    # Parse state
    try:
        if "|" in state:
            ws_part, next_path = state.split("|", 1)
        else:
            ws_part, next_path = state, "/dashboard/settings"

        workspace_id = int(ws_part)
        if not next_path.startswith("/"):
            next_path = "/dashboard/settings"
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Complete OAuth
    flow = build_flow(state=state)
    flow.fetch_token(code=code)

    creds = flow.credentials
    save_credentials_db(db, workspace_id, creds)

    try:
        # userinfo endpoint (requires openid + userinfo.email)
        headers = {"Authorization": f"Bearer {creds.token}"}
        r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers, timeout=10)
        if r.ok:
            me = r.json()
            email = me.get("email")
            if email:
                ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
                if ws:
                    ws.google_email = email
                    db.commit()
                log_action(db, "GOOGLE_CONNECTED", {"email": email}, workspace_id=workspace_id)
    except Exception:
        pass

        # Fetch connected Google account email and store in workspace.google_email
    try:
        c = Credentials(
            token=creds.token,
            refresh_token=getattr(creds, "refresh_token", None),
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=creds.scopes,
        )

        oauth2 = build("oauth2", "v2", credentials=c)
        me = oauth2.userinfo().get().execute()
        email = me.get("email")

        if email:
            ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if ws:
                ws.google_email = email
                db.commit()

        log_action(db, "GOOGLE_CONNECTED", {"email": email}, workspace_id=workspace_id)
    except Exception:
        # Don't block OAuth flow if userinfo fails
        pass

    # Audit log
    try:
        log_action(
            db,
            "GOOGLE_CONNECTED",
            {"workspace_id": workspace_id},
            workspace_id=workspace_id,
        )
    except Exception:
        # Don't block redirect if audit logging fails
        pass

    # Redirect back to frontend with a flag so UI can show "Connected ✅"
    redirect_url = f"{FRONTEND_URL}{next_path}"
    if "?" in redirect_url:
        redirect_url += "&google=connected"
    else:
        redirect_url += "?google=connected"

    # 303 is better for OAuth callback redirect
    return RedirectResponse(url=redirect_url, status_code=303)