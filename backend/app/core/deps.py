from typing import Generator
from fastapi import HTTPException

from app.core.db import get_session_local


def get_db() -> Generator:
    SessionLocal = get_session_local()
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="Database not configured (missing DATABASE_URL)")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()