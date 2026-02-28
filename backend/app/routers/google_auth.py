from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.integrations.google_oauth import build_flow, save_credentials_db
from app.services.store import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/start")
def google_start(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    workspace_id = int(user["workspace_id"])

    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=str(workspace_id),  # <— important: send workspace via OAuth state
    )
    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # this is our workspace_id

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    try:
        workspace_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    flow = build_flow()
    flow.fetch_token(code=code)

    creds = flow.credentials
    save_credentials_db(db, workspace_id, creds)

    # redirect back to frontend (optional)
    return {"status": "ok", "message": "Google connected. Tokens saved."}