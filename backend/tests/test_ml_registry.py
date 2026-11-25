import json

import pytest

from app.ml.registry import ModelUnavailable, _Registry


@pytest.mark.parametrize("version", ["", "   ", None, 123])
def test_metadata_rejects_invalid_version(tmp_path, monkeypatch, version):
    from app.core.config import get_settings

    monkeypatch.setattr(
        get_settings(),
        "ML_ARTIFACT_DIR",
        tmp_path,
    )

    model_dir = tmp_path / "crop_recommendation"
    model_dir.mkdir()
    (model_dir / "metadata.json").write_text(
        json.dumps({"version": version}),
        encoding="utf-8",
    )

    with pytest.raises(ModelUnavailable):
        _Registry().metadata("crop_recommendation")

def test_registry_reuses_cached_model(tmp_path, monkeypatch):
    import json

    from app.core.config import get_settings
    from app.ml.registry import _Registry

    model_dir = tmp_path / "crop_recommendation"
    model_dir.mkdir()
    (model_dir / "metadata.json").write_text(
        json.dumps({"version": "1.0"}),
        encoding="utf-8",
    )
    (model_dir / "model.joblib").write_bytes(b"model")

    monkeypatch.setattr(get_settings(), "ML_ARTIFACT_DIR", tmp_path)

    registry = _Registry()
    bundle = object()
    calls = []

    def fake_load(path):
        calls.append(path)
        return bundle

    monkeypatch.setattr("app.ml.registry.joblib.load", fake_load)

    first = registry.sklearn("crop_recommendation")
    second = registry.sklearn("crop_recommendation")

    assert first == second
    assert first[0] is bundle
    assert len(calls) == 1

def test_registry_reloads_when_artifact_changes(tmp_path, monkeypatch):
    import json

    from app.core.config import get_settings
    from app.ml.registry import _Registry

    model_dir = tmp_path / "crop_recommendation"
    model_dir.mkdir()
    model_path = model_dir / "model.joblib"
    model_path.write_bytes(b"first")
    (model_dir / "metadata.json").write_text(
        json.dumps({"version": "1.0"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(get_settings(), "ML_ARTIFACT_DIR", tmp_path)

    registry = _Registry()
    calls = []

    def fake_load(path):
        calls.append(path)
        return object()

    monkeypatch.setattr("app.ml.registry.joblib.load", fake_load)

    first, _ = registry.sklearn("crop_recommendation")
    model_path.write_bytes(b"second-version")

    second, _ = registry.sklearn("crop_recommendation")

    assert first is not second
    assert len(calls) == 2

def test_registry_detects_same_size_artifact_replacement(tmp_path, monkeypatch):
    import json
    import os

    from app.core.config import get_settings
    from app.ml.registry import _Registry

    model_dir = tmp_path / "crop_recommendation"
    model_dir.mkdir()
    model_path = model_dir / "model.joblib"
    model_path.write_bytes(b"first")
    metadata_path = model_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps({"version": "1.0"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(get_settings(), "ML_ARTIFACT_DIR", tmp_path)

    registry = _Registry()
    calls = []

    def fake_load(path):
        calls.append(path)
        return object()

    monkeypatch.setattr("app.ml.registry.joblib.load", fake_load)

    first, _ = registry.sklearn("crop_recommendation")
    original_time = model_path.stat().st_mtime_ns

    model_path.write_bytes(b"other")
    os.utime(model_path, ns=(original_time, original_time))

    second, _ = registry.sklearn("crop_recommendation")

    assert first is not second
    assert len(calls) == 2
