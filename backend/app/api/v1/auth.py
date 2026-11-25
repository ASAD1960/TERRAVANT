import hashlib
import logging
import smtplib
from datetime import datetime, timezone
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_session, get_current_user
from app.core.config import get_settings
from app.core.security import (
    _DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.middleware.rate_limit import auth_rate_limit
from app.models import Role, User, UserSession, UserStatus
from app.schemas.common import Message
from app.schemas.user import (
    ForgotIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    ResetIn,
    TokenOut,
    UserOut,
    UserUpdate,
)
from app.services.audit import audit
from app.services.email import send_password_reset_email, smtp_is_configured

log = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= _utc_now()


def _tokens(db: Session, user: User) -> TokenOut:
    session_id = str(uuid4())
    access_token = create_access_token(user.id, session_id)
    refresh_token = create_refresh_token(user.id, session_id)
    refresh_data = decode_token(refresh_token, "refresh")

    db.add(
        UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=_token_hash(refresh_token),
            expires_at=datetime.fromtimestamp(
                refresh_data["exp"],
                tz=timezone.utc,
            ),
        )
    )
    db.flush()

    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def _revoke_session(
    db: Session,
    user_session: UserSession,
    reason: str,
) -> None:
    user_session.revoked_at = _utc_now()
    user_session.revocation_reason = reason
    db.flush()


@router.post(
    "/auth/register",
    response_model=UserOut,
    status_code=201,
    dependencies=[Depends(auth_rate_limit)],
)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "An account with this email already exists")

    role = db.scalar(select(Role).where(Role.name == body.account_type))
    user = User(
        full_name=body.full_name,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        phone=body.phone,
        organization=body.organization,
        roles=[role],
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User.id).where(User.email == body.email.lower())):
            raise HTTPException(409, "An account with this email already exists")
        raise

    audit(db, user.id, "user.register", "users", {"account_type": body.account_type})
    db.commit()
    return user


@router.post(
    "/auth/login",
    response_model=TokenOut,
    dependencies=[Depends(auth_rate_limit)],
)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))

    # Verify a dummy Argon2 hash for unknown accounts to reduce timing-based enumeration.
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_valid = verify_password(body.password, password_hash)

    if (
        not user
        or not password_valid
        or user.status != UserStatus.active.value
    ):
        audit(
            db,
            user.id if user else None,
            "auth.login_failed",
            "users",
            {"email": body.email.lower()},
        )
        db.commit()
        raise HTTPException(401, "Invalid email or password")

    tokens = _tokens(db, user)
    audit(db, user.id, "auth.login", "users")
    db.commit()
    return tokens


@router.post(
    "/auth/refresh",
    response_model=TokenOut,
    dependencies=[Depends(auth_rate_limit)],
)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    try:
        data = decode_token(body.refresh_token, "refresh")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired refresh token")

    user_id = data.get("sub")
    session_id = data.get("sid")
    token_id = data.get("jti")

    if not all(
        isinstance(value, str) and value
        for value in (user_id, session_id, token_id)
    ):
        raise HTTPException(401, "Invalid or expired refresh token")

    user = db.get(User, user_id)
    if not user or user.status != UserStatus.active.value:
        raise HTTPException(401, "Account not available")

    user_session = db.get(UserSession, session_id)
    if (
        not user_session
        or user_session.user_id != user.id
        or user_session.revoked_at is not None
        or _is_expired(user_session.expires_at)
    ):
        raise HTTPException(401, "Session not available")

    old_hash = _token_hash(body.refresh_token)

    # A validly signed but previously rotated token indicates possible reuse.
    if user_session.refresh_token_hash != old_hash:
        _revoke_session(db, user_session, "refresh_token_reuse")
        audit(db, user.id, "auth.refresh_reuse", "users")
        db.commit()
        raise HTTPException(401, "Refresh token reuse detected")

    new_access_token = create_access_token(user.id, session_id)
    new_refresh_token = create_refresh_token(user.id, session_id)
    new_refresh_data = decode_token(new_refresh_token, "refresh")
    now = _utc_now()

    # Compare-and-swap: only one request can rotate the current token.
    result = db.execute(
        update(UserSession)
        .where(
            UserSession.id == session_id,
            UserSession.user_id == user.id,
            UserSession.refresh_token_hash == old_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        .values(
            refresh_token_hash=_token_hash(new_refresh_token),
            expires_at=datetime.fromtimestamp(
                new_refresh_data["exp"],
                tz=timezone.utc,
            ),
            last_used_at=now,
        )
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        db.rollback()
        current_session = db.get(UserSession, session_id)

        if (
            current_session
            and current_session.user_id == user.id
            and current_session.revoked_at is None
            and not _is_expired(current_session.expires_at)
            and current_session.refresh_token_hash != old_hash
        ):
            _revoke_session(db, current_session, "refresh_token_reuse")
            audit(db, user.id, "auth.refresh_reuse", "users")
            db.commit()

        raise HTTPException(401, "Refresh token is no longer valid")

    audit(db, user.id, "auth.refresh", "users")
    db.commit()

    return TokenOut(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/auth/logout", response_model=Message)
def logout(
    user: User = Depends(get_current_user),
    user_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    _revoke_session(db, user_session, "logout")
    audit(db, user.id, "auth.logout", "users")
    db.commit()
    return Message(message="Logged out")


@router.post(
    "/auth/forgot-password",
    dependencies=[Depends(auth_rate_limit)],
)
def forgot(body: ForgotIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    out: dict = {
        "message": "If the account exists, a reset link has been sent."
    }

    if user:
        token = create_reset_token(
            user.id,
            hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest(),
        )
        settings = get_settings()

        if smtp_is_configured():
            try:
                send_password_reset_email(user.email, token)
            except (OSError, smtplib.SMTPException, RuntimeError):
                log.exception("Password reset email delivery failed")

        if settings.ENV in ("development", "test"):
            out["dev_reset_token"] = token  # never returned in production

    return out


@router.post(
    "/auth/reset-password",
    response_model=Message,
    dependencies=[Depends(auth_rate_limit)],
)
def reset(body: ResetIn, db: Session = Depends(get_db)):
    try:
        data = decode_token(body.token, "reset")
    except jwt.PyJWTError:
        raise HTTPException(400, "Invalid or expired reset token")

    user = db.get(User, data["sub"])
    if not user or hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest() != data.get("pwf"):
        raise HTTPException(400, "Invalid or expired reset token")

    now = _utc_now()
    previous_password_hash = user.password_hash
    result = db.execute(
        update(User)
        .where(
            User.id == user.id,
            User.password_hash == previous_password_hash,
        )
        .values(password_hash=hash_password(body.new_password))
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(400, "Invalid or expired reset token")

    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=now,
            revocation_reason="password_reset",
        )
        .execution_options(synchronize_session=False)
    )
    audit(db, user.id, "auth.password_reset", "users")
    db.commit()
    return Message(message="Password updated")


@router.get("/users/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/users/me", response_model=UserOut)
def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    return user
