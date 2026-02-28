from fastapi import FastAPI

from app.routers.google_auth import router as google_auth_router
from app.routers.gmail import router as gmail_router
from app.routers.mailmind import router as mailmind_router
from app.routers.workspaces import router as workspaces_router
from app.routers.audit import router as audit_router
from app.routers.integrations import router as integrations_router
from app.main import app
from fastapi.testclient import TestClient


app = FastAPI(title="MailMind API", version="0.1.0")

app.include_router(google_auth_router)
app.include_router(gmail_router)
app.include_router(mailmind_router)
app.include_router(workspaces_router)
app.include_router(audit_router)

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"

@app.get("/health")
def health():
    return {"status": "ok", "service": "mailmind-api"}

@app.get("/")
def root():
    return {"message": "MailMind backend running"}

