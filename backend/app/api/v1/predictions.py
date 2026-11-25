
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_field, is_admin
from app.core.config import get_settings
from app.database import get_db
from app.ml import disease as disease_ml
from app.ml import fertilizer as fert
from app.ml import registry as ml
from app.models import (
    Crop,
    CropPrediction,
    DiseasePrediction,
    FertilizerRecommendation,
    Notification,
    User,
    YieldPrediction,
)
from app.schemas.prediction import (
    CropPredictIn,
    CropPredictionRow,
    CropPredictOut,
    DiseaseOut,
    DiseasePredictionRow,
    FertilizerIn,
    FertilizerOut,
    FertilizerRow,
    YieldOut,
    YieldPredictIn,
    YieldPredictionRow,
)
from app.services.model_sync import version_row

router = APIRouter(tags=["predictions"])


def _unavailable(e: Exception):
    return HTTPException(503, str(e))


def _owned(model, user: User):
    return model.user_id == user.id if not is_admin(user) else True


def _check_field(db, user, field_id):
    if field_id:
        get_owned_field(db, user, field_id)


# ---------- crop recommendation ----------

@router.post("/predictions/crop", response_model=CropPredictOut)
def crop_predict(
    body: CropPredictIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_field(db, user, body.field_id)
    feats = body.model_dump(exclude={"field_id"})

    try:
        res = ml.predict_crop(feats)
    except ml.ModelUnavailable as e:
        raise _unavailable(e) from e

    mv = version_row(db, res["model_name"], res["model_version"])

    row = CropPrediction(
        user_id=user.id,
        field_id=body.field_id,
        model_version_id=mv.id,
        input_data=feats,
        predicted_crop=res["predicted_crop"],
        confidence=res["confidence"],
        alternatives=res["alternatives"],
    )

    db.add(row)
    db.add(
        Notification(
            user_id=user.id,
            title="Crop recommendation ready",
            message=(
                f"Top suggestion: {res['predicted_crop']} "
                f"({res['confidence']:.0%} model confidence)."
            ),
        )
    )
    db.commit()

    return CropPredictOut(
        prediction_id=row.id,
        **{
            k: res[k]
            for k in (
                "predicted_crop",
                "confidence",
                "alternatives",
                "explanation",
                "model_version",
                "data_source",
                "limitations",
            )
        },
    )


@router.get("/predictions/crop", response_model=list[CropPredictionRow])
def crop_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        select(CropPrediction)
        .order_by(CropPrediction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if not is_admin(user):
        q = q.where(CropPrediction.user_id == user.id)

    return db.scalars(q).all()


@router.get("/predictions/crop/{pid}", response_model=CropPredictionRow)
def crop_get(
    pid: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(CropPrediction, pid)
    if not row or not _owned(row, user):
        raise HTTPException(404, "Prediction not found")

    return row


# ---------- disease detection ----------

@router.post("/predictions/disease", response_model=DiseaseOut)
async def disease_predict(
    file: UploadFile = File(...),
    field_id: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    _check_field(db, user, field_id)

    raw = await file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)

    if len(raw) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            413,
            f"Image exceeds {settings.MAX_UPLOAD_MB} MB",
        )

    try:
        img = disease_ml.validate_image(raw)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e

    try:
        res = disease_ml.predict_disease(img)
    except ml.ModelUnavailable as e:
        raise _unavailable(e) from e

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(settings.UPLOAD_DIR) / f"{uuid.uuid4().hex}.jpg"
    img.save(path, "JPEG", quality=90)

    try:
        mv = version_row(db, "disease_detection", res["model_version"])

        row = DiseasePrediction(
            user_id=user.id,
            field_id=field_id,
            image_path=str(path),
            predicted_class=res["predicted_class"],
            confidence=res["confidence"],
            is_uncertain=res["is_uncertain"],
            alternatives=res["alternatives"],
            model_version_id=mv.id,
        )

        db.add(row)
        db.commit()

        return DiseaseOut(
            prediction_id=row.id,
            **{
                k: res[k]
                for k in (
                    "predicted_class",
                    "confidence",
                    "is_uncertain",
                    "alternatives",
                    "model_version",
                    "data_source",
                    "message",
                    "limitations",
                )
            },
        )

    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


@router.get("/predictions/disease", response_model=list[DiseasePredictionRow])
def disease_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        select(DiseasePrediction)
        .order_by(DiseasePrediction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if not is_admin(user):
        q = q.where(DiseasePrediction.user_id == user.id)

    return db.scalars(q).all()


@router.get("/predictions/disease/{pid}", response_model=DiseasePredictionRow)
def disease_get(
    pid: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(DiseasePrediction, pid)
    if not row or not _owned(row, user):
        raise HTTPException(404, "Prediction not found")

    return row


# ---------- yield prediction ----------

@router.post("/predictions/yield", response_model=YieldOut)
def yield_predict(
    body: YieldPredictIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_field(db, user, body.field_id)

    try:
        res = ml.predict_yield(body.model_dump())
    except ml.ModelUnavailable as e:
        raise _unavailable(e) from e

    mv = version_row(db, res["model_name"], res["model_version"])

    crop = db.scalar(
        select(Crop).where(
            Crop.crop_name == body.crop_name.strip().lower()
        )
    )

    row = YieldPrediction(
        user_id=user.id,
        field_id=body.field_id,
        crop_id=crop.id if crop else None,
        crop_name=body.crop_name.strip().lower(),
        input_data=body.model_dump(exclude={"field_id"}),
        predicted_yield=res["yield_per_ha"],
        yield_low=res["yield_low"],
        yield_high=res["yield_high"],
        yield_unit=res["yield_unit"],
        model_version_id=mv.id,
    )

    db.add(row)
    db.commit()

    return YieldOut(
        prediction_id=row.id,
        crop_name=row.crop_name,
        **{
            k: res[k]
            for k in (
                "yield_per_ha",
                "yield_low",
                "yield_high",
                "total_production",
                "yield_unit",
                "interval_note",
                "model_version",
                "data_source",
                "limitations",
            )
        },
    )


@router.get("/predictions/yield", response_model=list[YieldPredictionRow])
def yield_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        select(YieldPrediction)
        .order_by(YieldPrediction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if not is_admin(user):
        q = q.where(YieldPrediction.user_id == user.id)

    return db.scalars(q).all()


@router.get("/predictions/yield/{pid}", response_model=YieldPredictionRow)
def yield_get(
    pid: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(YieldPrediction, pid)
    if not row or not _owned(row, user):
        raise HTTPException(404, "Prediction not found")

    return row


# ---------- fertilizer recommendation ----------

@router.post(
    "/recommendations/fertilizer",
    response_model=FertilizerOut,
)
def fertilizer(
    body: FertilizerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_field(db, user, body.field_id)

    try:
        res = fert.recommend(
            body.crop_name,
            body.nitrogen,
            body.phosphorus,
            body.potassium,
            body.ph,
            body.growth_stage,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        ) from e

    try:
        row = FertilizerRecommendation(
            user_id=user.id,
            field_id=body.field_id,
            crop_name=body.crop_name.strip().lower(),
            input_data=body.model_dump(exclude={"field_id"}),
            recommendation=res,
            ruleset_version=res["ruleset_version"],
        )

        db.add(row)
        db.commit()
        db.refresh(row)

    except Exception:
        db.rollback()
        raise

    return FertilizerOut(
        recommendation_id=row.id,
        crop_name=row.crop_name,
        **res,
    )


@router.get(
    "/recommendations/fertilizer",
    response_model=list[FertilizerRow],
)
def fertilizer_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        select(FertilizerRecommendation)
        .order_by(FertilizerRecommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if not is_admin(user):
        q = q.where(FertilizerRecommendation.user_id == user.id)

    return db.scalars(q).all()
