import re

NUMBER_MAP = {
    "10mg": "10 milligrams",
    "20mg": "20 milligrams",
    "25mg": "25 milligrams",
    "40mg": "40 milligrams",
    "50mg": "50 milligrams",
    "500mg": "500 milligrams",
    "500 mg": "500 milligrams",
    "5 mg": "5 milligrams",
    "10 mg": "10 milligrams",
    "20 mg": "20 milligrams",
    "25 mg": "25 milligrams",
    "40 mg": "40 milligrams",
}


def normalize_transcript(text: str) -> str:
    out = text
    for k, v in NUMBER_MAP.items():
        out = re.sub(rf"\b{re.escape(k)}\b", v, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip()
    return out