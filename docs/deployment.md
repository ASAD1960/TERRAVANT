# Deployment checklist
1. Set a strong `SECRET_KEY`, `ENV=production`, real `DATABASE_URL`, restrictive `CORS_ORIGINS`.
2. Put HTTPS in front (Caddy/nginx/cloud LB); the bundled nginx serves the SPA and proxies `/api`.
3. `alembic upgrade head` runs automatically in the backend container.
4. Mount persistent volumes for Postgres and uploads; schedule encrypted Postgres backups and test a restore.
5. Train/deploy real models; set their `data_source`; review `Admin → Models`.
6. Wire an email provider for password reset (currently logged only; token is returned only in development/test).
7. Add monitoring (Prometheus/Sentry) in `infrastructure/monitoring`; run `pip-audit` and `npm audit --omit=dev` in CI (already configured).
8. Load-test (Locust/k6) and run a security review before exposing to real users.
