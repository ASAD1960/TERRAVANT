from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORM


class CropPredictIn(BaseModel):
    field_id: str | None = None
    nitrogen: float = Field(ge=0, le=300, description="Soil N (kg/ha index)")
    phosphorus: float = Field(ge=0, le=300)
    potassium: float = Field(ge=0, le=300)
    temperature: float = Field(ge=-10, le=55, description="Mean temperature, °C")
    humidity: float = Field(ge=0, le=100, description="Relative humidity, %")
    ph: float = Field(ge=3, le=11)
    rainfall: float = Field(ge=0, le=3000, description="Rainfall, mm")


class Alternative(BaseModel):
    label: str
    probability: float


class Explanation(BaseModel):
    method: str
    top_factors: list[dict]


class CropPredictOut(BaseModel):
    prediction_id: str
    predicted_crop: str
    confidence: float
    alternatives: list[Alternative]
    explanation: Explanation
    model_version: str
    data_source: str
    limitations: list[str]
    status: str = "success"


class CropPredictionRow(ORM):
    id: str
    field_id: str | None
    predicted_crop: str
    confidence: float
    alternatives: list | None
    input_data: dict
    created_at: datetime


class DiseaseOut(BaseModel):
    prediction_id: str
    predicted_class: str
    confidence: float
    is_uncertain: bool
    alternatives: list[Alternative]
    model_version: str
    data_source: str
    message: str
    limitations: list[str]


class DiseasePredictionRow(ORM):
    id: str
    field_id: str | None
    predicted_class: str
    confidence: float
    is_uncertain: bool
    alternatives: list | None
    created_at: datetime


class YieldPredictIn(BaseModel):
    field_id: str | None = None
    crop_name: str = Field(min_length=2, max_length=80)
    area_ha: float = Field(gt=0, le=100_000)
    rainfall: float = Field(ge=0, le=3000)
    temperature: float = Field(ge=-10, le=55)
    irrigated: bool = True
    fertilizer_kg_ha: float = Field(ge=0, le=1500)
    soil_ph: float = Field(default=7.5, ge=3, le=11)


class YieldOut(BaseModel):
    prediction_id: str
    crop_name: str
    yield_per_ha: float
    yield_low: float
    yield_high: float
    total_production: float
    yield_unit: str
    interval_note: str
    model_version: str
    data_source: str
    limitations: list[str]


class YieldPredictionRow(ORM):
    id: str
    field_id: str | None
    crop_name: str
    predicted_yield: float
    yield_low: float | None
    yield_high: float | None
    yield_unit: str
    created_at: datetime


class FertilizerIn(BaseModel):
    field_id: str | None = None
    crop_name: str = Field(min_length=2, max_length=80)
    nitrogen: float | None = Field(default=None, ge=0, le=2000)
    phosphorus: float | None = Field(default=None, ge=0, le=2000)
    potassium: float | None = Field(default=None, ge=0, le=5000)
    ph: float | None = Field(default=None, ge=3, le=11)
    growth_stage: str | None = Field(default=None, max_length=48)


class FertilizerOut(BaseModel):
    recommendation_id: str
    crop_name: str
    nutrient_status: dict[str, dict]
    ph_status: dict | None
    guidance: list[str]
    needs_lab_test: bool
    lab_test_reasons: list[str]
    ruleset_version: str
    disclaimer: str


class FertilizerRow(ORM):
    id: str
    field_id: str | None
    crop_name: str
    recommendation: dict
    created_at: datetime
