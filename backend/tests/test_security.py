import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    _make_token,
    create_access_token,
    decode_token,
)


def test_access_token_contains_required_claims():
    token = create_access_token("user-1", "session-1")
    claims = decode_token(token, "access")

    assert claims["sub"] == "user-1"
    assert claims["sid"] == "session-1"
    assert claims["type"] == "access"
    assert claims["jti"]
    assert claims["iat"]
    assert claims["exp"]


def test_decode_rejects_wrong_token_type():
    token = create_access_token("user-1", "session-1")

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, "refresh")


@pytest.mark.parametrize(
    "claims",
    [
        {"type": "access", "iat": 1, "exp": 9999999999, "jti": "id"},
        {"sub": "user-1", "iat": 1, "exp": 9999999999, "jti": "id"},
        {"sub": "user-1", "type": "access", "exp": 9999999999, "jti": "id"},
        {"sub": "user-1", "type": "access", "iat": 1, "jti": "id"},
        {"sub": "user-1", "type": "access", "iat": 1, "exp": 9999999999},
    ],
)
def test_decode_rejects_missing_required_claims(claims):
    token = jwt.encode(
        claims,
        get_settings().SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, "access")


def test_token_extra_cannot_override_reserved_claims():
    with pytest.raises(ValueError):
        _make_token(
            "user-1",
            "access",
            __import__("datetime").timedelta(minutes=5),
            {"sub": "attacker"},
        )
