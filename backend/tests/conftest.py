import os
import subprocess
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="terravant-test-")
os.environ.update({
    "ENV": "test",
    "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
    "SECRET_KEY": "test-secret-key-test-secret-key-1234",
    "UPLOAD_DIR": f"{_tmp}/uploads",
    "RATE_LIMIT_AUTH_PER_MIN": "1000",
})
REPO = Path(__file__).resolve().parents[2]
if not (REPO / "ml" / "artifacts" / "crop_recommendation" / "model.joblib").exists():
    for m in ("crop_recommendation.train", "yield_prediction.train"):
        subprocess.run([sys.executable, "-m", m], cwd=REPO / "ml", check=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PW = "S3cure-passw0rd"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _register(client, email, account="farmer"):
    r = client.post("/api/v1/auth/register", json={"full_name": "Test User", "email": email, "password": PW, "account_type": account})
    assert r.status_code == 201, r.text
    t = client.post("/api/v1/auth/login", json={"email": email, "password": PW}).json()
    return {"Authorization": f"Bearer {t['access_token']}"}


@pytest.fixture(scope="session")
def farmer(client):
    return _register(client, "farmer1@example.com")


@pytest.fixture(scope="session")
def other(client):
    return _register(client, "farmer2@example.com")


@pytest.fixture(scope="session")
def admin(client):
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import Role, User

    h = _register(client, "admin@example.com")
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == "admin@example.com"))
        u.roles = [db.scalar(select(Role).where(Role.name == "admin"))]
        db.commit()
    return h
