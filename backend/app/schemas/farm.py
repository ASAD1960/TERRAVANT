from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORM


class FarmIn(BaseModel):
    farm_name: str = Field(min_length=2, max_length=160)
    location: str | None = None
    area: float | None = Field(default=None, gt=0, le=1_000_000)
    area_unit: str = Field(default="acre", pattern="^(acre|hectare|kanal|marla)$")


class FarmUpdate(BaseModel):
    @field_validator("farm_name", "area_unit", mode="before")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value

    farm_name: str | None = Field(default=None, min_length=2, max_length=160)
    location: str | None = None
    area: float | None = Field(default=None, gt=0, le=1_000_000)
    area_unit: str | None = Field(default=None, pattern="^(acre|hectare|kanal|marla)$")


class FieldIn(BaseModel):
    farm_id: str
    field_name: str = Field(min_length=1, max_length=160)
    area: float | None = Field(default=None, gt=0, le=1_000_000)
    soil_type: str | None = Field(default=None, max_length=64)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    current_crop_id: str | None = None


class FieldUpdate(BaseModel):
    @field_validator("field_name", mode="before")
    @classmethod
    def reject_null_field_name(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value

    field_name: str | None = Field(default=None, min_length=1, max_length=160)
    area: float | None = Field(default=None, gt=0, le=1_000_000)
    soil_type: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    current_crop_id: str | None = None


class FieldOut(ORM):
    id: str
    farm_id: str
    field_name: str
    area: float | None
    soil_type: str | None
    latitude: float | None
    longitude: float | None
    current_crop_id: str | None


class FarmOut(ORM):
    id: str
    owner_id: str
    farm_name: str
    location: str | None
    area: float | None
    area_unit: str
    created_at: datetime


class FarmDetail(FarmOut):
    fields: list[FieldOut] = []


class SoilIn(BaseModel):
    nitrogen: float | None = Field(default=None, ge=0, le=2000)
    phosphorus: float | None = Field(default=None, ge=0, le=2000)
    potassium: float | None = Field(default=None, ge=0, le=5000)
    ph: float | None = Field(default=None, ge=3, le=11)
    organic_matter: float | None = Field(default=None, ge=0, le=100)
    moisture: float | None = Field(default=None, ge=0, le=100)


class SoilOut(SoilIn, ORM):
    id: str
    field_id: str
    recorded_at: datetime


class ActivityIn(BaseModel):
    activity_type: str = Field(min_length=2, max_length=48)
    description: str | None = Field(default=None, max_length=2000)
    activity_date: date


class ActivityOut(ActivityIn, ORM):
    id: str
    field_id: str


class CropOut(ORM):
    id: str
    crop_name: str
    category: str | None
    description: str | None
    growing_season: str | None
