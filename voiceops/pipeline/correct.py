import re
from pathlib import Path
from typing import List, Dict
import joblib

from voiceops.models.retriever.rank_candidates import rank_medical_candidates

STOPWORDS = {"taking", "take", "is", "are", "was", "were", "keep", "continue", "needs"}

BASE_DIR = Path(__file__).resolve().parents[1]
DETECTOR_PATH = BASE_DIR / "models" / "detectors" / "error_detector.joblib"

_detector = None


def load_detector():
    global _detector
    if _detector is None:
        _detector = joblib.load(DETECTOR_PATH)
    return _detector


def generate_ngrams(tokens, n=4):
    ngrams = []
    for i in range(len(tokens)):
        for j in range(1, n + 1):
            if i + j <= len(tokens):
                span = " ".join(tokens[i:i + j])
                ngrams.append((i, i + j, span))
    return ngrams


def looks_like_error(span: str) -> bool:
    span = span.lower().strip()
    if len(span.replace(" ", "")) < 6:
        return False
    return True

COMMON_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or",
    "but", "with", "for", "from", "to", "of", "in", "on", "at",
    "patient", "please", "take", "taking", "needs", "need", "keep", "continue"
}

def suspicious_span_score(span: str) -> float:
    words = span.lower().split()
    if not words:
        return 0.0

    uncommon = sum(1 for w in words if w not in COMMON_WORDS)
    return uncommon / len(words)



def build_features(span: str, best: Dict) -> Dict:
    words = span.lower().split()
    return {
        "semantic_score": best["semantic_score"],
        "fuzzy_score": best["fuzzy_score"],
        "phonetic_score": best["phonetic_score"],
        "word_count": len(words),
        "contains_stopword": int(any(w in STOPWORDS for w in words)),
        "contains_digit": int(any(ch.isdigit() for ch in span)),
    }


def should_apply_correction(span: str, best: Dict, prob_threshold: float = 0.55):
    detector = load_detector()
    feats = build_features(span, best)

    X = [[
        feats["semantic_score"],
        feats["fuzzy_score"],
        feats["phonetic_score"],
        feats["word_count"],
        feats["contains_stopword"],
        feats["contains_digit"],
    ]]

    prob = detector.predict_proba(X)[0][1]
    return prob >= prob_threshold, prob, feats


def _run_retrieval_correction(text: str, retrieval_threshold: float = 0.70, use_gate: bool = True):
    tokens = text.split()
    used = [False] * len(tokens)
    corrections: List[Dict] = []
    corrected_tokens = tokens.copy()

    ngrams = sorted(generate_ngrams(tokens, n=4), key=lambda x: (x[1] - x[0]), reverse=True)

    for start, end, span in ngrams:
        if any(used[start:end]):
            continue

        clean = re.sub(r"[^a-zA-Z ]", "", span).strip()

        if not looks_like_error(clean):
            continue
        
        if suspicious_span_score(clean) < 0.5:
            continue


        ranked = rank_medical_candidates(clean, top_k=3)
        best = ranked[0] if ranked else None
        if not best:
            continue

        candidate = best["candidate"]

        if best["final_score"] < retrieval_threshold:
            continue

        if clean.lower() == candidate.lower():
            continue

        gate_prob = None
        feats = build_features(clean, best)

        if use_gate:
            apply_fix, gate_prob, feats = should_apply_correction(clean, best)
            if not apply_fix:
                continue

        corrected_tokens[start:end] = [candidate] + [""] * (end - start - 1)
        for i in range(start, end):
            used[i] = True

        corrections.append({
            "type": "gated_phrase_correction" if use_gate else "ungated_phrase_correction",
            "original": span,
            "clean_span": clean,
            "corrected": candidate,
            "retrieval_score": round(best["final_score"], 4),
            "gate_probability": None if gate_prob is None else round(gate_prob, 4),
            "semantic_score": round(best["semantic_score"], 4),
            "fuzzy_score": round(best["fuzzy_score"], 4),
            "phonetic_score": round(best["phonetic_score"], 4),
            "features": feats,
        })

    corrected_text = " ".join([t for t in corrected_tokens if t != ""])

    return {
        "corrected_text": corrected_text,
        "corrections": corrections
    }


def correct_transcript_with_retrieval(text: str, retrieval_threshold: float = 0.70):
    return _run_retrieval_correction(text, retrieval_threshold=retrieval_threshold, use_gate=False)


def correct_transcript_with_gated_retrieval(text: str, retrieval_threshold: float = 0.70):
    return _run_retrieval_correction(text, retrieval_threshold=retrieval_threshold, use_gate=True)