# IceNow backend

FastAPI service backed by SQLAlchemy and SQLite by default. The seed data is intentionally local and replaceable; set `DATABASE_URL` to another SQLAlchemy-supported database when moving beyond the prototype.

## Start

From this directory:

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

The default database is `ice_now.db`. To use another SQLAlchemy database:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost/ice_now"
uv run uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /api/scoreboard/yesterday`
- `GET /api/scoreboard/today`
- `GET /api/scoreboard/tomorrow`

## Tests

```powershell
uv run pytest
```
