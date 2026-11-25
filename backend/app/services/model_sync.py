"""Register trained model artifacts for prediction traceability."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.registry import ModelUnavailable, registry
from app.models import ModelVersion

log = logging.getLogger(__name__)

NAMES = (
    "crop_recommendation",
    "yield_prediction",
    "disease_detection",
)


def _artifacts_exist(name: str) -> bool:
    directory = get_settings().ML_ARTIFACT_DIR / name

    required = (
        ("metadata.json", "model.pt", "classes.json")
        if name == "disease_detection"
        else ("metadata.json", "model.joblib")
    )

    return all((directory / filename).is_file() for filename in required)


def sync_model_versions(db: Session) -> None:
    """Register missing model versions within the caller's transaction."""
    for name in NAMES:
        if not _artifacts_exist(name):
            log.warning("Skipping incomplete model artifacts: %s", name)
            continue

        try:
            meta = registry.metadata(name)
        except ModelUnavailable:
            log.warning("Skipping invalid model metadata: %s", name)
            continue

        version = meta["version"]

        exists = db.scalar(
            select(ModelVersion).where(
                ModelVersion.model_name == name,
                ModelVersion.version == version,
            )
        )

        if exists:
            continue

        db.add(
            ModelVersion(
                model_name=name,
                version=version,
                model_type=meta.get("model_type", "unknown"),
                artifact_location=str(get_settings().ML_ARTIFACT_DIR / name),
                metrics=meta.get("metrics"),
                data_source=meta.get("data_source"),
                deployment_status="active",
            )
        )

        log.info("Registered model %s version %s", name, version)

    db.flush()


def version_row(db: Session, name: str, version: str) -> ModelVersion:
    row = db.scalar(
        select(ModelVersion).where(
            ModelVersion.model_name == name,
            ModelVersion.version == version,
        )
    )

    if row is not None:
        return row

    sync_model_versions(db)

    row = db.scalar(
        select(ModelVersion).where(
            ModelVersion.model_name == name,
            ModelVersion.version == version,
        )
    )

    if row is None:
        raise ModelUnavailable(
            f"Model version '{name}:{version}' is not registered."
        )

    return row
