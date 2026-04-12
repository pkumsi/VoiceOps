import os
import json
from typing import Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()


def build_summary_prompt(redacted_transcript: str, audience: str = "clinician") -> str:
    if audience == "patient":
        return f"""
You are a medical communication assistant.

Summarize the following redacted healthcare call transcript for a patient.

Requirements:
- Use simple, non-technical language.
- Keep it short and clear.
- Do not invent facts.
- If uncertain, say so.
- Return ONLY valid JSON.
- Do NOT wrap the response in markdown or triple backticks.
- risk_flag must be a boolean: true or false.
- medications must be an array of strings.
- symptoms must be an array of strings.
- dosages must be an array of strings if present, otherwise [].
- next_steps must be an array of strings.

Return JSON with exactly these keys:
summary
medications
symptoms
dosages
next_steps
risk_flag

Transcript:
{redacted_transcript}
""".strip()

    return f"""
You are a healthcare documentation assistant.

Summarize the following redacted healthcare call transcript for a clinician.

Requirements:
- Be concise and factual.
- Capture medication mentions, symptoms, dosage/frequency if present, and follow-up actions.
- Do not invent facts.
- If uncertain, say so.
- Return ONLY valid JSON.
- Do NOT wrap the response in markdown or triple backticks.
- risk_flag must be a boolean: true or false.
- medications must be an array of strings.
- symptoms must be an array of strings.
- dosages must be an array of strings.
- follow_up must be an array of strings.

Return JSON with exactly these keys:
summary
medications
symptoms
dosages
follow_up
risk_flag

Transcript:
{redacted_transcript}
""".strip()


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    return cleaned


def _ensure_list(value: Any):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # split gently on commas only if needed
        if "," in value:
            return [part.strip() for part in value.split(",") if part.strip()]
        return [value.strip()] if value.strip() else []
    return [str(value)]


def _normalize_summary_payload(data: Dict[str, Any], audience: str) -> Dict[str, Any]:
    normalized = {
        "summary": data.get("summary", ""),
        "medications": _ensure_list(data.get("medications")),
        "symptoms": _ensure_list(data.get("symptoms")),
        "dosages": _ensure_list(data.get("dosages")),
        "risk_flag": bool(data.get("risk_flag", False)),
    }

    if audience == "patient":
        normalized["next_steps"] = _ensure_list(data.get("next_steps"))
    else:
        normalized["follow_up"] = _ensure_list(data.get("follow_up"))

    return normalized


def _safe_json_loads(text: str, audience: str):
    cleaned = _strip_code_fences(text)

    try:
        parsed = json.loads(cleaned)
        return _normalize_summary_payload(parsed, audience)
    except Exception:
        return {
            "summary": "",
            "medications": [],
            "symptoms": [],
            "dosages": [],
            "next_steps": [] if audience == "patient" else None,
            "follow_up": [] if audience != "patient" else None,
            "risk_flag": False,
            "raw_output": text,
            "parse_error": True
        }


def summarize_with_openrouter(prompt: str) -> Dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return {"text": content}


def summarize_with_gemini(prompt: str) -> Dict:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return {"text": text}


def summarize_transcript(redacted_transcript: str, audience: str = "clinician") -> Dict:
    provider = os.getenv("SUMMARY_PROVIDER", "openrouter").lower()
    prompt = build_summary_prompt(redacted_transcript, audience=audience)

    if provider == "gemini":
        llm_result = summarize_with_gemini(prompt)
    else:
        llm_result = summarize_with_openrouter(prompt)

    raw_text = llm_result["text"]
    parsed = _safe_json_loads(raw_text, audience)

    return {
        "provider": provider,
        "audience": audience,
        "result": parsed,
        "raw_output": raw_text,
        "parse_error": bool(parsed.get("parse_error", False)),
    }