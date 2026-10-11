# PUBG Match Analytics

This FastAPI application displays current-season aggregate statistics and detailed
analytics for recent Solo/Duo/Squad FPP and TPP matches using the PUBG API. PUBG only
retains individual match details for the last 14 days, so full-season totals are
shown separately from the analysis of up to 10 recent matches.
Recent matches are stored in a database (SQLite locally, PostgreSQL on Railway).
The API key is stored only in the local `.env` file and is not included in the
Docker image.

K/D in recent match analysis is calculated as total kills divided by confirmed
deaths using PUBG's `deathType` field. Wins with `deathType=alive` do not count
as deaths. K/D is hidden for older records that do not contain this field.
PUBG's aggregate season summary does not include a death count, so seasonal K/D
is not calculated.

## Run locally with Docker Compose

Docker Desktop and Docker Compose are required. In PowerShell, from the project
directory:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set a valid `PUBG_API_KEY`, then start the application and observability stack:

```powershell
docker compose up --build -d --wait
```

- Application: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/health>
- Readiness (including the SQLite check): <http://127.0.0.1:8000/ready>
- Grafana: <http://127.0.0.1:3000/> (`admin` / `admin`, for local development only)
- Prometheus: <http://127.0.0.1:9090/>

Grafana automatically configures Prometheus, Loki, and Tempo data sources.
Metrics, logs, and traces are available in Explore. Application HTTP logs are
written as JSON to stdout:

```powershell
docker compose logs -f app
```

SQLite is stored in a named Docker volume and persists when containers are
recreated. Stop the stack while preserving data:

```powershell
docker compose down
```

To use PostgreSQL, set `DATABASE_URL` to a connection string such as
`postgresql+psycopg://<user>:<password>@<host>:5432/<database>`. The PostgreSQL
driver is included in the runtime dependencies; Docker Compose uses SQLite by
default for local development.

## Run locally without Docker

Python 3.11 or later is required:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Set PUBG_API_KEY in .env
uvicorn backend.app.main:app --reload
```

When running locally without an OTLP endpoint, the application writes JSON logs
to the console. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to send telemetry; by default,
Compose routes it to the local OpenTelemetry Collector.

## Tests and CI

From the `pubg-analytics` directory:

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

Tests do not call the live PUBG API and use an isolated SQLite database.
GitHub Actions installs development dependencies, runs the tests, and builds
the Docker image on pushes and pull requests. The application image installs
only runtime dependencies from `requirements.txt`.

## API

`POST /analyze` accepts `{"nickname":"PlayerName","mode":"duo-fpp"}`.
The API accepts `solo`, `solo-fpp`, `duo`, `duo-fpp`, `squad`, and `squad-fpp`;
the interface offers Solo/Duo/Squad in both FPP and TPP. If no mode is specified,
`PUBG_MODE` is used. A successful response includes statistics for the full active season,
up to 10 of the most recent available detailed matches, and insights for that
recent sample. The PUBG API does not provide detailed match history older than
14 days. Errors use the format
`{ "error": { "code": "...", "message": "..." } }`.

`GET /health` checks process liveness. `GET /ready` queries the database and
returns HTTP 503 if it is unavailable. `GET /version` returns the commit SHA
used by Railway for the current deployment.

The OpenAPI contract is stored in [`openapi.yaml`](openapi.yaml) and generated
from the FastAPI schemas:

```powershell
python ops/export_openapi.py
```

## Architecture, tests, and AI workflow

The backend is in `backend/app/`, the browser frontend is in `frontend/`, and
product requirements are in [`product-spec.md`](product-spec.md).
[Architecture documentation](docs/architecture.md) describes interactions
between the UI, API, PUBG API, database, and observability stack.
[`AGENTS.md`](AGENTS.md) contains project instructions; the
[AI workflow](docs/ai-workflow.md) describes AI usage, manual review, and
verification practices.

Backend tests include unit and API tests, plus an integration scenario in
`tests/integration/` that exercises the HTTP API, service layer, and isolated
SQLite database. Frontend tests use the built-in Node test runner and require no
npm packages:

```powershell
pytest -q tests
node --test tests/frontend/*.test.js
```

## Security and operations

See the [threat model](security/threat-model.md),
[AI tools and data policy](security/tool-data-policy.md),
[security scan policy](security/scan-policy.md), and
[tool and data permissions](docs/permissions.md).
GitHub Actions publishes Bandit and `pip-audit` reports and saves Compose stack
diagnostics as a workflow artifact.

After starting the Compose stack, check the services and save a JSON report:

```powershell
python ops/diagnose.py --output ops/diagnostic-report.json
```

Instructions for configuring the production service on Railway and GitHub
Actions are in [`docs/railway-deploy.md`](docs/railway-deploy.md). The workflow
deploys only after successful CI checks, on pushes to `main`, and when the
required Railway variables and secrets are configured.
