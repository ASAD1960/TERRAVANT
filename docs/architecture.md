# Architecture

Modular monolith (SDD 5.2). Request path: React → `/api/v1` (FastAPI routers, Pydantic validation) →
dependency layer (JWT auth, role checks, ownership checks) → services / ML inference → SQLAlchemy → PostgreSQL.

- **Auth**: Argon2id hashes; short-lived access token (30 min, held in memory by the SPA), refresh token (7 d, sessionStorage).
  Reset tokens are bound to the current password hash (single use). Login errors are identical for unknown user / bad password / suspended.
  Hardening to consider: httpOnly cookie refresh, Redis token denylist for hard logout.
- **Authorization**: roles `farmer, business, advisor, admin, operator`; non-owners get 404 (not 403) to avoid leaking existence.
- **ML**: artifacts in `ml/artifacts/<module>/` (`model.joblib` + `metadata.json`). On startup each is registered in `model_versions`;
  every prediction stores its `model_version_id` (BR-05). Responses carry confidence, limitations and data source (BR-06, BR-09).
- **Disease uploads**: validated by decoding actual bytes (JPEG/PNG/WebP, ≥64 px, ≤8 MB), re-encoded, stored under random names outside static paths.
  Low-confidence results return `uncertain` instead of a diagnosis.
- **Resilience**: weather failures degrade to cached data or a 503 for that endpoint only (BR-07). Unhandled errors return a generic 500; detail stays in logs.
- **Single-process caveats**: rate limiter and weather cache are in-memory; use Redis when running multiple replicas.
