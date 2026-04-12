from rapidfuzz import process, fuzz

MED_VOCAB = [
    "metformin",
    "lisinopril",
    "hydroxyzine",
    "atorvastatin",
    "insulin",
    "amlodipine",
    "omeprazole"
]


def correct_medical_terms(text: str):
    corrections = []
    words = text.split()
    corrected_words = []

    for word in words:
        match = process.extractOne(word, MED_VOCAB, scorer=fuzz.ratio)
        if match and match[1] >= 85 and word.lower() != match[0].lower():
            corrections.append({
                "type": "medical_term",
                "original": word,
                "corrected": match[0],
                "reason": "closest vocabulary match"
            })
            corrected_words.append(match[0])
        else:
            corrected_words.append(word)

    return " ".join(corrected_words), corrections