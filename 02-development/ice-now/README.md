# IceNow

**Every game. Right now.**

IceNow is a responsive NHL scoreboard for coaches and players. The MVP focuses on quickly scanning games for yesterday, today, and tomorrow, with compact standings available alongside the scoreboard.

## MVP scope

- Live, upcoming, and completed games
- Scheduled, live, final, postponed, and canceled states
- Automatic refresh every 30-60 seconds
- Compact standings with points and goal differential
- Desktop grid and mobile list layouts
- Cached data, freshness timestamps, retry behavior, and WCAG 2.1 AA accessibility

The complete product specification is in [_docs/specs.md](_docs/specs.md).

## Start the frontend

Install Node.js, then run:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

## Start the backend

In a second terminal:

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The mock FastAPI service runs at `http://127.0.0.1:8000`. Run its tests with:

```powershell
uv run pytest
```

## Development status

The backend uses SQLAlchemy with SQLite seed data for development. The database URL is configurable, and the frontend talks to the same stable API contract regardless of the database engine.

## Brand direction

- Modern sports-data interface
- White, charcoal, and electric cyan
- Geometric sans-serif typography
- Minimal abstract speed/ice symbol
