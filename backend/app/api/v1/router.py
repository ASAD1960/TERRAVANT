from fastapi import APIRouter

from app.api.v1 import admin, analytics, auth, farms, predictions, weather

api_router = APIRouter()
for r in (auth.router, farms.router, predictions.router, weather.router, analytics.router, admin.router):
    api_router.include_router(r)
