# Architecture

```text
Browser (static HTML/CSS/ES modules)
          | POST /analyze (nickname + selected mode)
          v
FastAPI app (backend/app/)
   |             |
   |             +--> PUBGClient --> PUBG API (season totals + recent matches)
   |
   +--> SQLAlchemy repositories --> SQLite locally / PostgreSQL on Railway

FastAPI telemetry --> OTLP Collector --> Prometheus / Loki / Tempo --> Grafana
```

The browser assets live in `frontend/` and are served by FastAPI, so local and
container deployments use one origin and require no separate frontend server.
`frontend/api.js` centralizes
browser-to-backend communication. Pydantic response models define the
backend contract; `openapi.yaml` is generated from the same FastAPI schema and
checked in integration tests.

`backend/app/service.py` orchestrates the lookup, selected-mode season summary,
recent match analysis, and persistence. PUBG exposes season aggregates for the
full active season but retains detailed individual matches for 14 days.
`backend/app/pubg_client.py` owns outbound API calls and error translation.
`backend/app/repository.py` performs SQLAlchemy upserts over models in `backend/app/models.py`.
`backend/app/analytics.py` derives deterministic match summaries, including
K/D from confirmed participant deaths rather than match losses. Season
aggregates provide context for recent kills-per-match and damage; because the
recent matches are part of the season totals, this comparison is not treated
as an independent trend.
The database URL is set by `DATABASE_URL`; Compose uses a named volume for
SQLite persistence, while Railway uses its PostgreSQL service.

The Docker image contains only runtime packages and runs as a non-root user.
It reads Railway's assigned `PORT` and defaults to 8000 locally. GitHub Actions
runs backend and frontend tests, security checks, builds and smoke-tests the
image. Railway waits for CI before deploying from the connected branch. A
separate scheduled/manual GitHub Actions workflow checks public liveness,
readiness, UI, and deployed commit version without requiring a Railway token.
