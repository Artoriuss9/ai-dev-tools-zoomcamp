# Railway deployment

This app is prepared for Railway with Railway PostgreSQL. Railway deploys from
the connected `main` branch after GitHub Actions checks pass. A separate
health workflow checks `/health`, `/ready`, `/`, and the deployed commit SHA
at `/version` every 15 minutes or when manually triggered. No Railway API
token is required in GitHub Actions.

## Provision the services once

1. Create a Railway project and add a PostgreSQL service.
2. Create an application service in the same project. Configure its source
   repository as this repository and set its **Root Directory** to
   `/pubg-analytics`. Railway builds the checked-in `Dockerfile`. Keep
   deployment on pushes to `main` enabled, and enable **Wait for CI** so
   Railway waits for GitHub Actions to finish successfully before deployment.
3. Add the following application service variables in Railway:
   - `PUBG_API_KEY`: your PUBG developer API key.
   - `DATABASE_URL`: reference the PostgreSQL service's `DATABASE_URL` using
     Railway's variable-reference picker (normally `${{Postgres.DATABASE_URL}}`;
     use the actual database service name). The backend normalizes Railway's
     `postgresql://` URL to the installed Psycopg 3 SQLAlchemy driver.
   - `PUBG_PLATFORM`: `steam` (or the platform for your account).
   - `PUBG_MODE`: `solo-fpp` (or the mode you want to analyze).
   - `PUBG_API_TIMEOUT`: `10`.
4. In the application service networking settings, generate a public domain.
   Do not expose the PostgreSQL service publicly.
5. Set the GitHub repository **Actions variable** `RAILWAY_PUBLIC_URL` to the
   generated application URL, including `https://`.

The service listens on Railway's injected `PORT`; for local development the
default remains port 8000. Railway's `/ready` health probe checks database
connectivity before traffic is considered healthy.

## Deploy and verify

Push a change to `main`. GitHub Actions tests, audits, builds, and smoke-tests
the image. Railway waits for CI and then deploys the connected branch. The
deployment-health workflow can be run manually after Railway marks the
deployment **Active**, and then continues checking every 15 minutes. It reports
the deployed Railway commit SHA from `/version`.

The deployment-health workflow can also be triggered manually with
`workflow_dispatch`. It requires only `RAILWAY_PUBLIC_URL`, not Railway API
credentials. The health check is deliberately not triggered by `workflow_run`:
with Railway's **Wait for CI** enabled, a post-CI workflow that itself waits
for the new deployment could create a deployment/CI wait cycle. Keep the PUBG
API key in Railway variables, not GitHub Actions.

Railway documentation: <https://docs.railway.com/cli>,
<https://docs.railway.com/databases/postgresql>, and
<https://docs.railway.com/guides/ci-cd>.
