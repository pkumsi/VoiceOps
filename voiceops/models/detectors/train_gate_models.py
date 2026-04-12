from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parents[2]
TRAIN_PATH = BASE_DIR / "models" / "detectors" / "train_data.csv"
OUT_DIR = BASE_DIR / "models" / "detectors"

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

    lr = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(class_weight="balanced", max_iter=1000))
    ])
    lr.fit(X, y)
    lr_preds = lr.predict(X)

    gb = GradientBoostingClassifier(random_state=42)
    gb.fit(X, y)
    gb_preds = gb.predict(X)

    print("=== Logistic Regression ===")
    print(classification_report(y, lr_preds, digits=3))

    print("=== Gradient Boosting ===")
    print(classification_report(y, gb_preds, digits=3))

    joblib.dump(lr, OUT_DIR / "error_detector_lr.joblib")
    joblib.dump(gb, OUT_DIR / "error_detector_gb.joblib")

    print("Saved both detector models.")


if __name__ == "__main__":
    train()