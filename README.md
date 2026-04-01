# Replynto: 
**Enterprise-ready AI automation platform for email + task execution with approvals and audit trails.**

## 1️⃣ Product Overview

Replynto is a multi-tenant B2B AI automation platform that:
- Connects to company Gmail accounts
- Classifies incoming emails
- Drafts intelligent replies
- Detects actionable intents (e.g., meeting scheduling)
- Requires human approval (configurable)
- Executes tasks across applications (Calendar, Email)
- Logs every action in an audit trail

It functions as a secure AI employee for modern businesses.

---

## 2️⃣ Core Architecture
Backend Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic (migrations)
- Google Gmail API
- Google Calendar API
- Gemini LLM
- Docker

---

## High-Level Flow

Inbox → AI → Approval Queue → Execution Engine → Audit Log

---

## 3️⃣ Data Model
Workspace

Represents a client/company.

Fields:
- id
- name
- timezone
- default_meeting_duration_minutes
- company_tone
- auto_execute_actions

This enables per-client behavior configuration.

---

Approval

Represents an AI-proposed action.

Fields:
- id
- workspace_id
- message_id
- status (pending / approved / sent)
- draft_reply
- action_type (email_only / calendar_create)
- action_payload (JSON)
- created_at

This decouples suggestion from execution.

---

AuditLog

Stores immutable history:

- workspace_id
- action
- details (JSON)
- timestamp

Ensures enterprise compliance & transparency.

---

## 4️⃣ Automation Engine
Email Processing
1. Fetch unread emails
2. Classify via LLM
3. Draft reply
4. Analyze for action intent

---

Action Analyzer

analyze_email_for_action():
- Detects meeting intent
- Uses LLM to extract structured meeting details
- Generates JSON payload
- Falls back to default schedule if extraction fails

Returns
```text
{
  action_type: "calendar_create" | "none",
  payload: {...}
}
```
---

Execution Engine

On approval + send:

If action_type == calendar_create:

- Create Google Calendar event
- Append event link to email
- Send email
- Log audit entry

If email_only:
- Send email
- Log audit entry

---

## 5️⃣ Current Capabilities

✔ Multi-workspace support

✔ Configurable workspace behavior

✔ Intelligent meeting extraction

✔ Calendar creation

✔ Approval workflow

✔ Audit logging

✔ Production-ready architecture

---

## 6️⃣ Next Roadmap (Strategic)

1. Extract attendee email automatically
2. Add Slack integration
3. Add CRM update action
4. Add admin dashboard UI
5. Add role-based access
6. Add billing layer

---