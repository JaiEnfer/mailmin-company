from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.roles import require_role
from app.models import User
from app.services.store import log_action
from app.services.auth import hash_password  # <-- IMPORTANT: uses your existing auth service

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_ROLES = {"admin", "approver", "viewer"}


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_role("admin")),
):
    """List users in the admin's workspace."""
    workspace_id = int(admin["workspace_id"])

    rows = (
        db.query(User)
        .filter(User.workspace_id == workspace_id)
        .order_by(User.id.asc())
        .all()
    )

    items = []
    for u in rows:
        items.append(
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "is_active": bool(u.is_active),
                "workspace_id": u.workspace_id,
            }
        )

    return {"items": items}


@router.post("/create")
def create_user(
    payload: dict,  # keep it simple to avoid pydantic EmailStr dependency issues
    db: Session = Depends(get_db),
    admin: dict = Depends(require_role("admin")),
):
    """
    Admin creates a new user inside their workspace.
    Body JSON:
      { "email": "x@company.com", "password": "Pass1234!", "role": "viewer|approver|admin" }
    """
    workspace_id = int(admin["workspace_id"])

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "viewer").strip().lower()

    if not email:
        raise HTTPException(status_code=422, detail="Email is required")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of: {sorted(ALLOWED_ROLES)}")

    existing = (
        db.query(User)
        .filter(User.workspace_id == workspace_id, User.email == email)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already exists in this workspace")

    u = User(
        workspace_id=workspace_id,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    log_action(
        db,
        "USER_CREATED",
        {"user_id": u.id, "email": u.email, "role": u.role},
        workspace_id=workspace_id,
    )

    return {"id": u.id, "email": u.email, "role": u.role, "is_active": bool(u.is_active)}


@router.post("/{user_id}/disable")
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_role("admin")),
):
    workspace_id = int(admin["workspace_id"])
    # Prevent admin from disabling themselves (don't assume JWT has "sub")
    admin_email = (admin.get("email") or "").strip().lower()

    target = (
        db.query(User)
        .filter(User.id == user_id, User.workspace_id == workspace_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if admin_email and target.email and target.email.strip().lower() == admin_email:
        raise HTTPException(status_code=400, detail="You cannot disable your own account.")

    u = target

    if not u.is_active:
        return {"ok": True, "id": u.id, "email": u.email, "is_active": bool(u.is_active)}

    u.is_active = False
    db.commit()
    db.refresh(u)

    log_action(
        db,
        "USER_DISABLED",
        {"user_id": u.id, "email": u.email},
        workspace_id=workspace_id,
    )

    return {"ok": True, "id": u.id, "email": u.email, "is_active": bool(u.is_active)}


@router.post("/{user_id}/enable")
def enable_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_role("admin")),
):
    workspace_id = int(admin["workspace_id"])

    u = (
        db.query(User)
        .filter(User.id == user_id, User.workspace_id == workspace_id)
        .first()
    )
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    if u.is_active:
        return {"ok": True, "id": u.id, "email": u.email, "is_active": bool(u.is_active)}

    u.is_active = True
    db.commit()
    db.refresh(u)

    log_action(
        db,
        "USER_ENABLED",
        {"user_id": u.id, "email": u.email},
        workspace_id=workspace_id,
    )

    return {"ok": True, "id": u.id, "email": u.email, "is_active": bool(u.is_active)}