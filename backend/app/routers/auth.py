from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import User, Workspace
from app.services.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(workspace_name: str, email: str, password: str, db: Session = Depends(get_db)):
    # create workspace + first admin user
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    ws = Workspace(name=workspace_name)
    db.add(ws)
    db.commit()
    db.refresh(ws)

    user = User(workspace_id=ws.id, email=email, password_hash=hash_password(password), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "workspace_id": ws.id, "role": user.role})
    return {"access_token": token, "user": {"id": user.id, "email": user.email, "role": user.role, "workspace_id": ws.id}}

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "workspace_id": user.workspace_id, "role": user.role})
    return {"access_token": token, "user": {"id": user.id, "email": user.email, "role": user.role, "workspace_id": user.workspace_id}}