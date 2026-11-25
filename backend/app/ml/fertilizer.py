
import math

"""Rule-based fertilizer guidance (hybrid-ready).

Thresholds are generic placeholders and require validation against current
Punjab agronomic guidance before production use. Outputs are qualitative;
this module never provides fertilizer dosage figures.
"""

RULESET_VERSION = "0.2-generic"

GROWTH_STAGES = {
    "sowing",
    "vegetative",
    "flowering",
    "fruiting",
    "maturity",
    "harvest",
}

THRESHOLDS = {
    "nitrogen": (20.0, 60.0),
    "phosphorus": (7.0, 20.0),
    "potassium": (80.0, 180.0),
}

CROP_NOTES = {
    "wheat": "Wheat responds strongly to nitrogen and phosphorus; timing across growth stages matters.",
    "rice": "Rice nutrient management depends on water regime; nitrogen is typically split across stages.",
    "cotton": "Cotton is sensitive to potassium and nitrogen balance during boll development.",
    "maize": "Maize has high nitrogen demand during rapid vegetative growth.",
    "sugarcane": "Sugarcane is a long-duration, high-nutrient-demand crop; ratoon crops need separate planning.",
}

ADVICE = {
    ("nitrogen", "low"): "Soil nitrogen appears low: a nitrogen source may benefit this crop. Confirm requirements locally.",
    ("nitrogen", "high"): "Soil nitrogen appears high: avoid additional nitrogen until a test confirms need.",
    ("phosphorus", "low"): "Soil phosphorus appears low: phosphorus management should be guided by a soil test.",
    ("phosphorus", "high"): "Soil phosphorus appears high: additional phosphorus may not add benefit.",
    ("potassium", "low"): "Soil potassium appears low: potassium management may improve crop quality and stress tolerance.",
    ("potassium", "high"): "Soil potassium appears high: additional potassium may not be needed.",
    ("nitrogen", "adequate"): "Nitrogen appears adequate; maintain normal crop-stage monitoring.",
    ("phosphorus", "adequate"): "Phosphorus appears adequate; follow locally recommended management.",
    ("potassium", "adequate"): "Potassium appears adequate; no corrective action is indicated by this test.",
}


def _validate_measurement(name: str, value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name} measurement.") from None

    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Invalid {name} measurement.")

    return number


def classify(nutrient: str, value: float) -> str:
    if nutrient not in THRESHOLDS:
        raise ValueError("Unsupported nutrient.")

    value = _validate_measurement(nutrient, value)
    low, high = THRESHOLDS[nutrient]
    return "low" if value < low else "high" if value > high else "adequate"


def ph_status(ph: float) -> dict:
    ph = _validate_measurement("pH", ph)
    if not 3 <= ph <= 11:
        raise ValueError("Soil pH must be between 3 and 11.")

    if ph < 5.5:
        return {"value": ph, "status": "acidic", "note": "Strongly acidic soils require retesting and local agronomic advice."}
    if ph > 8.5:
        return {"value": ph, "status": "strongly_alkaline", "note": "Possible sodic or calcareous conditions; seek local agronomic advice."}
    if ph > 7.8:
        return {"value": ph, "status": "alkaline", "note": "Alkaline conditions may limit micronutrient availability."}
    return {"value": ph, "status": "suitable", "note": "pH is within a generally workable range."}


def recommend(
    crop_name: str,
    nitrogen=None,
    phosphorus=None,
    potassium=None,
    ph=None,
    growth_stage=None,
) -> dict:
    if not isinstance(crop_name, str) or not crop_name.strip():
        raise ValueError("Crop name is required.")

    if growth_stage is not None:
        if not isinstance(growth_stage, str):
            raise ValueError("Invalid growth stage.")
        growth_stage = growth_stage.strip().lower()
        if growth_stage not in GROWTH_STAGES:
            raise ValueError("Unsupported growth stage.")

    values = {
        "nitrogen": nitrogen,
        "phosphorus": phosphorus,
        "potassium": potassium,
    }

    status = {}
    guidance = []
    reasons = []

    for name, value in values.items():
        if value is None:
            reasons.append(f"No {name} measurement provided.")
            continue

        number = _validate_measurement(name, value)
        level = classify(name, number)
        status[name] = {
            "value": number,
            "status": level,
            "reference_range": THRESHOLDS[name],
        }
        guidance.append(ADVICE[(name, level)])

    ph_info = ph_status(ph) if ph is not None else None

    if ph_info is None:
        reasons.append("No soil pH provided.")
    elif ph_info["status"] != "suitable":
        guidance.append(ph_info["note"])
        if ph_info["status"] in ("acidic", "strongly_alkaline"):
            reasons.append("Soil pH is outside the typical range.")

    note = CROP_NOTES.get(crop_name.strip().lower())
    if note:
        guidance.append(note)

    if growth_stage:
        guidance.append(
            f"Growth stage: {growth_stage}. Confirm timing with local crop guidance."
        )

    if not status:
        reasons.append(
            "No nutrient measurements: a laboratory soil test is required."
        )

    return {
        "nutrient_status": status,
        "ph_status": ph_info,
        "guidance": guidance,
        "needs_lab_test": bool(reasons),
        "lab_test_reasons": reasons,
        "ruleset_version": RULESET_VERSION,
        "disclaimer": (
            "Qualitative guidance based on generic reference ranges, not a "
            "prescription. Confirm requirements with a laboratory soil test "
            "and local agricultural advisor."
        ),
    }
