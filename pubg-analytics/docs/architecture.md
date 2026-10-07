# Architecture

```text
Browser (static HTML/CSS/ES modules)
          | POST /analyze
          v
FastAPI app (backend/app/)
   |             |
   |             +--> PUBGClient --> PUBG API (server-side bearer token)
   |
   +--> SQLAlchemy repositories --> SQLite

FastAPI telemetry --> OTLP Collector --> Prometheus / Loki / Tempo --> Grafana
```

The browser assets live in `frontend/` and are served by FastAPI, so local and
container deployments use one origin and require no separate frontend server.
`frontend/api.js` centralizes
browser-to-backend communication. Pydantic response models define the
backend contract; `openapi.yaml` is generated from the same FastAPI schema and
checked in integration tests.

`backend/app/service.py` orchestrates the lookup, mode filtering, and persistence.
`backend/app/pubg_client.py` owns outbound API calls and error translation.
`backend/app/repository.py` performs SQLAlchemy upserts over models in `backend/app/models.py`.
`backend/app/analytics.py` derives deterministic summary and coaching statistics.
The database URL is set by `DATABASE_URL`; Compose uses a named volume for
SQLite persistence.

The Docker image contains only runtime packages and runs as a non-root user.
It reads Railway's assigned `PORT` and defaults to 8000 locally. GitHub Actions
runs backend and frontend tests, security checks, builds and smoke-tests the
image, and can deploy to Railway after a successful CI run when repository
deployment variables and the Railway project token are configured.
