from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_field
from app.database import get_db
from app.integrations import weather as wx
from app.models import User

router = APIRouter(prefix="/weather", tags=["weather"])
# Default: Lahore, Punjab
DEFAULT = (31.5204, 74.3587)


def _coords(db: Session, user: User, field_id: str | None, lat: float | None, lon: float | None):
    if (lat is None) != (lon is None):
        raise HTTPException(422, "Latitude and longitude must be provided together.")
    if field_id:
        f = get_owned_field(db, user, field_id)
        if f.latitude is not None and f.longitude is not None:
            return float(f.latitude), float(f.longitude)
        raise HTTPException(422, "This field has no coordinates. Add latitude/longitude to the field.")
    if lat is not None and lon is not None:
        return lat, lon
    return DEFAULT


def _wrap(fn, *a):
    try:
        return fn(*a)
    except wx.WeatherUnavailable as e:
        raise HTTPException(503, str(e))


@router.get("/current")
def current(field_id: str | None = None, lat: float | None = Query(None, ge=-90, le=90), lon: float | None = Query(None, ge=-180, le=180),
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    la, lo = _coords(db, user, field_id, lat, lon)
    d = _wrap(wx.current_and_forecast, la, lo, 1)
    return {"latitude": la, "longitude": lo, "source": d["source"], "stale": d["stale"], "current": d["current"]}


@router.get("/forecast")
def forecast(field_id: str | None = None, days: int = Query(7, ge=1, le=14),
             lat: float | None = Query(None, ge=-90, le=90), lon: float | None = Query(None, ge=-180, le=180),
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    la, lo = _coords(db, user, field_id, lat, lon)
    d = _wrap(wx.current_and_forecast, la, lo, days)
    d["latitude"], d["longitude"] = la, lo
    d["advisories"] = _advisories(d["forecast"])
    return d


@router.get("/history")
def history(field_id: str | None = None, days: int = Query(30, ge=1, le=365),
            lat: float | None = Query(None, ge=-90, le=90), lon: float | None = Query(None, ge=-180, le=180),
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    la, lo = _coords(db, user, field_id, lat, lon)
    end = date.today() - timedelta(days=2)  # archive lags a couple of days
    return _wrap(wx.history, la, lo, (end - timedelta(days=days)).isoformat(), end.isoformat())


def _advisories(forecast: list[dict]) -> list[str]:
    out = []
    for d in forecast[:5]:
        if (d.get("t_max") or 0) >= 42:
            out.append(f"{d['date']}: extreme heat expected ({d['t_max']}°C). Consider irrigation timing and heat stress.")
        if (d.get("rain_mm") or 0) >= 25:
            out.append(f"{d['date']}: heavy rain expected ({d['rain_mm']} mm). Consider delaying spraying/fertilizer application.")
        if (d.get("t_min") is not None) and d["t_min"] <= 2:
            out.append(f"{d['date']}: frost risk (min {d['t_min']}°C) for sensitive crops.")
    return out
