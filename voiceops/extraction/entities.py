import re
from typing import Dict, List

MEDICATIONS = [
    "metformin",
    "lisinopril",
    "atorvastatin",
    "amlodipine",
    "hydroxyzine",
    "omeprazole",
    "torsemide",
    "ibuprofen",
    "insulin",
    "acetaminophen",
    "amoxicillin",
    "prednisone",
    "gabapentin",
    "sertraline",
    "losartan",
    "levothyroxine",
    "albuterol",
    "azithromycin",
    "hydrochlorothiazide",
    "pantoprazole",
]

SYMPTOMS = [
    "chest pain",
    "shortness of breath",
    "dizziness",
    "itching",
    "fever",
    "vomiting",
    "nausea",
    "cough",
    "headache",
]

FREQUENCY_PATTERNS = [
    r"\bonce daily\b",
    r"\btwice daily\b",
    r"\bevery morning\b",
    r"\bevery night\b",
    r"\bbefore breakfast\b",
    r"\bbefore dinner\b",
    r"\btonight\b",
    r"\bstarting tomorrow\b",
]

DOSAGE_PATTERN = r"\b\d+\s?(?:mg|milligrams|ml|units)\b"
NEGATION_PATTERNS = [
    r"\bno chest pain\b",
    r"\bno fever\b",
    r"\bno vomiting\b",
    r"\bno ibuprofen\b",
    r"\bnot taking insulin\b",
    r"\bdenies dizziness\b",
]


def extract_entities(text: str) -> Dict:
    lowered = text.lower()

    medications: List[str] = [m for m in MEDICATIONS if m in lowered]
    symptoms: List[str] = [s for s in SYMPTOMS if s in lowered]
    dosages: List[str] = re.findall(DOSAGE_PATTERN, lowered)

    frequencies: List[str] = []
    for pattern in FREQUENCY_PATTERNS:
        matches = re.findall(pattern, lowered)
        frequencies.extend(matches)

    negations: List[str] = []
    for pattern in NEGATION_PATTERNS:
        matches = re.findall(pattern, lowered)
        negations.extend(matches)

    intent = "follow_up"
    if "refill" in lowered:
        intent = "prescription_refill"
    elif "change" in lowered:
        intent = "dose_change"
    elif any(symptom in lowered for symptom in SYMPTOMS):
        intent = "symptom_report"
    elif medications:
        intent = "medication_instruction"

    risk_flag = bool(negations) or ("shortness of breath" in lowered)

    return {
        "medications": medications,
        "dosages": dosages,
        "frequencies": frequencies,
        "negations": negations,
        "intent": intent,
        "risk_flag": risk_flag,
        "symptoms": symptoms,
    }