from fastapi import FastAPI

from app.routers.google_auth import router as google_auth_router
from app.routers.gmail import router as gmail_router
from app.routers.mailmind import router as mailmind_router
from app.routers.workspaces import router as workspaces_router
from app.routers.audit import router as audit_router
from app.routers.tasks import router as tasks_router
from app.routers.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.admin import router as admin_router
from app.routers.integrations import router as integrations_router
app = FastAPI(title="MailMind API", version="0.1.0")

app.include_router(google_auth_router)
app.include_router(gmail_router)
app.include_router(mailmind_router)
app.include_router(workspaces_router)
app.include_router(audit_router)
app.include_router(tasks_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(integrations_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "mailmind-api"}

@app.get("/")
def root():
    return {"message": "MailMind backend running"}