from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from google import genai


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_client = None


def _get_gemini_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        # Don't crash at import-time; only when action extraction needs it.
        raise RuntimeError("Missing GEMINI_API_KEY (required for meeting extraction)")

    _client = genai.Client(api_key=api_key)
    return _client


def _gemini_text(prompt: str) -> str:
    client = _get_gemini_client()
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return (resp.text or "").strip()


def _safe_json_loads(text: str) -> Optional[dict]:
    # Try direct JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract the first JSON object from the output
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return None
    return None


def extract_meeting_details(email_text: str, timezone_default: str = "Europe/Berlin") -> Optional[dict]:
    """
    Returns a dict:
    {
      "title": "...",
      "start_iso": "YYYY-MM-DDTHH:MM:SS+01:00" (preferred) or without offset
      "end_iso": "YYYY-MM-DDTHH:MM:SS+01:00" (preferred) or without offset
      "timezone": "Europe/Berlin"
    }
    or None if not found.
    """
    prompt = f"""
You extract meeting event details from an email.

Return ONLY valid JSON (no markdown, no extra text) with exactly these keys:
{{
  "title": "string",
  "start_iso": "ISO-8601 datetime",
  "end_iso": "ISO-8601 datetime",
  "timezone": "IANA timezone like Europe/Berlin"
}}

Rules:
- If the email does NOT contain a meeting proposal with date/time, return: null
- If duration is not specified, assume 30 minutes.
- Prefer timezone = {timezone_default} unless the email clearly specifies another timezone.
- Use an ISO format like 2026-02-27T15:00:00+01:00 if possible.

Email:
\"\"\"{email_text}\"\"\"
""".strip()

    text = _gemini_text(prompt)

    if text.lower() == "null":
        return None

    data = _safe_json_loads(text)
    if not data:
        return None

    # Minimal validation
    if not all(k in data for k in ("title", "start_iso", "end_iso", "timezone")):
        return None

    return data


def analyze_email_for_action(classification: Dict[str, Any], email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
    {
      "action_type": "calendar_create" | "none",
      "payload": dict | None
    }
    """
    label = (classification.get("label") or "").lower()

    subject = (email_data.get("subject") or "").strip()
    snippet = (email_data.get("snippet") or "").strip()
    email_text = f"Subject: {subject}\n\nSnippet: {snippet}".strip()

    # --- 1) Detect meeting intent (client-configurable later; MVP uses simple heuristics)
    keyword_hit = bool(re.search(r"\b(meet|meeting|schedule|call|demo|appointment|calendar|invite)\b", email_text.lower()))
    label_hit = "meet" in label or "calendar" in label or "call" in label or "appointment" in label

    meeting_intent = keyword_hit or label_hit

    if not meeting_intent:
        return {"action_type": "none", "payload": None}

    # --- 2) Try LLM extraction
    details = None
    try:
        details = extract_meeting_details(email_text, timezone_default="Europe/Berlin")
    except Exception:
        details = None

    if details:
        payload = {
            "title": details["title"] or (subject or "Meeting"),
            "start_iso": details["start_iso"],
            "end_iso": details["end_iso"],
            "timezone": details.get("timezone") or "Europe/Berlin",
            "attendees": [],  # later: extract or map sender email
            "description": "Auto-created by MailMind",
        }
        return {"action_type": "calendar_create", "payload": payload}

    # --- 3) Fallback (still creates a proposal)
    start = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)

    payload = {
        "title": subject or "Proposed meeting",
        "start_iso": start.isoformat(),
        "end_iso": end.isoformat(),
        "timezone": "Europe/Berlin",
        "attendees": [],
        "description": "Auto-created by MailMind (fallback schedule)",
    }
    return {"action_type": "calendar_create", "payload": payload}