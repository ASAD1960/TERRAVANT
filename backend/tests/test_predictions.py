
import io

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.fertilizer import recommend

CROP = {
    "nitrogen": 80,
    "phosphorus": 50,
    "potassium": 40,
    "temperature": 16,
    "humidity": 55,
    "ph": 7.3,
    "rainfall": 60,
}


def test_crop_prediction_and_history(client, farmer):
    r = client.post("/api/v1/predictions/crop", json=CROP, headers=farmer)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["predicted_crop"] == "wheat" and 0 < d["confidence"] <= 1
    assert len(d["alternatives"]) == 3
    assert d["model_version"] and d["limitations"]
    assert d["explanation"]["top_factors"]

    hist = client.get("/api/v1/predictions/crop", headers=farmer).json()
    assert any(h["id"] == d["prediction_id"] for h in hist)


def test_crop_input_bounds(client, farmer):
    assert client.post(
        "/api/v1/predictions/crop",
        json={**CROP, "ph": 20},
        headers=farmer,
    ).status_code == 422

    assert client.post(
        "/api/v1/predictions/crop",
        json={k: v for k, v in CROP.items() if k != "ph"},
        headers=farmer,
    ).status_code == 422


def test_prediction_not_visible_to_other_user(client, farmer, other):
    pid = client.post(
        "/api/v1/predictions/crop", json=CROP, headers=farmer
    ).json()["prediction_id"]

    assert client.get(
        f"/api/v1/predictions/crop/{pid}", headers=other
    ).status_code == 404

    assert client.get(
        f"/api/v1/predictions/crop/{pid}", headers=farmer
    ).status_code == 200


def test_cannot_use_foreign_field(client, farmer, other):
    farm = client.post(
        "/api/v1/farms",
        json={"farm_name": "Farm F"},
        headers=farmer,
    ).json()

    fid = client.post(
        "/api/v1/fields",
        json={"farm_id": farm["id"], "field_name": "f"},
        headers=farmer,
    ).json()["id"]

    assert client.post(
        "/api/v1/predictions/crop",
        json={**CROP, "field_id": fid},
        headers=other,
    ).status_code == 404


def test_yield(client, farmer):
    body = {
        "crop_name": "Wheat",
        "area_ha": 2,
        "rainfall": 80,
        "temperature": 18,
        "irrigated": True,
        "fertilizer_kg_ha": 150,
    }

    r = client.post(
        "/api/v1/predictions/yield", json=body, headers=farmer
    )
    assert r.status_code == 200, r.text

    d = r.json()
    assert d["yield_low"] <= d["yield_per_ha"] <= d["yield_high"]
    assert abs(d["total_production"] - d["yield_per_ha"] * 2) < 0.01
    assert "NOT a calibrated" in d["interval_note"]

    assert client.post(
        "/api/v1/predictions/yield",
        json={**body, "crop_name": "dragonfruit"},
        headers=farmer,
    ).status_code == 503


def test_fertilizer_has_no_dosage_and_flags_lab_test(client, farmer):
    r = client.post(
        "/api/v1/recommendations/fertilizer",
        json={
            "crop_name": "wheat",
            "nitrogen": 10,
            "phosphorus": 3,
            "ph": 8.9,
        },
        headers=farmer,
    )

    d = r.json()
    assert r.status_code == 200
    assert d["nutrient_status"]["nitrogen"]["status"] == "low"
    assert d["nutrient_status"]["phosphorus"]["status"] == "low"
    assert d["needs_lab_test"] is True
    assert "kg" not in " ".join(d["guidance"]).lower()
    assert d["disclaimer"]

    empty = client.post(
        "/api/v1/recommendations/fertilizer",
        json={"crop_name": "wheat"},
        headers=farmer,
    ).json()

    assert empty["needs_lab_test"] and not empty["nutrient_status"]


def _img(fmt="PNG", size=(128, 128)):
    b = io.BytesIO()
    Image.new("RGB", size, (30, 120, 40)).save(b, fmt)
    return b.getvalue()


def test_disease_rejects_non_images(client, farmer):
    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("evil.jpg", b"<?php echo 1; ?>", "image/jpeg")},
        headers=farmer,
    )
    assert r.status_code == 422

    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("tiny.png", _img(size=(10, 10)), "image/png")},
        headers=farmer,
    )
    assert r.status_code == 422

    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("a.gif", _img("GIF"), "image/gif")},
        headers=farmer,
    )
    assert r.status_code == 422


def test_disease_valid_image_never_fabricates(client, farmer):
    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("leaf.png", _img(), "image/png")},
        headers=farmer,
    )

    assert r.status_code in (200, 503)
    if r.status_code == 503:
        assert (
            "model" in r.json()["detail"].lower()
            or "pytorch" in r.json()["detail"].lower()
        )


def test_disease_requires_auth(client):
    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("a.png", _img(), "image/png")},
    )
    assert r.status_code == 401


def test_disease_rejects_oversized_image(client, farmer):
    oversized = _img(size=(5000, 5000))

    r = client.post(
        "/api/v1/predictions/disease",
        files={"file": ("large.png", oversized, "image/png")},
        headers=farmer,
    )

    assert r.status_code == 422
    assert "pixel limit" in r.json()["detail"].lower()


def test_disease_image_deleted_when_database_commit_fails(
    client, farmer, monkeypatch
):
    from types import SimpleNamespace

    from app.api.v1 import predictions

    def fake_prediction(img):
        return {
            "predicted_class": "test_disease",
            "confidence": 0.9,
            "is_uncertain": False,
            "alternatives": [
                {"label": "test_disease", "probability": 0.9}
            ],
            "model_version": "test",
            "data_source": "test",
            "message": "Test prediction",
            "limitations": [],
        }

    def fail_commit(self):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        predictions.disease_ml, "predict_disease", fake_prediction
    )
    monkeypatch.setattr(
        predictions,
        "version_row",
        lambda *args: SimpleNamespace(id="test-model-version"),
    )
    monkeypatch.setattr(Session, "commit", fail_commit)

    upload_dir = get_settings().UPLOAD_DIR
    before = set(upload_dir.glob("*.jpg")) if upload_dir.exists() else set()

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        client.post(
            "/api/v1/predictions/disease",
            files={"file": ("leaf.png", _img(), "image/png")},
            headers=farmer,
        )

    after = set(upload_dir.glob("*.jpg")) if upload_dir.exists() else set()
    assert after == before


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_fertilizer_rejects_invalid_nutrients(value):
    with pytest.raises(ValueError):
        recommend("wheat", nitrogen=value)


@pytest.mark.parametrize("ph", [2.9, 11.1, float("nan")])
def test_fertilizer_rejects_invalid_ph(ph):
    with pytest.raises(ValueError):
        recommend("wheat", ph=ph)


@pytest.mark.parametrize(
    "stage",
    [
        "sowing",
        "vegetative",
        "flowering",
        "fruiting",
        "maturity",
        "harvest",
    ],
)
def test_fertilizer_accepts_standard_growth_stages(stage):
    result = recommend("wheat", nitrogen=40, growth_stage=stage)
    assert any(stage in item for item in result["guidance"])


def test_fertilizer_rejects_unknown_growth_stage():
    with pytest.raises(ValueError, match="growth stage"):
        recommend("wheat", growth_stage="germination")
