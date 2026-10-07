# Project instructions

## Scope

- The backend is `backend/app/`; browser assets are in `frontend/`; product and operations
  documents live alongside the application.
- Preserve the stable `POST /analyze` response and error shape. Update
  `openapi.yaml` by running `python ops/export_openapi.py` whenever API schemas
  or routes change.
- `openapi.yaml` is the published contract generated from FastAPI. The browser
  HTTP client in `frontend/api.js` is the only module that makes API requests.

## Engineering rules

- Do not put PUBG API keys, tokens, personal credentials, or real player data
  in source, test fixtures, logs, or CI artifacts.
- Keep upstream calls behind `PUBGClient`; tests must use fakes or mocks and
  must not make real PUBG API calls.
- Use isolated SQLite databases in tests. Keep integration tests under
  `tests/integration/` and mark them `integration`.
- Add or update frontend tests for browser API-client and presentation changes.
- Keep HTTP failures explicit and consistent; do not turn upstream or database
  failures into success responses.
- Avoid logging submitted nicknames or upstream authorization headers.

## Verification

From this directory:

```powershell
pytest -q
node --test tests/frontend/*.test.js
python ops/export_openapi.py
python ops/diagnose.py
```

For the complete local container stack, see `README.md`.
