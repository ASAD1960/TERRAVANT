FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt backend/requirements-dl.txt ./
ARG WITH_DL=false
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$WITH_DL" = "true" ]; then pip install --no-cache-dir -r requirements-dl.txt --extra-index-url https://download.pytorch.org/whl/cpu; fi
COPY backend/ /srv/backend/
COPY ml/ /srv/ml/
WORKDIR /srv/backend
ENV ML_ARTIFACT_DIR=/srv/ml/artifacts UPLOAD_DIR=/srv/storage/uploads
RUN useradd -m app && mkdir -p /srv/storage/uploads && chown -R app /srv/storage
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fs http://localhost:8000/health || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers"]
