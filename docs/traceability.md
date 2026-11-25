# Requirement traceability (SRS → implementation)

| Req | Where |
|---|---|
| FR-01–05 | `api/v1/auth.py`, `schemas/user.py` |
| FR-06/07 | `users.organization`, register `account_type` (profile fields minimal) |
| FR-08–10 | `api/v1/farms.py` |
| FR-11/12 | `POST /predictions/crop` (+ explanation) |
| FR-13–15 | `POST /predictions/disease`, `ml/disease.py` (uncertainty) |
| FR-16 | `POST /predictions/yield` |
| FR-17 | `POST /recommendations/fertilizer`, `ml/fertilizer.py` |
| FR-18 | `api/v1/weather.py`, `integrations/weather.py` |
| FR-19/20 | `api/v1/analytics.py`, `pages/farmer/Dashboard.tsx` |
| FR-21 | notifications endpoints (generated on crop prediction; extend for other events) |
| FR-22 | `GET /analytics/reports` (CSV farm inventory; extend for other reports) |
| FR-23 | `/fields/{id}/activities` |
| FR-24/25 | `api/v1/admin.py` |
| FR-26 | prediction history endpoints |
| FR-27 | `services/audit.py` |
| FR-28 | Pydantic bounds + upload validation |
| FR-29/30 | weather integration; `/health`, `/ready`, request logging |
| BR-05/06/09 | model_version on every prediction; limitations in responses |
| BR-07 | weather degradation tests |
| BR-08 | admin actions audited (tested) |
| Partial / not done | FR-07 full business workflows, advisor role features, NFR-12 formal accessibility audit, NFR-14 backups (infra), NFR-15 Urdu |
