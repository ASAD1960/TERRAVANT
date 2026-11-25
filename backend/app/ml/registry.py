
"""Load trained ML artifacts and expose inference helpers."""

import hashlib
import json
import logging
import threading
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import get_settings

log = logging.getLogger(__name__)

MODEL_NAMES = (
    "crop_recommendation",
    "yield_prediction",
    "disease_detection",
)


class ModelUnavailable(Exception):
    """Raised when a model artifact is missing or cannot run."""


class _Registry:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[object, dict, tuple]] = {}

    def _dir(self, name: str) -> Path:
        if name not in MODEL_NAMES:
            raise ModelUnavailable(f"Unknown model: {name}")
        return get_settings().ML_ARTIFACT_DIR / name

    def metadata(self, name: str) -> dict:
        path = self._dir(name) / "metadata.json"

        if not path.is_file():
            raise ModelUnavailable(
                f"Model '{name}' metadata is missing."
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelUnavailable(
                f"Model '{name}' metadata is invalid."
            ) from exc

        if not isinstance(data, dict):
            raise ModelUnavailable(
                f"Model '{name}' metadata must be a JSON object."
            )

        if (
            not isinstance(data.get("version"), str)
            or not data["version"].strip()
        ):
            raise ModelUnavailable(
                f"Model '{name}' metadata has no valid version."
            )

        return data

    def sklearn(self, name: str):
        with self._lock:
            directory = self._dir(name)
            model_path = directory / "model.joblib"
            metadata_path = directory / "metadata.json"

            if not model_path.is_file():
                raise ModelUnavailable(
                    f"Model '{name}' artifact is missing. Run model training."
                )

            if not metadata_path.is_file():
                raise ModelUnavailable(
                    f"Model '{name}' metadata is missing."
                )

            try:
                def digest(path):
                    hasher = hashlib.sha256()
                    with path.open("rb") as artifact:
                        for chunk in iter(
                            lambda: artifact.read(1024 * 1024), b""
                        ):
                            hasher.update(chunk)
                    return hasher.hexdigest()

                signature = (
                    model_path.stat().st_mtime_ns,
                    model_path.stat().st_size,
                    digest(model_path),
                    metadata_path.stat().st_mtime_ns,
                    metadata_path.stat().st_size,
                    digest(metadata_path),
                )
            except OSError as exc:
                raise ModelUnavailable(
                    f"Cannot inspect model '{name}' artifacts."
                ) from exc

            cached = self._cache.get(name)

            if cached is not None and cached[2] == signature:
                return cached[0], cached[1]

            try:
                bundle = joblib.load(model_path)
                meta = self.metadata(name)
            except ModelUnavailable:
                raise
            except Exception as exc:
                log.exception("Failed loading model '%s'", name)
                raise ModelUnavailable(
                    f"Model '{name}' could not be loaded."
                ) from exc

            self._cache[name] = (bundle, meta, signature)
            return bundle, meta

    def reset(self):
        """Clear cached model artifacts."""
        with self._lock:
            self._cache.clear()

    def available(self) -> dict[str, bool]:
        root = get_settings().ML_ARTIFACT_DIR

        return {
            "crop_recommendation": (
                (root / "crop_recommendation" / "metadata.json").is_file()
                and (root / "crop_recommendation" / "model.joblib").is_file()
            ),
            "yield_prediction": (
                (root / "yield_prediction" / "metadata.json").is_file()
                and (root / "yield_prediction" / "model.joblib").is_file()
            ),
            "disease_detection": all(
                (root / "disease_detection" / filename).is_file()
                for filename in (
                    "metadata.json",
                    "model.pt",
                    "classes.json",
                )
            ),
        }


registry = _Registry()

CROP_LIMITATIONS = [
    "Model trained on {src} data; regional validation for Punjab is required before relying on it.",
    "Recommendations are decision support, not a guarantee of crop performance.",
    "Confidence is the model's own probability estimate, not real-world accuracy.",
]


def predict_crop(features: dict) -> dict:
    bundle, meta = registry.sklearn("crop_recommendation")

    try:
        order = meta["feature_order"]

        if not isinstance(order, list) or not order:
            raise ValueError("Invalid feature_order metadata.")

        values = [float(features[k]) for k in order]

        if not np.isfinite(values).all():
            raise ValueError("Input features must be finite.")

        x = pd.DataFrame([values], columns=order)
        proba = np.asarray(bundle.predict_proba(x)[0], dtype=float)
        classes = bundle.classes_

        if len(proba) != len(classes) or not len(proba):
            raise ValueError("Model returned incompatible class probabilities.")

        if not np.isfinite(proba).all():
            raise ValueError("Model returned invalid probabilities.")

        idx = np.argsort(proba)[::-1][:3]
        alts = [
            {
                "label": str(classes[i]),
                "probability": round(float(proba[i]), 4),
            }
            for i in idx
        ]

    except ModelUnavailable:
        raise
    except Exception as exc:
        log.exception("Crop prediction failed")
        raise ModelUnavailable(
            "Crop recommendation model could not process the input."
        ) from exc

    imp = meta.get("feature_importances", {})
    med = meta.get("feature_medians", {})
    ranges = meta.get("feature_ranges", {})

    factors = []

    for key, value in zip(order, values, strict=True):
        feature_range = ranges.get(key, [0, 1])
        span = max(feature_range[1] - feature_range[0], 1e-9)
        deviation = abs(value - med.get(key, value)) / span

        factors.append(
            {
                "feature": key,
                "importance": round(float(imp.get(key, 0.0)), 4),
                "value": value,
                "deviation_from_typical": round(deviation, 3),
            }
        )

    factors.sort(
        key=lambda factor: factor["importance"],
        reverse=True,
    )

    return {
        "predicted_crop": alts[0]["label"],
        "confidence": alts[0]["probability"],
        "alternatives": alts,
        "explanation": {
            "method": "global feature importance (Random Forest)",
            "top_factors": factors[:4],
        },
        "model_name": "crop_recommendation",
        "model_version": meta["version"],
        "data_source": meta.get("data_source", "unknown"),
        "limitations": [
            limitation.format(
                src=meta.get("data_source", "unknown")
            )
            for limitation in CROP_LIMITATIONS
        ],
    }


def predict_yield(f: dict) -> dict:
    bundle, meta = registry.sklearn("yield_prediction")

    try:
        crops = meta["crops"]

        if (
            not isinstance(crops, list)
            or not crops
            or not all(isinstance(crop, str) for crop in crops)
        ):
            raise ValueError("Invalid crop metadata.")

        key = f["crop_name"].strip().lower()
        normalized_crops = [crop.strip().lower() for crop in crops]

        if key not in normalized_crops:
            raise ModelUnavailable(
                f"Crop '{f['crop_name']}' is not supported. "
                f"Supported: {', '.join(crops)}"
            )

        estimators = bundle.estimators_

        if not len(estimators):
            raise ValueError("Yield model has no estimators.")

        row = [[
            normalized_crops.index(key),
            f["rainfall"],
            f["temperature"],
            1.0 if f["irrigated"] else 0.0,
            f["fertilizer_kg_ha"],
            f["soil_ph"],
        ]]

        x = np.asarray(row, dtype=float)

        if not np.isfinite(x).all():
            raise ValueError("Yield inputs must be finite.")

        per_tree = np.asarray(
            [tree.predict(x)[0] for tree in estimators],
            dtype=float,
        )

        if not np.isfinite(per_tree).all():
            raise ValueError("Yield model returned invalid predictions.")

    except ModelUnavailable:
        raise
    except Exception as exc:
        log.exception("Yield prediction failed")
        raise ModelUnavailable(
            "Yield prediction model could not process the input."
        ) from exc

    mean = float(per_tree.mean())
    low = float(np.percentile(per_tree, 10))
    high = float(np.percentile(per_tree, 90))

    mean, low, high = (
        max(mean, 0.0),
        max(low, 0.0),
        max(high, 0.0),
    )

    return {
        "yield_per_ha": round(mean, 3),
        "yield_low": round(low, 3),
        "yield_high": round(high, 3),
        "total_production": round(mean * f["area_ha"], 3),
        "yield_unit": "t/ha",
        "interval_note": (
            "10th-90th percentile spread across ensemble trees. "
            "This is NOT a calibrated prediction interval."
        ),
        "model_name": "yield_prediction",
        "model_version": meta["version"],
        "data_source": meta.get("data_source", "unknown"),
        "limitations": [
            f"Model trained on {meta.get('data_source', 'unknown')} data; "
            "treat output as a rough estimate.",
            "Actual yield depends on weather variability, pests, "
            "management and inputs not captured here.",
        ],
        "supported_crops": crops,
    }
