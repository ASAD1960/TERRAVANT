from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORM


def _validate_password_strength(value: str) -> str:
    if not (
        any(char.isalpha() for char in value)
        and any(char.isdigit() for char in value)
    ):
        raise ValueError("Password must contain letters and numbers")
    return value


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    account_type: str = Field(default="farmer", pattern="^(farmer|business)$")
    organization: str | None = Field(default=None, max_length=160)

    _strength = field_validator("password")(_validate_password_strength)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)

    _strength = field_validator("new_password")(_validate_password_strength)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: str
    full_name: str
    email: EmailStr
    phone: str | None
    organization: str | None
    language: str
    status: str
    role_names: list[str]
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=32)
    organization: str | None = Field(default=None, max_length=160)
    language: str | None = Field(default=None, pattern="^(en|ur)$")

    @field_validator("full_name", "language", mode="before")
    @classmethod
    def _reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value
