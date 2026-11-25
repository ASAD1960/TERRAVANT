from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import ModelVersion
from app.services.model_sync import version_row


def setup_module():
    Base.metadata.create_all(engine)


def test_version_row_does_not_commit_unrelated_changes():
    with SessionLocal() as db:
        pending = ModelVersion(
            model_name="transaction_test",
            version="1.0",
            model_type="test",
            deployment_status="staged",
        )
        db.add(pending)

        version_row(db, "crop_recommendation", "0.1.0")

        with SessionLocal() as other:
            found = other.scalar(
                select(ModelVersion).where(
                    ModelVersion.model_name == "transaction_test"
                )
            )
            assert found is None

        db.rollback()


def test_version_row_returns_existing_version():
    with SessionLocal() as db:
        row = ModelVersion(
            model_name="existing_test",
            version="1.0",
            model_type="test",
            deployment_status="staged",
        )
        db.add(row)
        db.flush()

        result = version_row(db, "existing_test", "1.0")
        assert result.id == row.id

        db.rollback()
