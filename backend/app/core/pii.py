import re

PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def redact_pii(text: str | None) -> str | None:
    if not text:
        return text
    t = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    t = PHONE_RE.sub("[REDACTED_PHONE]", t)
    return t