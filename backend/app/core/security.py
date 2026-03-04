import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET", "dev-change-me")
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "10080"))  # 7 days default

bearer = HTTPBearer(auto_error=False)

def create_access_token(payload: Dict[str, Any]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MIN)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> Dict[str, Any]:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        data = decode_token(creds.credentials)
        # expected: sub, workspace_id, role
        if "workspace_id" not in data or "role" not in data or "sub" not in data:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": int(data["sub"]), "workspace_id": int(data["workspace_id"]), "role": str(data["role"])}
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")