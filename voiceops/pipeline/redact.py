import re
from typing import Dict, List

PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
DOB_RE = re.compile(
    r"\b(?:DOB[:\s]*)?(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)?\d{2}\b",
    re.IGNORECASE,
)
MRN_RE = re.compile(r"\b(?:MRN|Medical Record Number)[:\s#-]*[A-Za-z0-9-]+\b", re.IGNORECASE)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

SPOKEN_SSN_RE = re.compile(r"\b(?:\d[\s,.\-]*){9}\b")

DIGIT_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}


def _replace_with_log(pattern, text: str, label: str):
    matches = []

    def repl(match):
        matches.append(match.group(0))
        return f"[REDACTED_{label}]"

    updated = pattern.sub(repl, text)
    return updated, matches


def _normalize_digit_words(text: str) -> str:
    out = text
    for word, digit in DIGIT_WORDS.items():
        out = re.sub(rf"\b{word}\b", digit, out, flags=re.IGNORECASE)
    return out


def redact_ssn_context(text: str):
    patterns = [
        r"((?:social security number|ssn)\s*(?:is|:)?\s*)([\d\s,.\-]+)",
    ]

    all_matches = []
    updated = text

    for pattern in patterns:
        def repl(match):
            prefix = match.group(1)
            digits = match.group(2)
            cleaned = re.sub(r"\D", "", digits)

            if len(cleaned) >= 4:
                all_matches.append(match.group(0))
                return prefix + "[REDACTED_SSN]"
            return match.group(0)

        updated = re.sub(pattern, repl, updated, flags=re.IGNORECASE)

    return updated, all_matches


def _redact_spoken_ssn(text: str):
    matches = []

    def repl(match):
        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 9:
            matches.append(raw)
            return "[REDACTED_SSN]"
        return raw

    updated = SPOKEN_SSN_RE.sub(repl, text)
    return updated, matches


def redact_pii(text: str) -> Dict:
    redacted = text
    redaction_log: List[Dict] = []

    redacted = _normalize_digit_words(redacted)

    for label, pattern in [
        ("PHONE", PHONE_RE),
        ("EMAIL", EMAIL_RE),
        ("DOB", DOB_RE),
        ("MRN", MRN_RE),
        ("SSN", SSN_RE),
    ]:
        redacted, matches = _replace_with_log(pattern, redacted, label)
        if matches:
            redaction_log.append({
                "type": label,
                "count": len(matches),
                "examples": matches[:3],
            })

    # context-aware SSN first
    redacted, ssn_ctx_matches = redact_ssn_context(redacted)
    if ssn_ctx_matches:
        redaction_log.append({
            "type": "SSN",
            "count": len(ssn_ctx_matches),
            "examples": ssn_ctx_matches[:3],
        })

    # fallback for spaced/spoken 9-digit forms
    redacted, spoken_ssn_matches = _redact_spoken_ssn(redacted)
    if spoken_ssn_matches:
        redaction_log.append({
            "type": "SSN",
            "count": len(spoken_ssn_matches),
            "examples": spoken_ssn_matches[:3],
        })

    return {
        "original_text": text,
        "redacted_text": redacted,
        "redactions": redaction_log,
    }