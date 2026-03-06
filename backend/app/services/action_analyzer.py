from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo
import json

from app.services.actions import build_meeting_payload

DEFAULT_TIMEZONE = "Europe/Berlin"
DEFAULT_DURATION_MINUTES = 30


def _safe_zoneinfo(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except Exception:
        return ZoneInfo("UTC")


def _text_from_msg(msg: dict) -> str:
    parts = [
        msg.get("subject") or "",
        msg.get("snippet") or "",
        msg.get("body") or "",
    ]
    return "\n".join(p for p in parts if p).strip()


def _extract_timezone(text: str) -> str:
    lowered = (text or "").lower()

    if "europe/berlin" in lowered or "berlin time" in lowered or "cet" in lowered or "cest" in lowered:
        return "Europe/Berlin"
    if "utc" in lowered or "gmt" in lowered:
        return "UTC"
    if "asia/karachi" in lowered or "pkt" in lowered:
        return "Asia/Karachi"
    if "america/new_york" in lowered or "new york time" in lowered or "est" in lowered or "edt" in lowered:
        return "America/New_York"
    if "america/los_angeles" in lowered or "pacific time" in lowered or "pst" in lowered or "pdt" in lowered:
        return "America/Los_Angeles"

    return DEFAULT_TIMEZONE


def _extract_duration_minutes(text: str) -> int:
    if not text:
        return DEFAULT_DURATION_MINUTES

    m = re.search(r"(\d+)\s*minutes?", text, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)))

    m = re.search(r"(\d+)\s*mins?", text, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)))

    m = re.search(r"(\d+)\s*hours?", text, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)) * 60)

    return DEFAULT_DURATION_MINUTES


def _extract_time(text: str) -> Optional[tuple[int, int]]:
    if not text:
        return None

    m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", text, flags=re.IGNORECASE)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = (m.group(3) or "").lower()

        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text, flags=re.IGNORECASE)
    if m:
        hour = int(m.group(1))
        minute = 0
        ampm = (m.group(2) or "").lower()

        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    return None


def _extract_date(text: str, timezone: str) -> Optional[datetime]:
    tz = _safe_zoneinfo(timezone)
    now = datetime.now(tz)
    lowered = (text or "").lower()

    if "tomorrow" in lowered:
        target = now + timedelta(days=1)
        return datetime(target.year, target.month, target.day, tzinfo=tz)

    if "today" in lowered:
        return datetime(now.year, now.month, now.day, tzinfo=tz)

    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz)

    m = re.search(r"\b([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\b", text, flags=re.IGNORECASE)
    if m:
        raw = f"{m.group(1)} {m.group(2)}, {m.group(3)}"
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return datetime(dt.year, dt.month, dt.day, tzinfo=tz)
            except ValueError:
                pass

    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b", text, flags=re.IGNORECASE)
    if m:
        raw = f"{m.group(1)} {m.group(2)} {m.group(3)}"
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return datetime(dt.year, dt.month, dt.day, tzinfo=tz)
            except ValueError:
                pass

    return None


def _extract_attendees(msg: dict) -> list[str]:
    sender = (msg.get("from") or "").strip()
    if "<" in sender and ">" in sender:
        email = sender.split("<", 1)[1].split(">", 1)[0].strip()
        return [email] if email else []
    if "@" in sender and " " not in sender:
        return [sender]
    return []


def _extract_title(msg: dict) -> str:
    return (msg.get("subject") or "").strip() or "Meeting"


def analyze_email_for_action(classification: dict, msg: dict) -> Dict[str, Any]:
    label = (classification.get("label") or "").lower().strip()

    if label not in ("meeting", "schedule", "call"):
        return {"action_type": "none", "payload": None}

    text = _text_from_msg(msg)
    timezone = _extract_timezone(text)
    duration_minutes = _extract_duration_minutes(text)
    date_part = _extract_date(text, timezone)
    time_part = _extract_time(text)

    if date_part and time_part:
        tz = _safe_zoneinfo(timezone)
        start_dt = datetime(
            date_part.year,
            date_part.month,
            date_part.day,
            time_part[0],
            time_part[1],
            tzinfo=tz,
        )
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        payload = {
            "title": _extract_title(msg),
            "start_iso": start_dt.isoformat(),
            "end_iso": end_dt.isoformat(),
            "timezone": timezone,
            "attendees": _extract_attendees(msg),
            "description": "Proposed by MailMind based on email intent.",
        }

        print("ACTION ANALYZER TIME:", payload)

        return {"action_type": "calendar_create", "payload": payload}

    # Fallback so booking still works in MVP
    fallback_payload = build_meeting_payload(timezone=timezone)
    payload = json.loads(fallback_payload)
    payload["title"] = _extract_title(msg)

    print("ACTION ANALYZER FALLBACK:", payload)

    return {"action_type": "calendar_create", "payload": payload}