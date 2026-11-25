"""Train the yield regressor (t/ha).

  python -m yield_prediction.train                  # synthetic demo data
  python -m yield_prediction.train --csv data.csv   # columns: crop, rainfall, temperature, irrigated, fertilizer_kg_ha, soil_ph, yield_t_ha
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from shared.common import save_sklearn_artifact
from shared.synthetic import YIELD_FEATURES, yield_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--version", default="0.1.0")
    a = ap.parse_args()

    if a.csv:
        df = pd.read_csv(a.csv).dropna()
        df["crop"] = df["crop"].str.strip().str.lower()
        crops = sorted(df["crop"].unique())
        df["crop_idx"] = df["crop"].map({c: i for i, c in enumerate(crops)})
        source = f"csv:{a.csv}"
    else:
        df, crops = yield_dataset()
        source = "synthetic-demo"

    X, y = df[YIELD_FEATURES], df["yield_t_ha"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=a.seed)
    model = RandomForestRegressor(n_estimators=250, min_samples_leaf=3, n_jobs=-1, random_state=a.seed).fit(Xtr, ytr)
    p = model.predict(Xte)
    metrics = {"mae": float(mean_absolute_error(yte, p)), "rmse": float(np.sqrt(mean_squared_error(yte, p))),
               "r2": float(r2_score(yte, p)), "n_train": int(len(Xtr)), "n_test": int(len(Xte))}
    print(metrics, f"(source: {source})")
    if source == "synthetic-demo":
        print("WARNING: trained on SYNTHETIC data — metrics are not evidence of real-world performance.")
    save_sklearn_artifact("yield_prediction", model, {
        "version": a.version, "model_type": "RandomForestRegressor", "data_source": source,
        "feature_order": YIELD_FEATURES, "crops": list(crops), "metrics": metrics,
        "interval": "tree-ensemble spread (uncalibrated)",
    })


if __name__ == "__main__":
    main()
