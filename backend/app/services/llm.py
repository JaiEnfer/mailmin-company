import os
import json
from google import genai

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") 
COMPANY_TONE = os.getenv(
    "MAILMIND_COMPANY_TONE",
    "Professional, concise, friendly, action-oriented. Short paragraphs."
)

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        # Don't crash app import/CI. Fail only when LLM is actually used.
        raise RuntimeError("Missing GEMINI_API_KEY (required for LLM endpoints)")

    _client = genai.Client(api_key=api_key)
    return _client


def _gen_text(prompt: str) -> str:
    client = _get_client()
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return (resp.text or "").strip()


def classify_email(from_: str | None, subject: str | None, snippet: str | None) -> dict:
    prompt = f"""
You are MailMind, an AI email operations agent for a company.

Classify the email into ONE label:
- sales
- support
- billing
- meeting
- internal
- spam
- other

Return JSON ONLY (no markdown, no commentary) with keys:
label: string
confidence: number (0 to 1)
reason: short string

Email:
From: {from_}
Subject: {subject}
Snippet: {snippet}
""".strip()

    text = _gen_text(prompt)
    
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"label": "other", "confidence": 0.3, "reason": "Could not parse JSON from model output"}

    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {"label": "other", "confidence": 0.3, "reason": "JSON parse failed"}


def draft_reply(from_: str | None, subject: str | None, snippet: str | None) -> str:
    prompt = f"""
You are MailMind, an AI email operations agent for a company.

Write a reply draft. Follow this tone:
{COMPANY_TONE}

Rules:
- Do NOT invent facts.
- If info is missing, ask 1-2 clarifying questions.
- Keep it short and business-ready.
- Do not include a subject line, only the email body.

Email:
From: {from_}
Subject: {subject}
Snippet: {snippet}
""".strip()

    return _gen_text(prompt)