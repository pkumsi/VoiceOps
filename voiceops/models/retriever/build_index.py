from pathlib import Path
from sentence_transformers import SentenceTransformer
import json


BASE_DIR = Path(__file__).resolve().parents[2]
VOCAB_PATH = BASE_DIR / "benchmark" / "vocab" / "meds.txt"
OUTPUT_PATH = BASE_DIR / "models" / "retriever" / "med_index.json"


def load_vocab(path: Path):
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    terms = load_vocab(VOCAB_PATH)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(terms, normalize_embeddings=True)

    payload = {
        "terms": terms,
        "embeddings": embeddings.tolist()
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f)

    print(f"Saved index to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()