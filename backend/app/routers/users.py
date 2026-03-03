from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.roles import require_role
from app.models import User
from app.services.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_ROLES = {"admin", "approver", "viewer"}

class CreateUserBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str = "viewer"

@router.post("/create")
def create_user(
    payload: CreateUserBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    workspace_id = int(user["workspace_id"])

    role = (payload.role or "viewer").lower().strip()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Use one of: {sorted(ALLOWED_ROLES)}")

    existing = db.query(User).filter(User.workspace_id == workspace_id, User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists in this workspace")

    new_user = User(
        workspace_id=workspace_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "workspace_id": new_user.workspace_id,
    }

@router.get("")
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
                "is_active": bool(getattr(u, "is_active", True)),
                "workspace_id": u.workspace_id,
            }
        )
    return {"items": items}