import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, is_admin
from app.database import get_db
from app.models import CropPrediction, DiseasePrediction, Farm, Field, Notification, User, YieldPrediction

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _farm_filter(user: User):
    return [] if is_admin(user) else [Farm.owner_id == user.id]


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ff = _farm_filter(user)
    farms = db.scalar(select(func.count(Farm.id)).where(*ff)) or 0
    area = sum(
        float(f.area or 0) * {
            "acre": 1,
            "hectare": 2.47105,
            "kanal": 0.125,
            "marla": 0.00625,
        }.get(f.area_unit, 1)
        for f in db.scalars(select(Farm).where(*ff))
    )
    fields = db.scalar(select(func.count(Field.id)).join(Farm).where(*ff)) or 0
    uf = [] if is_admin(user) else None

    def cnt(model):
        q = select(func.count(model.id))
        return db.scalar(q if uf == [] else q.where(model.user_id == user.id)) or 0

    def recent(model, label, text):
        q = select(model).order_by(model.created_at.desc()).limit(5)
        if uf is None:
            q = q.where(model.user_id == user.id)
        return [{"type": label, "id": r.id, "summary": text(r), "created_at": r.created_at} for r in db.scalars(q)]

    recents = (
        recent(CropPrediction, "crop", lambda r: f"{r.predicted_crop} ({float(r.confidence):.0%})")
        + recent(DiseasePrediction, "disease", lambda r: "Uncertain" if r.is_uncertain else r.predicted_class)
        + recent(YieldPrediction, "yield", lambda r: f"{r.crop_name}: {float(r.predicted_yield):.2f} {r.yield_unit}")
    )
    recents.sort(key=lambda r: r["created_at"], reverse=True)
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.is_read.is_(False))) or 0
    return {
        "total_farms": farms, "total_area": round(area, 2), "area_unit": "acre", "total_fields": fields,
        "prediction_counts": {"crop": cnt(CropPrediction), "disease": cnt(DiseasePrediction), "yield": cnt(YieldPrediction)},
        "recent_predictions": recents[:8], "unread_notifications": unread,
    }


@router.get("/farms")
def farm_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = (select(Farm.id, Farm.farm_name, Farm.area, Farm.area_unit, func.count(Field.id))
         .outerjoin(Field).where(*_farm_filter(user)).group_by(Farm.id))
    return [{"farm_id": i, "farm_name": n, "area": float(a) if a else None, "area_unit": u, "field_count": c}
            for i, n, a, u, c in db.execute(q)]


@router.get("/crops")
def crop_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(CropPrediction.predicted_crop, func.count(CropPrediction.id)).group_by(CropPrediction.predicted_crop)
    if not is_admin(user):
        q = q.where(CropPrediction.user_id == user.id)
    rec = [{"crop": c, "recommendations": n} for c, n in db.execute(q)]
    yq = select(YieldPrediction.crop_name, func.avg(YieldPrediction.predicted_yield)).group_by(YieldPrediction.crop_name)
    if not is_admin(user):
        yq = yq.where(YieldPrediction.user_id == user.id)
    return {"recommendation_counts": rec, "average_predicted_yield": [{"crop": c, "t_per_ha": round(float(v), 3)} for c, v in db.execute(yq)]}


@router.get("/reports")
def report_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """CSV export of the user's farm/field inventory."""
    q = select(Farm.farm_name, Farm.location, Farm.area, Farm.area_unit, Field.field_name, Field.area, Field.soil_type)\
        .outerjoin(Field).where(*_farm_filter(user)).order_by(Farm.farm_name)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["farm", "location", "farm_area", "unit", "field", "field_area", "soil_type"])
    for row in db.execute(q):
        w.writerow(["" if v is None else v for v in row])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=terravant_farms.csv"})


@router.get("/notifications", tags=["notifications"])
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50))
    return [{"id": n.id, "title": n.title, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in rows]


@router.post("/notifications/{nid}/read", tags=["notifications"])
def mark_read(nid: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, nid)
    if n and n.user_id == user.id:
        n.is_read = True
        db.commit()
    return {"message": "ok"}
