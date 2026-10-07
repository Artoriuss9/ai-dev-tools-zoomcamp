# Threat model

## Assets

- PUBG API key and upstream authorization header.
- Local database containing player identifiers and match statistics.
- Integrity and availability of the analysis API and its reports.

## Trust boundaries

- Browser input crosses into FastAPI at `/analyze`.
- FastAPI sends a bearer-authenticated request to the PUBG API.
- The service writes upstream-derived data to SQLite.
- CI builds and tests untrusted pull-request changes.

## Main risks and controls

| Risk | Controls | Residual limitation |
| --- | --- | --- |
| API key disclosure | `.env` ignored, `.dockerignore` excludes environment files, server-side token use, CI never needs the production key | Operators must not paste secrets into logs or reports |
| Nickname injection/XSS | Pydantic length/nonblank validation; frontend escapes values inserted into HTML and uses `textContent` for copy | Keep escaping coverage when adding new UI templates |
| Malformed/upstream error payloads | Explicit HTTP status translation, required participant-field checks, bounded HTTP timeout | PUBG API availability and rate limits remain external dependencies |
| Data loss or corruption | SQLAlchemy models, transactional upserts, persistent Docker volume, isolated tests | SQLite is intended for a single application instance |
| Dependency compromise | Pinned runtime dependencies and CI dependency audit | Review and update pins when a vulnerability is reported |
| Untrusted pull request access to secrets | Tests use fakes; CI does not require deployment secrets | Do not add production credentials to ordinary CI jobs |
| Observability data leakage | Logs omit API keys and request payloads; diagnostics omit environment values | Keep telemetry endpoints private to the local Compose network |

## Operational assumptions

The observability stack and default Grafana credentials are for local
development only. Do not expose them publicly unchanged. A production
deployment must use managed secrets, HTTPS, restricted network access, backup
and retention policies, and a database appropriate for its availability needs.
