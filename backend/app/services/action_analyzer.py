from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Europe/Berlin"
DEFAULT_DURATION_MINUTES = 30

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

MONTH_PATTERN = (
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)

CANCEL_PATTERNS = [
    r"\bcancel\b",
    r"\bcancelled\b",
    r"\bcancel the meeting\b",
    r"\bcancel the appointment\b",
    r"\bcancel the call\b",
    r"\bplease cancel\b",
    r"\bcall off\b",
    r"\bcall off the meeting\b",
    r"\bdrop the meeting\b",
    r"\bno need for the meeting\b",
    r"\bno need for the call\b",
]

RESCHEDULE_PATTERNS = [
    r"\breschedule\b",
    r"\breschedule the meeting\b",
    r"\breschedule the appointment\b",
    r"\breschedule the call\b",
    r"\bmove it\b",
    r"\bmove the meeting\b",
    r"\bmove the appointment\b",
    r"\bmove the call\b",
    r"\bchange the time\b",
    r"\bchange the meeting\b",
    r"\bchange the appointment\b",
    r"\bchange the schedule\b",
    r"\bpostpone\b",
    r"\bpush it\b",
    r"\bshift it\b",
]


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


def _normalize_text_for_parsing(text: str) -> str:
    if not text:
        return ""

    cleaned = text

    cleaned = re.sub(r"[\t\r\n]+", " ", cleaned)

    cleaned = re.sub(
        rf"\b(\d{{1,2}})(st|nd|rd|th)?(?=({MONTH_PATTERN})\b)",
        r"\1\2 ",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?=\d)",
        r"\1 ",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def _extract_timezone(text: str) -> str:
    lowered = _normalize_text_for_parsing(text).lower()

    if (
        "europe/berlin" in lowered
        or "berlin time" in lowered
        or "germany time" in lowered
        or re.search(r"\b(cet|cest)\b", lowered)
    ):
        return "Europe/Berlin"

    if re.search(r"\b(utc|gmt)\b", lowered):
        return "UTC"

    if "asia/karachi" in lowered or re.search(r"\bpkt\b", lowered):
        return "Asia/Karachi"

    if (
        "america/new_york" in lowered
        or "new york time" in lowered
        or re.search(r"\b(est|edt)\b", lowered)
    ):
        return "America/New_York"

    if (
        "america/los_angeles" in lowered
        or "pacific time" in lowered
        or re.search(r"\b(pst|pdt)\b", lowered)
    ):
        return "America/Los_Angeles"

    if (
        "asia/dubai" in lowered
        or "dubai time" in lowered
        or re.search(r"\bgst\b", lowered)
    ):
        return "Asia/Dubai"

    if (
        "asia/kolkata" in lowered
        or "india time" in lowered
        or re.search(r"\bist\b", lowered)
    ):
        return "Asia/Kolkata"

    return DEFAULT_TIMEZONE


def _extract_duration_minutes(text: str) -> int:
    if not text:
        return DEFAULT_DURATION_MINUTES

    cleaned = _normalize_text_for_parsing(text)

    m = re.search(r"\b(\d+)\s*minutes?\b", cleaned, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)))

    m = re.search(r"\b(\d+)\s*mins?\b", cleaned, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)))

    m = re.search(r"\b(\d+)\s*hours?\b", cleaned, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)) * 60)

    m = re.search(r"\b(\d+)\s*hrs?\b", cleaned, flags=re.IGNORECASE)
    if m:
        return max(5, int(m.group(1)) * 60)

    return DEFAULT_DURATION_MINUTES


def _extract_time(text: str) -> Optional[tuple[int, int]]:
    if not text:
        return None

    cleaned = _normalize_text_for_parsing(text)

    m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", cleaned, flags=re.IGNORECASE)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = (m.group(3) or "").lower()

        if ampm:
            if hour < 1 or hour > 12:
                return None
            if ampm == "pm" and hour < 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
        else:
            if hour > 23 or minute > 59:
                return None

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute

    m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", cleaned, flags=re.IGNORECASE)
    if m:
        hour = int(m.group(1))
        minute = 0
        ampm = (m.group(2) or "").lower()

        if hour < 1 or hour > 12:
            return None

        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    return None


def _next_weekday(base_dt: datetime, weekday_name: str) -> datetime:
    target_weekday = WEEKDAYS[weekday_name.lower()]
    days_ahead = (target_weekday - base_dt.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target = base_dt + timedelta(days=days_ahead)
    return datetime(target.year, target.month, target.day, tzinfo=base_dt.tzinfo)


def _extract_date(text: str, timezone: str) -> Optional[datetime]:
    tz = _safe_zoneinfo(timezone)
    now = datetime.now(tz)
    cleaned = _normalize_text_for_parsing(text)
    lowered = cleaned.lower()

    if re.search(r"\btomorrow\b", lowered):
        target = now + timedelta(days=1)
        return datetime(target.year, target.month, target.day, tzinfo=tz)

    if re.search(r"\btoday\b", lowered):
        return datetime(now.year, now.month, now.day, tzinfo=tz)

    m = re.search(
        r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        lowered,
        flags=re.IGNORECASE,
    )
    if m:
        return _next_weekday(now, m.group(1))

    m = re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        lowered,
        flags=re.IGNORECASE,
    )
    if m and not re.search(r"\b\d{4}\b", cleaned):
        return _next_weekday(now, m.group(1))

    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", cleaned)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz)
        except ValueError:
            return None

    cleaned_no_ordinals = re.sub(
        r"\b(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE,
    )

    m = re.search(
        r"\b([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\b",
        cleaned_no_ordinals,
        flags=re.IGNORECASE,
    )
    if m:
        raw = f"{m.group(1)} {m.group(2)}, {m.group(3)}"
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return datetime(dt.year, dt.month, dt.day, tzinfo=tz)
            except ValueError:
                pass

    m = re.search(
        r"\b(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b",
        cleaned_no_ordinals,
        flags=re.IGNORECASE,
    )
    if m:
        raw = f"{m.group(1)} {m.group(2)} {m.group(3)}"
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                return datetime(dt.year, dt.month, dt.day, tzinfo=tz)
            except ValueError:
                pass

    m = re.search(
        rf"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday),?\s+(\d{{1,2}})\s+([A-Za-z]+)\s+(\d{{4}})\b",
        cleaned_no_ordinals,
        flags=re.IGNORECASE,
    )
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


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = _normalize_text_for_parsing(text).lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in patterns)


def analyze_email_for_action(classification: dict, msg: dict) -> Dict[str, Any]:
    label = (classification.get("label") or "").lower().strip()
    text = _text_from_msg(msg)
    timezone = _extract_timezone(text)
    duration_minutes = _extract_duration_minutes(text)
    date_part = _extract_date(text, timezone)
    time_part = _extract_time(text)

    is_cancel = _matches_any(text, CANCEL_PATTERNS)
    is_reschedule = _matches_any(text, RESCHEDULE_PATTERNS)

    if is_cancel:
        payload = {
            "title": _extract_title(msg),
            "timezone": timezone,
            "description": "Cancellation requested by Replynto based on email intent.",
        }
        print("ACTION ANALYZER CANCEL:", payload)
        return {"action_type": "calendar_cancel", "payload": payload}

    if is_reschedule:
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
                "description": "Rescheduled by Replynto based on email intent.",
            }

            print("ACTION ANALYZER RESCHEDULE:", payload)
            return {"action_type": "calendar_reschedule", "payload": payload}

        print(
            "ACTION ANALYZER: reschedule intent detected but date/time could not be extracted",
            {
                "timezone": timezone,
                "text": text,
            },
        )
        return {"action_type": "none", "payload": None}

    if label in ("meeting", "schedule", "call"):
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
                "description": "Proposed by Replynto based on email intent.",
            }

            print("ACTION ANALYZER CREATE:", payload)
            return {"action_type": "calendar_create", "payload": payload}

        print(
            "ACTION ANALYZER: meeting intent detected but date/time could not be extracted",
            {
                "timezone": timezone,
                "text": text,
            },
        )
        return {"action_type": "none", "payload": None}

    return {"action_type": "none", "payload": None}