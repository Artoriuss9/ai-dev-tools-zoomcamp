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
Prometheus --> Blackbox Exporter --> /health and /ready
Prometheus --> Alertmanager --> On-call Agent --> Restart Proxy --> app container
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

The Docker image contains runtime packages and runs the application as a
non-root user. It reads Railway's assigned `PORT` and defaults to 8000 locally.
In local Compose, Prometheus probes liveness and readiness, Alertmanager sends
firing/resolved alerts to the on-call agent, and a separate restart proxy
provides only the fixed app-restart operation. The proxy's one-attempt-per-alert
ledger is stored in a dedicated volume. The proxy alone mounts the Docker
socket; compromise of that privileged component remains a local-development
risk.

Application JSON logs include the active OpenTelemetry trace and span IDs.
GitHub Actions runs backend and frontend tests, security checks, builds and
smoke-tests the image. Railway waits for CI before deploying from the connected
branch when deployment is enabled. A separate scheduled/manual GitHub Actions
workflow checks public liveness, readiness, UI, and deployed commit version
without requiring a Railway token. The local alert responder is not connected
to Railway and cannot start, stop, or deploy the hosted service.
