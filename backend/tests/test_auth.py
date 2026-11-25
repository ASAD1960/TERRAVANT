from tests.conftest import PW


def test_register_duplicate_and_validation(client):
    body = {"full_name": "A B", "email": "dup@example.com", "password": PW}
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    assert client.post("/api/v1/auth/register", json=body).status_code == 409           # TC-02
    assert client.post("/api/v1/auth/register", json={**body, "email": "x@example.com", "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={**body, "email": "y@example.com", "account_type": "admin"}).status_code == 422


def test_login_ok_and_bad(client, farmer):
    assert client.post("/api/v1/auth/login", json={"email": "farmer1@example.com", "password": PW}).status_code == 200   # TC-03
    r = client.post("/api/v1/auth/login", json={"email": "farmer1@example.com", "password": "wrong-password1"})
    assert r.status_code == 401                                                                                         # TC-04
    r2 = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong-password1"})
    assert r.json() == r2.json()  # no account enumeration


def test_protected_requires_token(client):
    assert client.get("/api/v1/farms").status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_refresh_and_token_type_confusion(client):
    t = client.post("/api/v1/auth/login", json={"email": "farmer1@example.com", "password": PW}).json()
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]})
    assert refreshed.status_code == 200
    replacement = refreshed.json()

    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t["access_token"]}).status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {t['refresh_token']}"}).status_code == 401

    # Reusing a rotated refresh token revokes the entire session.
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": replacement["refresh_token"]}).status_code == 401
    assert client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {replacement['access_token']}"},
    ).status_code == 401


def test_password_reset_single_use(client):
    client.post("/api/v1/auth/register", json={"full_name": "Re Set", "email": "reset@example.com", "password": PW})
    tok = client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"}).json()["dev_reset_token"]
    assert client.post("/api/v1/auth/reset-password", json={"token": tok, "new_password": "N3w-passw0rd!!"}).status_code == 200
    assert client.post("/api/v1/auth/reset-password", json={"token": tok, "new_password": "An0ther-passw0rd"}).status_code == 400
    assert client.post("/api/v1/auth/login", json={"email": "reset@example.com", "password": "N3w-passw0rd!!"}).status_code == 200


def test_forgot_does_not_leak_existence(client):
    r = client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"})
    assert r.status_code == 200 and "dev_reset_token" not in r.json()


def test_login_persists_hashed_refresh_session(client):
    import hashlib

    from app.core.security import decode_token
    from app.database import SessionLocal
    from app.models import UserSession

    email = "session-persist@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "Session Persist", "email": email, "password": PW},
    ).status_code == 201

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PW},
    ).json()

    claims = decode_token(tokens["refresh_token"], "refresh")
    with SessionLocal() as db:
        session = db.get(UserSession, claims["sid"])
        assert session is not None
        assert session.user_id == claims["sub"]
        assert session.refresh_token_hash == hashlib.sha256(
            tokens["refresh_token"].encode("utf-8")
        ).hexdigest()
        assert tokens["refresh_token"] not in session.refresh_token_hash
        assert session.revoked_at is None


def test_logout_revokes_access_and_refresh(client):
    email = "session-logout@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "Session Logout", "email": email, "password": PW},
    ).status_code == 201

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PW},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401


def test_password_reset_revokes_existing_sessions(client):
    email = "session-reset@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "Session Reset", "email": email, "password": PW},
    ).status_code == 201

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PW},
    ).json()

    reset_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
    )
    assert reset_response.status_code == 200
    reset_token = reset_response.json()["dev_reset_token"]

    new_password = "N3w-session-passw0rd!"
    assert client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    ).status_code == 200

    old_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/v1/users/me", headers=old_headers).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert new_login.status_code == 200


def test_admin_suspension_revokes_sessions_permanently(client, admin):
    email = "session-suspend@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "Session Suspend", "email": email, "password": PW},
    ).status_code == 201

    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PW},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    user = client.get("/api/v1/users/me", headers=headers)
    assert user.status_code == 200
    user_id = user.json()["id"]

    suspended = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=admin,
    )
    assert suspended.status_code == 200

    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401

    reactivated = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "active"},
        headers=admin,
    )
    assert reactivated.status_code == 200

    # Reactivation must not revive the old access or refresh tokens.
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    ).status_code == 401

    # A fresh login after reactivation must work.
    fresh_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PW},
    )
    assert fresh_login.status_code == 200


def test_reset_rejects_weak_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Weak Reset", "email": "weakreset@example.com", "password": PW},
    )
    token = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "weakreset@example.com"},
    ).json()["dev_reset_token"]

    for password in ("abcdefghij", "1234567890"):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": password},
        )
        assert response.status_code == 422


def test_profile_update_rejects_null_required_fields(client, farmer):
    for field in ("full_name", "language"):
        response = client.put(
            "/api/v1/users/me",
            headers=farmer,
            json={field: None},
        )
        assert response.status_code == 422


def test_profile_update_accepts_valid_and_nullable_fields(client, farmer):
    response = client.put(
        "/api/v1/users/me",
        headers=farmer,
        json={
            "full_name": "Updated Farmer",
            "language": "ur",
            "phone": None,
            "organization": None,
        },
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Farmer"
    assert response.json()["language"] == "ur"
    assert response.json()["phone"] is None


def test_access_token_rejects_missing_session_id(client, farmer):
    import jwt

    from app.core.config import get_settings
    from app.core.security import decode_token

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer1@example.com", "password": PW},
    ).json()["access_token"]

    claims = decode_token(token, "access")
    claims.pop("sid")

    malformed = jwt.encode(
        claims,
        get_settings().SECRET_KEY,
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {malformed}"},
    )
    assert response.status_code == 401


def test_access_token_rejects_revoked_session(client, farmer):
    from datetime import datetime, timezone

    from app.core.security import decode_token
    from app.database import SessionLocal
    from app.models import UserSession

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer1@example.com", "password": PW},
    ).json()["access_token"]

    claims = decode_token(token, "access")

    with SessionLocal() as db:
        session = db.get(UserSession, claims["sid"])
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401



def test_access_token_rejects_expired_session(client, farmer):
    from datetime import datetime, timedelta, timezone

    from app.core.security import decode_token
    from app.database import SessionLocal
    from app.models import UserSession

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "farmer1@example.com", "password": PW},
    ).json()["access_token"]

    claims = decode_token(token, "access")

    with SessionLocal() as db:
        session = db.get(UserSession, claims["sid"])
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_register_rolls_back_when_audit_fails(client, monkeypatch):
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import User

    def fail_audit(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Audit unavailable")

    monkeypatch.setattr("app.api.v1.auth.audit", fail_audit)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Audit Failure",
            "email": "audit-failure@example.com",
            "password": PW,
        },
    )
    assert response.status_code == 500

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == "audit-failure@example.com")
        )
        assert user is None

def test_forgot_password_sends_email_in_production(client, monkeypatch):
    from types import SimpleNamespace

    import app.api.v1.auth as auth

    sent = []
    monkeypatch.setattr(auth, "smtp_is_configured", lambda: True)
    monkeypatch.setattr(
        auth,
        "send_password_reset_email",
        lambda email, token: sent.append((email, token)),
    )
    monkeypatch.setattr(
        auth, "get_settings", lambda: SimpleNamespace(ENV="production")
    )

    email = "smtp-success@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "SMTP Success", "email": email, "password": PW},
    ).status_code == 201

    response = client.post("/api/v1/auth/forgot-password", json={"email": email})

    assert response.status_code == 200
    assert "dev_reset_token" not in response.json()
    assert len(sent) == 1
    assert sent[0][0] == email
    assert sent[0][1]


def test_forgot_password_smtp_failure_preserves_generic_response(client, monkeypatch):
    from types import SimpleNamespace

    import app.api.v1.auth as auth

    def fail_delivery(email, token):
        raise auth.smtplib.SMTPException("SMTP unavailable")

    monkeypatch.setattr(auth, "smtp_is_configured", lambda: True)
    monkeypatch.setattr(auth, "send_password_reset_email", fail_delivery)
    monkeypatch.setattr(
        auth, "get_settings", lambda: SimpleNamespace(ENV="production")
    )

    email = "smtp-failure@example.com"
    assert client.post(
        "/api/v1/auth/register",
        json={"full_name": "SMTP Failure", "email": email, "password": PW},
    ).status_code == 201

    existing = client.post("/api/v1/auth/forgot-password", json={"email": email})
    missing = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "not-registered@example.com"},
    )

    assert existing.status_code == missing.status_code == 200
    assert existing.json() == missing.json()
    assert "dev_reset_token" not in existing.json()
