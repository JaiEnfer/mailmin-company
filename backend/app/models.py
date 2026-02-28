from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.core.db import Base

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(128), nullable=False, index=True)
    thread_id = Column(String(128), nullable=True)
    from_email = Column(Text, nullable=True)
    subject = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)

    classification_label = Column(String(32), nullable=True)
    classification_confidence = Column(String(16), nullable=True)
    classification_reason = Column(Text, nullable=True)

    draft_reply = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="pending")  # pending|approved|rejected|sent

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sent_message_id = Column(String(128), nullable=True)
    sent_thread_id = Column(String(128), nullable=True)
    workspace_id = Column(Integer, nullable=True, index=True)
    action_type = Column(String(32), nullable=True)  # "email_only", "calendar_create"
    action_payload = Column(Text, nullable=True)     # JSON for task details

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, nullable=True, index=True)  # ← THIS MUST EXIST
    action = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # NEW CONFIG FIELDS
    timezone = Column(String(64), default="Europe/Berlin")
    default_meeting_duration_minutes = Column(Integer, default=30)
    company_tone = Column(Text, default="Professional and concise.")
    auto_execute_actions = Column(Boolean, default=False)

class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, nullable=False, index=True)

    token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_uri = Column(Text, nullable=True)
    client_id = Column(Text, nullable=True)
    client_secret = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)  # store as JSON string

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)

    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    role = Column(String(32), nullable=False, default="admin")  # admin | approver | viewer
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)