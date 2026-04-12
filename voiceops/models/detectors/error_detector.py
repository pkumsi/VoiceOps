from pathlib import Path
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parents[2]
TRAIN_PATH = BASE_DIR / "models" / "detectors" / "train_data.csv"
MODEL_PATH = BASE_DIR / "models" / "detectors" / "error_detector.joblib"

FEATURE_COLUMNS = [
    "semantic_score",
    "fuzzy_score",
    "phonetic_score",
    "word_count",
    "contains_stopword",
    "contains_digit",
]


def train():
    df = pd.read_csv(TRAIN_PATH)

    X = df[FEATURE_COLUMNS]
    y = df["should_correct"]

    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(class_weight="balanced", max_iter=1000))
    ])

    clf.fit(X, y)

    preds = clf.predict(X)
    print(classification_report(y, preds, digits=3))

    joblib.dump(clf, MODEL_PATH)
    print(f"Saved detector to {MODEL_PATH}")


if __name__ == "__main__":
    train()