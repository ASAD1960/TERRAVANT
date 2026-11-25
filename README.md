# TERRAVANT — Intelligence That Grows.

AI-powered agricultural intelligence and decision-support platform (initial target: Punjab, Pakistan).
React + TypeScript frontend · FastAPI backend · PostgreSQL · scikit-learn / PyTorch ML modules · Docker.

## Honest status

| Area | State |
|---|---|
| Auth (Argon2id, JWT access/refresh, reset), RBAC, ownership checks, audit log | Implemented, tested |
| Farms, fields, soil records, activities, notifications, CSV report | Implemented, tested |
| Crop recommendation, yield prediction | Implemented end-to-end, **trained on synthetic demo data** |
| Fertilizer guidance | Rule-based, qualitative only (no dosages). **Thresholds are placeholders to validate with Punjab agronomists** |
| Disease detection | API, validation, uncertainty handling and training script implemented. **No model is shipped**: needs PyTorch + a real dataset. Until trained the API returns 503 rather than inventing output |
| Weather | Open-Meteo integration with cache, retry, stale fallback |
| Frontend | All main pages, responsive, typed, tested |
| Not built | Urdu UI, business team/customer records, advisor workflows, Redis/Celery, MLflow/DVC wiring, email delivery for password reset, user-study tooling |

**Models trained on synthetic data say nothing about real-world accuracy.** The UI and API label this
(`data_source: synthetic-demo`). Retrain with real data (`--csv`) and perform regional validation before real use.

## Quick start (local)

```bash
make setup                      # backend + frontend deps
make train                      # trains demo crop + yield models into ml/artifacts
cd backend && uvicorn app.main:app --reload     # http://localhost:8000/docs
cd frontend && npm run dev                      # http://localhost:5173
python scripts/seed_demo.py     # optional: demo@terravant.local / Demo-passw0rd!
ADMIN_PASSWORD='...' python scripts/create_admin.py you@example.com "Your Name"
```

## Docker

```bash
cp .env.example .env     # set SECRET_KEY (python -c "import secrets;print(secrets.token_urlsafe(64))")
docker compose up --build   # web http://localhost:8080 · api http://localhost:8000
```
Set `WITH_DL: "true"` in `docker-compose.yml` to include PyTorch for disease detection.
Production (`ENV=production`) refuses the default secret, disables `/docs`, and uses Alembic migrations.

## Tests

`make test` — 29 backend tests (auth, ownership isolation, validation, ML, uploads, RBAC, audit, weather failure) and 13 frontend tests.

## Layout

```
backend/   FastAPI app (api/, core/, models/, schemas/, services/, integrations/, ml/ inference), alembic/, tests/
frontend/  React app (pages/, layouts/, hooks/, services/, utils/, routes/)
ml/        training pipelines per module + artifacts/
infrastructure/  docker, deployment, monitoring (placeholders for your environment)
docs/      architecture, requirements traceability, deployment, ML validation checklist
scripts/   create_admin.py, seed_demo.py
```

## Requirements traceability and docs
See `docs/`: `architecture.md`, `traceability.md`, `deployment.md`, `ml-validation.md`.
