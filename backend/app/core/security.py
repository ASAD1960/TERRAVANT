from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_ph = PasswordHasher()
_DUMMY_PASSWORD_HASH = _ph.hash(uuid4().hex)
_RESERVED_CLAIMS = {"sub", "type", "iat", "exp", "jti"}


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def _make_token(
    sub: str,
    kind: str,
    expires: timedelta,
    extra: dict | None = None,
) -> str:
    extra = extra or {}
    if _RESERVED_CLAIMS.intersection(extra):
        raise ValueError("Extra claims cannot override reserved JWT claims")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "type": kind,
        "iat": now,
        "exp": now + expires,
        "jti": uuid4().hex,
        **extra,
    }
    return jwt.encode(
        payload,
        get_settings().SECRET_KEY,
        algorithm="HS256",
    )


def create_access_token(user_id: str, session_id: str) -> str:
    return _make_token(
        user_id,
        "access",
        timedelta(minutes=get_settings().ACCESS_TOKEN_MINUTES),
        {"sid": session_id},
    )


def create_refresh_token(user_id: str, session_id: str) -> str:
    return _make_token(
        user_id,
        "refresh",
        timedelta(days=get_settings().REFRESH_TOKEN_DAYS),
        {"sid": session_id},
    )


def create_reset_token(user_id: str, pw_fingerprint: str) -> str:
    return _make_token(
        user_id,
        "reset",
        timedelta(minutes=get_settings().RESET_TOKEN_MINUTES),
        {"pwf": pw_fingerprint},
    )


def decode_token(token: str, expected_type: str) -> dict:
    """Decode a JWT and enforce its required claim structure."""
    data = jwt.decode(
        token,
        get_settings().SECRET_KEY,
        algorithms=["HS256"],
        options={
            "require": ["sub", "type", "iat", "exp", "jti"],
        },
    )

    if data.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")

    if not all(
        isinstance(data.get(key), str) and data[key].strip()
        for key in ("sub", "type", "jti")
    ):
        raise jwt.InvalidTokenError("invalid token claims")

    if not isinstance(data.get("iat"), (int, float)):
        raise jwt.InvalidTokenError("invalid issued-at claim")

    if not isinstance(data.get("exp"), (int, float)):
        raise jwt.InvalidTokenError("invalid expiration claim")

    return data
