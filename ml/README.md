# TERRAVANT ML

| Module | Script | Notes |
|---|---|---|
| Crop recommendation | `python -m crop_recommendation.train` | compares DT / RF / GB by CV macro-F1 |
| Yield prediction | `python -m yield_prediction.train` | RandomForestRegressor |
| Disease detection | `python -m disease_detection.train --data DIR` | needs torch + real image data |
| Fertilizer | rules in backend | no training |

Run from this directory (`cd ml`). Artifacts go to `ml/artifacts/<module>/` and are auto-registered
as `model_versions` when the API starts.

**Without `--csv`, models train on synthetic demo data** (`shared/synthetic.py`). That makes the system
runnable end-to-end, but the models are NOT agronomically valid. Replace with real datasets and perform
regional (Punjab) validation before any real-world use.
