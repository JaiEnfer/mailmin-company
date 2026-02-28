from app.core.db import get_session_local
from app.models import User
from app.services.auth import hash_password

SessionLocal = get_session_local()
if SessionLocal is None:
    raise RuntimeError("DATABASE_URL not configured")

db = SessionLocal()

email = "viewer@demo.co"
password = "Pass1234!"
workspace_id = 1
role = "viewer"

u = db.query(User).filter(User.email == email).first()

if not u:
    u = User(
        email=email,
        password_hash=hash_password(password),
        workspace_id=workspace_id,
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    print("Created user:", email, "role:", role)
else:
    print("User already exists:", email)

db.close()