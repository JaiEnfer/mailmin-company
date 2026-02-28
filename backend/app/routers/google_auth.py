from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.integrations.google_oauth import build_flow, save_credentials_db
from app.services.store import log_action

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/start")
def google_start(workspace_id: int, db: Session = Depends(get_db)):
    # store workspace_id in state
    flow = build_flow(state=str(workspace_id))
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    log_action(db, "GOOGLE_AUTH_START", {"workspace_id": workspace_id})
    return RedirectResponse(auth_url)


@router.get("/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    # state contains workspace_id
    try:
        workspace_id = int(state)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    flow = build_flow(state=state)
    flow.fetch_token(code=code)

    save_credentials_db(db, workspace_id, flow.credentials)
    log_action(db, "GOOGLE_CONNECTED", {"workspace_id": workspace_id}, workspace_id=workspace_id)

    return {"status": "ok", "message": "Google connected. Tokens saved to DB.", "workspace_id": workspace_id}