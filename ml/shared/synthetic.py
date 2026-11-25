"""SYNTHETIC DEMONSTRATION DATA — NOT REAL AGRONOMIC DATA.

These generators exist so the pipeline, API and UI can run end-to-end before real
datasets are acquired. Class profiles below are illustrative and were NOT derived
from measurements. Metrics from models trained on them say nothing about real-world
performance. Replace with real data (Kaggle Crop Recommendation, regional soil lab
records, FAOSTAT yields, ...) via the --csv option of each train script.
"""
import numpy as np
import pandas as pd

CROP_FEATURES = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]

# mean, std for [N, P, K, temp, humidity, pH, rainfall]
CROP_PROFILES = {
    "wheat":     ([80, 50, 40, 16, 55, 7.3, 60],   [18, 12, 10, 3.0, 9, 0.45, 20]),
    "rice":      ([80, 45, 40, 26, 82, 6.5, 220],  [18, 12, 10, 2.5, 6, 0.40, 45]),
    "maize":     ([80, 45, 25, 24, 65, 6.3, 95],   [18, 12, 10, 3.0, 9, 0.45, 25]),
    "cotton":    ([115, 45, 25, 26, 78, 7.0, 85],  [18, 12, 10, 2.5, 7, 0.45, 25]),
    "sugarcane": ([100, 40, 80, 27, 75, 7.2, 150], [18, 12, 12, 2.5, 7, 0.45, 35]),
    "mustard":   ([60, 40, 40, 18, 60, 7.0, 50],   [15, 11, 10, 3.0, 9, 0.45, 18]),
    "chickpea":  ([40, 65, 80, 19, 40, 7.2, 70],   [12, 12, 12, 3.0, 10, 0.45, 22]),
    "potato":    ([100, 60, 115, 18, 70, 6.0, 75], [18, 12, 14, 2.5, 8, 0.40, 22]),
    "sunflower": ([60, 55, 50, 25, 55, 6.8, 65],   [15, 12, 10, 3.0, 9, 0.45, 20]),
}

# baseline yield t/ha (illustrative)
YIELD_BASE = {"wheat": 3.0, "rice": 2.8, "maize": 4.5, "cotton": 2.0, "sugarcane": 55.0,
              "mustard": 1.1, "chickpea": 0.9, "potato": 22.0, "sunflower": 1.9}
YIELD_FEATURES = ["crop_idx", "rainfall", "temperature", "irrigated", "fertilizer_kg_ha", "soil_ph"]


def crop_dataset(n_per_class: int = 400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts = []
    for crop, (mu, sd) in CROP_PROFILES.items():
        x = rng.normal(mu, sd, size=(n_per_class, len(mu)))
        df = pd.DataFrame(x, columns=CROP_FEATURES)
        df["label"] = crop
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    df[["nitrogen", "phosphorus", "potassium", "rainfall"]] = df[["nitrogen", "phosphorus", "potassium", "rainfall"]].clip(lower=0)
    df["humidity"] = df["humidity"].clip(5, 100)
    df["ph"] = df["ph"].clip(4, 9.5)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def yield_dataset(n: int = 6000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    crops = list(YIELD_BASE)
    idx = rng.integers(0, len(crops), n)
    rain = rng.uniform(20, 400, n)
    temp = rng.uniform(12, 36, n)
    irrig = rng.integers(0, 2, n).astype(float)
    fert = rng.uniform(0, 300, n)
    ph = rng.uniform(6.0, 8.8, n)
    base = np.array([YIELD_BASE[crops[i]] for i in idx])
    factor = (
        0.75 + 0.25 * irrig
        + 0.20 * (1 - np.exp(-fert / 120))
        - 0.0006 * (temp - 22) ** 2
        + 0.0003 * np.minimum(rain, 250)
        - 0.05 * np.abs(ph - 7.0)
    )
    y = np.clip(base * factor * rng.normal(1.0, 0.08, n), 0.05, None)
    return pd.DataFrame({"crop_idx": idx, "rainfall": rain, "temperature": temp, "irrigated": irrig,
                         "fertilizer_kg_ha": fert, "soil_ph": ph, "yield_t_ha": y}), crops
