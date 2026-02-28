from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.roles import require_role
from app.models import User
from app.services.auth import hash_password
from app.services.store import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    rows = (
        db.query(User)
        .filter(User.workspace_id == workspace_id)
        .order_by(User.id.desc())
        .all()
    )
    items = []
    for u in rows:
        items.append(
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
        )
    return {"items": items}


@router.post("/users")
def create_user(
    email: str,
    password: str,
    role: str = "viewer",
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    role = role.lower().strip()
    if role not in ("admin", "approver", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

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

    log_action(db, "ADMIN_CREATE_USER", {"user_id": u.id, "email": u.email, "role": u.role}, workspace_id=workspace_id)

    return {"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active}


@router.post("/users/{user_id}/disable")
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    u = db.query(User).filter(User.id == user_id, User.workspace_id == workspace_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.is_active = False
    db.commit()

    log_action(db, "ADMIN_DISABLE_USER", {"user_id": u.id, "email": u.email}, workspace_id=workspace_id)

    return {"id": u.id, "email": u.email, "is_active": u.is_active}


@router.post("/users/{user_id}/role")
def change_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])
    role = role.lower().strip()
    if role not in ("admin", "approver", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    u = db.query(User).filter(User.id == user_id, User.workspace_id == workspace_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.role = role
    db.commit()

    log_action(db, "ADMIN_CHANGE_ROLE", {"user_id": u.id, "email": u.email, "role": u.role}, workspace_id=workspace_id)

    return {"id": u.id, "email": u.email, "role": u.role}