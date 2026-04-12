from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz
import jellyfish


BASE_DIR = Path(__file__).resolve().parents[2]
INDEX_PATH = BASE_DIR / "models" / "retriever" / "med_index.json"

_model = None
_terms = None
_embeddings = None


def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_index():
    global _terms, _embeddings
    if _terms is None or _embeddings is None:
        with open(INDEX_PATH, "r") as f:
            payload = json.load(f)
        _terms = payload["terms"]
        _embeddings = np.array(payload["embeddings"], dtype=np.float32)
    return _terms, _embeddings


def _phonetic_similarity(a: str, b: str) -> float:
    ma = jellyfish.metaphone(a)
    mb = jellyfish.metaphone(b)
    if not ma or not mb:
        return 0.0
    return fuzz.ratio(ma, mb) / 100.0


def rank_medical_candidates(span: str, top_k: int = 5):
    model = _load_model()
    terms, embeddings = _load_index()

    query_vec = model.encode([span], normalize_embeddings=True)[0]
    scores = embeddings @ query_vec

    ranked_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in ranked_idx:
        term = terms[idx]
        semantic_score = float(scores[idx])
        fuzzy_score = fuzz.ratio(span.lower(), term.lower()) / 100.0
        phonetic_score = _phonetic_similarity(span.lower(), term.lower())

        final_score = (
            0.5 * semantic_score +
            0.3 * fuzzy_score +
            0.2 * phonetic_score
        )

        results.append({
            "candidate": term,
            "semantic_score": semantic_score,
            "fuzzy_score": fuzzy_score,
            "phonetic_score": phonetic_score,
            "final_score": final_score
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results