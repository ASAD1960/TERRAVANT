import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database import Base, SessionLocal, engine
from app.middleware.rate_limit import (
    close_rate_limiter,
    initialize_rate_limiter,
    rate_limiter_ready,
)
from app.middleware.request_log import RequestLogMiddleware
from app.ml.registry import registry
from app.services.model_sync import sync_model_versions
from app.services.seed import seed_reference_data

settings = get_settings()
setup_logging()
log = logging.getLogger("terravant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_rate_limiter()
    try:
        if settings.ENV != "production":
            Base.metadata.create_all(engine)  # production uses Alembic migrations
        with SessionLocal() as db:
            seed_reference_data(db)
            sync_model_versions(db)
            db.commit()
        log.info("TERRAVANT started (env=%s) models=%s", settings.ENV, registry.available())
        yield
    finally:
        close_rate_limiter()


app = FastAPI(
    title="TERRAVANT API", version="1.0.0", lifespan=lifespan,
    description="AI-powered agricultural intelligence and decision-support platform. Intelligence That Grows.",
    docs_url=None if settings.is_prod else "/docs", redoc_url=None,
)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)  # details stay in logs (NFR-08)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
def ready():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "database_unavailable"}, status_code=503)

    if settings.is_prod and not rate_limiter_ready():
        return JSONResponse({"status": "redis_unavailable"}, status_code=503)

    return {"status": "ready", "models": registry.available()}

