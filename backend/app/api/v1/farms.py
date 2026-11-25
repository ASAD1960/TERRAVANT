from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_farm, get_owned_field, is_admin
from app.database import get_db
from app.models import AgriculturalActivity, Crop, Farm, Field, SoilRecord, User
from app.schemas.common import Message
from app.schemas.farm import (
    ActivityIn,
    ActivityOut,
    CropOut,
    FarmDetail,
    FarmIn,
    FarmOut,
    FarmUpdate,
    FieldIn,
    FieldOut,
    FieldUpdate,
    SoilIn,
    SoilOut,
)
from app.services.audit import audit

router = APIRouter(tags=["farms"])


@router.get("/farms", response_model=list[FarmOut])
def list_farms(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Farm).order_by(Farm.created_at.desc()).offset(skip).limit(limit)
    if not is_admin(user):
        q = q.where(Farm.owner_id == user.id)
    return db.scalars(q).all()


@router.post("/farms", response_model=FarmOut, status_code=201)
def create_farm(body: FarmIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = Farm(owner_id=user.id, **body.model_dump())
    db.add(farm)
    db.commit()
    return farm


@router.get("/farms/{farm_id}", response_model=FarmDetail)
def get_farm(farm_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned_farm(db, user, farm_id)


@router.put("/farms/{farm_id}", response_model=FarmOut)
def update_farm(farm_id: str, body: FarmUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = get_owned_farm(db, user, farm_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(farm, k, v)
    db.commit()
    return farm


@router.delete("/farms/{farm_id}", response_model=Message)
def delete_farm(farm_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farm = get_owned_farm(db, user, farm_id)
    db.delete(farm)
    audit(db, user.id, "farm.delete", "farms", {"farm_id": farm_id})
    db.commit()
    return Message(message="Farm deleted")


@router.get("/fields", response_model=list[FieldOut])
def list_fields(farm_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Field).join(Farm)
    if farm_id:
        get_owned_farm(db, user, farm_id)
        q = q.where(Field.farm_id == farm_id)
    elif not is_admin(user):
        q = q.where(Farm.owner_id == user.id)
    return db.scalars(q).all()


@router.post("/fields", response_model=FieldOut, status_code=201)
def create_field(body: FieldIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_owned_farm(db, user, body.farm_id)
    field = Field(**body.model_dump())
    db.add(field)
    db.commit()
    return field


@router.put("/fields/{field_id}", response_model=FieldOut)
def update_field(field_id: str, body: FieldUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    field = get_owned_field(db, user, field_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(field, k, v)
    db.commit()
    return field


@router.delete("/fields/{field_id}", response_model=Message)
def delete_field(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_owned_field(db, user, field_id))
    db.commit()
    return Message(message="Field deleted")


@router.post("/fields/{field_id}/soil", response_model=SoilOut, status_code=201)
def add_soil(field_id: str, body: SoilIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_owned_field(db, user, field_id)
    rec = SoilRecord(field_id=field_id, **body.model_dump())
    db.add(rec)
    db.commit()
    return rec


@router.get("/fields/{field_id}/soil", response_model=list[SoilOut])
def list_soil(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_owned_field(db, user, field_id)
    return db.scalars(select(SoilRecord).where(SoilRecord.field_id == field_id).order_by(SoilRecord.recorded_at.desc())).all()


@router.post("/fields/{field_id}/activities", response_model=ActivityOut, status_code=201)
def add_activity(field_id: str, body: ActivityIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_owned_field(db, user, field_id)
    act = AgriculturalActivity(field_id=field_id, **body.model_dump())
    db.add(act)
    db.commit()
    return act


@router.get("/fields/{field_id}/activities", response_model=list[ActivityOut])
def list_activities(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_owned_field(db, user, field_id)
    return db.scalars(select(AgriculturalActivity).where(AgriculturalActivity.field_id == field_id)
                      .order_by(AgriculturalActivity.activity_date.desc())).all()


@router.get("/crops", response_model=list[CropOut])
def list_crops(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Crop).order_by(Crop.crop_name)).all()
