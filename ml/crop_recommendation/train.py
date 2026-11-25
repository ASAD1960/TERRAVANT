"""Train the crop recommendation classifier.

Usage:
  python -m crop_recommendation.train                     # synthetic demo data
  python -m crop_recommendation.train --csv path/to.csv   # real data (see below)

CSV columns (Kaggle 'Crop Recommendation' layout also accepted):
  nitrogen|N, phosphorus|P, potassium|K, temperature, humidity, ph, rainfall, label
Candidates are compared with stratified CV on the training split only; the test split
is touched once, for the final report (no leakage; preprocessing lives inside the pipeline).
"""
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

from shared.common import save_sklearn_artifact
from shared.synthetic import CROP_FEATURES, crop_dataset

RENAME = {"N": "nitrogen", "P": "phosphorus", "K": "potassium"}


def load(csv: str | None):
    if not csv:
        return crop_dataset(), "synthetic-demo"
    df = pd.read_csv(csv).rename(columns=RENAME)
    missing = set(CROP_FEATURES + ["label"]) - set(df.columns)
    if missing:
        raise SystemExit(f"CSV missing columns: {sorted(missing)}")
    df = df[CROP_FEATURES + ["label"]].dropna().drop_duplicates()
    df["label"] = df["label"].str.strip().str.lower()
    return df, f"csv:{csv}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--version", default="0.1.0")
    a = ap.parse_args()

    df, source = load(a.csv)
    X, y = df[CROP_FEATURES], df["label"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=a.seed)

    candidates = {
        "decision_tree": DecisionTreeClassifier(max_depth=12, random_state=a.seed),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=2, n_jobs=-1, random_state=a.seed),
        "gradient_boosting": GradientBoostingClassifier(random_state=a.seed),
    }
    cv = StratifiedKFold(5, shuffle=True, random_state=a.seed)
    scores = {n: float(np.mean(cross_val_score(m, Xtr, ytr, cv=cv, scoring="f1_macro", n_jobs=-1))) for n, m in candidates.items()}
    best = max(scores, key=scores.get)
    print("CV macro-F1:", json.dumps(scores, indent=2), "→ selected", best)

    model = candidates[best].fit(Xtr, ytr)
    pred = model.predict(Xte)
    metrics = {
        "accuracy": float(accuracy_score(yte, pred)),
        "f1_macro": float(f1_score(yte, pred, average="macro")),
        "cv_f1_macro": scores,
        "selected_model": best,
        "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
        "per_class": classification_report(yte, pred, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(yte, pred, labels=model.classes_).tolist(),
        "labels": [str(c) for c in model.classes_],
    }
    print(f"test accuracy={metrics['accuracy']:.3f} macro-F1={metrics['f1_macro']:.3f}  (source: {source})")
    if source == "synthetic-demo":
        print("WARNING: trained on SYNTHETIC data — metrics are not evidence of real-world performance.")

    imp = getattr(model, "feature_importances_", np.zeros(len(CROP_FEATURES)))
    save_sklearn_artifact("crop_recommendation", model, {
        "version": a.version, "model_type": type(model).__name__, "data_source": source,
        "feature_order": CROP_FEATURES, "metrics": {k: v for k, v in metrics.items() if k != "per_class"} | {"per_class_f1": {c: v["f1-score"] for c, v in metrics["per_class"].items() if isinstance(v, dict) and c in metrics["labels"]}},
        "feature_importances": dict(zip(CROP_FEATURES, map(float, imp))),
        "feature_medians": X.median().to_dict(),
        "feature_ranges": {c: [float(X[c].min()), float(X[c].max())] for c in CROP_FEATURES},
        "regional_validation": "NOT DONE — required before presenting as locally reliable (SDD 8.1)",
    })


if __name__ == "__main__":
    main()
