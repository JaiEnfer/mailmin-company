from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_session_local

def get_db():
    SessionLocal = get_session_local()
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="Database not configured (missing DATABASE_URL)")
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()