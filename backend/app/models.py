from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base



class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    google_email = Column(String(255), nullable=True)  # e.g. "

    timezone = Column(String, default="UTC")
    default_meeting_duration_minutes = Column(Integer, default=30)
    company_tone = Column(Text, default="Professional and concise.")
    auto_execute_actions = Column(Boolean, default=False)

    # ✅ NEW: company identity for signatures
    company_display_name = Column(String, nullable=True)   # e.g. "Acme Inc."
    company_email = Column(String, nullable=True)          # e.g. "hello@acme.com"
    company_address = Column(Text, nullable=True)          # e.g. "Street, City, Country"
    company_phone = Column(String, nullable=True)          # optional
    signature_style = Column(String, default="team")       # "team" | "name" | "minimal"
    signature_name = Column(String, nullable=True)         # e.g. "Jai" (optional)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    email = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(32), nullable=False, default="viewer")  # admin/approver/viewer
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    token_json = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)

    message_id = Column(String(128), nullable=False)
    thread_id = Column(String(128), nullable=True)

    from_email = Column(Text, nullable=True)
    subject = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)

    classification_label = Column(String(32), nullable=True)
    classification_confidence = Column(String(16), nullable=True)
    classification_reason = Column(Text, nullable=True)

    draft_reply = Column(Text, nullable=False)
    status = Column(String(24), nullable=False)  # pending/approved/rejected/executed/sent/no_reply

    sent_message_id = Column(String(128), nullable=True)
    sent_thread_id = Column(String(128), nullable=True)

    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)

    action_type = Column(String(32), nullable=True)      # calendar_create/none
    action_payload = Column(Text, nullable=True)         # json string

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    action = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())