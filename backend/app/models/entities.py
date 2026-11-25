"""SQLAlchemy models. Mirrors the schema in the SDD (Chapter 6).

UUIDs are stored as 36-char strings and JSON columns use JSONB on PostgreSQL,
so the same models work on PostgreSQL (production) and SQLite (tests/dev).
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RoleName(str, enum.Enum):
    farmer = "farmer"
    business = "business"
    advisor = "advisor"
    admin = "admin"
    operator = "operator"


class UserStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class UUIDMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)


class Role(UUIDMixin, Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(32), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class User(UUIDMixin, Base):
    __tablename__ = "users"
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    organization: Mapped[str | None] = mapped_column(String(160))  # business profile
    language: Mapped[str] = mapped_column(String(8), default="en")
    status: Mapped[str] = mapped_column(String(16), default=UserStatus.active.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    roles: Mapped[list[Role]] = relationship(secondary="user_roles", lazy="selectin")

    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]


class UserSession(UUIDMixin, Base):
    """Server-side refresh session; raw refresh tokens are never stored."""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_revoked", "user_id", "revoked_at"),
        Index("ix_user_sessions_expires_at", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(64))

class Farm(UUIDMixin, Base):
    __tablename__ = "farms"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    farm_name: Mapped[str] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(Text)
    area: Mapped[float | None] = mapped_column(Numeric(12, 3))
    area_unit: Mapped[str] = mapped_column(String(16), default="acre")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    fields: Mapped[list["Field"]] = relationship(back_populates="farm", cascade="all, delete-orphan")


class Field(UUIDMixin, Base):
    __tablename__ = "fields"
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    field_name: Mapped[str] = mapped_column(String(160))
    area: Mapped[float | None] = mapped_column(Numeric(12, 3))
    soil_type: Mapped[str | None] = mapped_column(String(64))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    current_crop_id: Mapped[str | None] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"))

    farm: Mapped[Farm] = relationship(back_populates="fields")


class SoilRecord(UUIDMixin, Base):
    __tablename__ = "soil_records"
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), index=True)
    nitrogen: Mapped[float | None] = mapped_column(Numeric(10, 3))
    phosphorus: Mapped[float | None] = mapped_column(Numeric(10, 3))
    potassium: Mapped[float | None] = mapped_column(Numeric(10, 3))
    ph: Mapped[float | None] = mapped_column(Numeric(4, 2))
    organic_matter: Mapped[float | None] = mapped_column(Numeric(6, 3))
    moisture: Mapped[float | None] = mapped_column(Numeric(6, 3))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Crop(UUIDMixin, Base):
    __tablename__ = "crops"
    crop_name: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    growing_season: Mapped[str | None] = mapped_column(String(32))


class ModelVersion(UUIDMixin, Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_name", "version"),)
    model_name: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(32))
    model_type: Mapped[str] = mapped_column(String(64))
    artifact_location: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict | None] = mapped_column(JSONType)
    data_source: Mapped[str | None] = mapped_column(String(64))
    deployment_status: Mapped[str] = mapped_column(String(24), default="staged")  # staged|active|retired
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class _PredictionBase(UUIDMixin):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class CropPrediction(_PredictionBase, Base):
    __tablename__ = "crop_predictions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey("fields.id", ondelete="SET NULL"))
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"))
    input_data: Mapped[dict] = mapped_column(JSONType)
    predicted_crop: Mapped[str] = mapped_column(String(80))
    confidence: Mapped[float] = mapped_column(Numeric(5, 4))
    alternatives: Mapped[list | None] = mapped_column(JSONType)


class DiseasePrediction(_PredictionBase, Base):
    __tablename__ = "disease_predictions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey("fields.id", ondelete="SET NULL"))
    image_path: Mapped[str] = mapped_column(Text)
    predicted_class: Mapped[str] = mapped_column(String(160))
    confidence: Mapped[float] = mapped_column(Numeric(5, 4))
    is_uncertain: Mapped[bool] = mapped_column(Boolean, default=False)
    alternatives: Mapped[list | None] = mapped_column(JSONType)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"))


class YieldPrediction(_PredictionBase, Base):
    __tablename__ = "yield_predictions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey("fields.id", ondelete="SET NULL"))
    crop_id: Mapped[str | None] = mapped_column(ForeignKey("crops.id"))
    crop_name: Mapped[str] = mapped_column(String(80))
    input_data: Mapped[dict] = mapped_column(JSONType)
    predicted_yield: Mapped[float] = mapped_column(Numeric(10, 3))
    yield_low: Mapped[float | None] = mapped_column(Numeric(10, 3))
    yield_high: Mapped[float | None] = mapped_column(Numeric(10, 3))
    yield_unit: Mapped[str] = mapped_column(String(24), default="t/ha")
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"))


class FertilizerRecommendation(_PredictionBase, Base):
    __tablename__ = "fertilizer_recommendations"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey("fields.id", ondelete="SET NULL"))
    crop_name: Mapped[str] = mapped_column(String(80))
    input_data: Mapped[dict] = mapped_column(JSONType)
    recommendation: Mapped[dict] = mapped_column(JSONType)
    ruleset_version: Mapped[str] = mapped_column(String(32))


class AgriculturalActivity(UUIDMixin, Base):
    __tablename__ = "agricultural_activities"
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), index=True)
    activity_type: Mapped[str] = mapped_column(String(48))
    description: Mapped[str | None] = mapped_column(Text)
    activity_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class WeatherRecord(UUIDMixin, Base):
    __tablename__ = "weather_records"
    location: Mapped[str] = mapped_column(Text)
    temperature: Mapped[float | None] = mapped_column(Numeric(5, 2))
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2))
    rainfall: Mapped[float | None] = mapped_column(Numeric(7, 2))
    wind_speed: Mapped[float | None] = mapped_column(Numeric(6, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    source: Mapped[str] = mapped_column(String(48))


class Notification(UUIDMixin, Base):
    __tablename__ = "notifications"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditLog(UUIDMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_created", "created_at"),)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

