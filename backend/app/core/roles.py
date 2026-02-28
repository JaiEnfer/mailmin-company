from fastapi import Depends, HTTPException
from app.core.security import get_current_user

def require_role(*allowed_roles: str):
    def dep(user: dict = Depends(get_current_user)):
        role = (user.get("role") or "").lower()
        if role not in [r.lower() for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dep