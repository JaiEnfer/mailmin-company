import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def build_meeting_payload(timezone: str = "Europe/Berlin") -> str:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)

    payload = {
        "title": "Proposed meeting",
        "start_iso": start.isoformat(),
        "end_iso": end.isoformat(),
        "timezone": timezone,
        "attendees": [],
        "description": "Created by MailMind (proposed).",
    }
    return json.dumps(payload, ensure_ascii=False)