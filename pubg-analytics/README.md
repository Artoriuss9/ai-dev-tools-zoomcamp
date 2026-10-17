# PUBG Match Analytics

This FastAPI application displays current-season aggregate statistics and detailed
analytics for recent Solo/Duo/Squad FPP and TPP matches using the PUBG API. PUBG only
retains individual match details for the last 14 days, so full-season totals are
shown separately from the analysis of up to 10 recent matches.

**Public demo URL (currently paused):**
<https://ai-dev-tools-zoomcamp-production-0bee.up.railway.app/>
See [Railway deployment](docs/railway-deploy.md) before resuming it.

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

Set a valid `PUBG_API_KEY`. The local alert responder uses two Docker Compose
secret files. Create them once without putting their contents in source control.

**Security note:** the local restart proxy mounts the Docker socket, which grants
powerful daemon access if that proxy is compromised. This is a local
demonstration only, not a production setup.

```powershell
New-Item -ItemType Directory -Force .secrets | Out-Null
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$webhookBytes = New-Object byte[] 32
$restartBytes = New-Object byte[] 32
$rng.GetBytes($webhookBytes)
$rng.GetBytes($restartBytes)
$webhookToken = [Convert]::ToBase64String($webhookBytes)
$restartToken = [Convert]::ToBase64String($restartBytes)
[IO.File]::WriteAllText((Join-Path $PWD ".secrets\alertmanager-webhook-token"), $webhookToken)
[IO.File]::WriteAllText((Join-Path $PWD ".secrets\restart-proxy-token"), $restartToken)
$rng.Dispose()
[Array]::Clear($webhookBytes, 0, $webhookBytes.Length)
[Array]::Clear($restartBytes, 0, $restartBytes.Length)
Remove-Variable webhookToken, restartToken, webhookBytes, restartBytes, rng
```

Do not share or commit these files. Then start the application, alert pipeline,
and observability stack:

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
written as JSON to stdout and include the active OpenTelemetry `trace_id` and
`span_id` when a request span exists:

```powershell
docker compose logs -f app
```

### Local alert and on-call demonstration

Prometheus uses Blackbox Exporter to probe `/health` and `/ready`. An endpoint
that remains unavailable for one minute fires an alert through Alertmanager to
the on-call agent. The agent checks liveness and readiness before acting:

- A liveness alert requests a restart only when readiness is healthy: at most
  one restart of the fixed `pubg-analytics-app` container for that alert
  fingerprint, followed by a recovery check.
- A failing readiness probe blocks all restarts and escalates to the operator,
  including database-connectivity failures, unless a separate liveness alert
  also reports that the app process is unavailable; that liveness incident may
  request its one app restart because readiness cannot be determined while
  the process is down.
- If the application is still unhealthy after its one restart, it escalates
  without retrying. The attempt is stored in the `on-call-state` volume until
  Alertmanager sends a resolved notification.

Escalations are recorded in the on-call-agent logs, and the alert remains
visible in Prometheus/Alertmanager. No external paging channel is configured.
Inspect the agent and alert pipeline with:

```powershell
docker compose logs -f on-call-agent restart-proxy alertmanager
```

To exercise the liveness alert locally, stop only the Compose app container and
wait for the one-minute alert rule plus notification delay:

```powershell
docker compose stop app
docker compose logs -f on-call-agent restart-proxy alertmanager
```

The liveness alert should request one restart; a second attempt for the same
incident must be rejected. Do not use this procedure against Railway or any
other production service.

The restart proxy alone has access to the Docker socket. It exposes only
authenticated app-restart and incident-clear operations and hardcodes the
application container name; the on-call agent has no Docker socket access.
Docker daemon access is still highly privileged if the proxy itself is
compromised. This is a local demonstration boundary, not a production Railway
control plane. Never expose the proxy, agent, or Alertmanager ports publicly.

SQLite is stored in a named Docker volume and persists when containers are
recreated. Stop the stack while preserving data:

```powershell
docker compose down
```

To use PostgreSQL with Docker Compose, set `PUBG_DATABASE_URL` to a connection
string such as
`postgresql+psycopg://<user>:<password>@<host>:5432/<database>`. The PostgreSQL
driver is included in the runtime dependencies; Docker Compose uses the
`/data/pubg.db` SQLite volume by default. `DATABASE_URL` from `.env` remains
available for running locally without Docker.

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
GitHub Actions installs development dependencies, runs the tests and security
scans, validates Compose and observability configuration, and builds the Docker
image on pushes and pull requests. The application image installs only runtime
dependencies from `requirements.txt`.

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
[public task tracker](docs/task-tracker.md) records rubric work and evidence;
repository [custom agents](../.github/agents/) define the team roles; the
[AI workflow](docs/ai-workflow.md) describes context, handoffs, manual review,
and verification practices.

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
