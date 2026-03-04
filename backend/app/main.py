from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers.auth import router as auth_router
from app.routers.google_auth import router as google_auth_router
from app.routers.workspaces import router as workspace_router
from app.routers.integrations import router as integrations_router
from app.routers.gmail import router as gmail_router
from app.routers.mailmind import router as mailmind_router
from app.routers.audit import router as audit_router
from app.routers.users import router as users_router

app = FastAPI(title="MailMind API", version="1.0.0")

frontend = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(google_auth_router)
app.include_router(workspace_router)
app.include_router(integrations_router)
app.include_router(gmail_router)
app.include_router(mailmind_router)
app.include_router(audit_router)
app.include_router(users_router)

@app.get("/health")
def health():
    return {"ok": True}