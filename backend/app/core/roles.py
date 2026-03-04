from fastapi import Depends, HTTPException
from app.core.security import get_current_user

def require_role(*roles: str):
    def _dep(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return _dep