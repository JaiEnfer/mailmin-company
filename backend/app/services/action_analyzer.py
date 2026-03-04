from __future__ import annotations
from typing import Dict, Any

def analyze_email_for_action(classification: dict, msg: dict) -> Dict[str, Any]:
    """
    Client-flexible: decide actions based on classification.
    Return:
      { action_type: "calendar_create" | "none", payload: {...} | None }
    """
    label = (classification.get("label") or "").lower().strip()

    if label in ("meeting", "schedule", "call"):
        # Minimal payload — frontend/admin can edit later (future feature)
        return {
            "action_type": "calendar_create",
            "payload": {
                "title": "Meeting (proposed by MailMind)",
                "start_iso": None,
                "end_iso": None,
                "timezone": "Europe/Berlin",
                "attendees": [],
                "description": "Proposed by MailMind based on email intent.",
            },
        }

    return {"action_type": "none", "payload": None}