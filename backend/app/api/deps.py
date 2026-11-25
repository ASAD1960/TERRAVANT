from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import Farm, Field, User, UserSession, UserStatus

bearer = HTTPBearer(auto_error=False)


def get_current_session(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserSession:
    if not creds:
        raise HTTPException(
            401,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        data = decode_token(creds.credentials, "access")
    except jwt.PyJWTError:
        raise HTTPException(
            401,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = data.get("sub")
    session_id = data.get("sid")
    token_id = data.get("jti")

    if not all(isinstance(value, str) and value for value in (user_id, session_id, token_id)):
        raise HTTPException(401, "Invalid or expired token")

    user_session = db.get(UserSession, session_id)
    if (
        not user_session
        or user_session.user_id != user_id
        or user_session.revoked_at is not None
    ):
        raise HTTPException(401, "Session not available")

    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(401, "Session expired")

    return user_session


def get_current_user(
    user_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_session.user_id)
    if not user or user.status != UserStatus.active.value:
        raise HTTPException(401, "Account not available")
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not set(roles) & set(user.role_names):
            raise HTTPException(403, "You do not have permission for this action")
        return user

    return checker


def is_admin(user: User) -> bool:
    return "admin" in user.role_names


def get_owned_farm(db: Session, user: User, farm_id: str) -> Farm:
    farm = db.get(Farm, farm_id)
    # 404 (not 403) so record existence is not leaked across owners.
    if not farm or (farm.owner_id != user.id and not is_admin(user)):
        raise HTTPException(404, "Farm not found")
    return farm


def get_owned_field(db: Session, user: User, field_id: str) -> Field:
    field = db.get(Field, field_id)
    if not field:
        raise HTTPException(404, "Field not found")
    get_owned_farm(db, user, field.farm_id)
    return field
