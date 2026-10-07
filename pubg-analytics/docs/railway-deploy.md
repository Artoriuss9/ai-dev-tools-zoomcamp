# Railway deployment

This app is prepared for Railway with Railway PostgreSQL. The GitHub Actions
deployment job runs only after tests, audits, container build, and smoke checks
pass, and only for pushes to `main`. Pull requests never receive deployment
credentials.

## Provision the services once

1. Create a Railway project and add a PostgreSQL service.
2. Create an application service in the same project. Configure its source
   repository as this repository and set its **Root Directory** to
   `/pubg-analytics`. Railway builds the checked-in `Dockerfile`. Disable
   Railway's automatic deploy-on-push setting so deployment happens only after
   the GitHub Actions checks succeed.
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
5. Set the GitHub repository **Actions variables**:
   - `RAILWAY_PROJECT_ID`: the Railway project ID.
   - `RAILWAY_ENVIRONMENT_ID`: the production environment ID.
   - `RAILWAY_SERVICE_ID`: the application service ID (not the PostgreSQL
     service ID).
   - `RAILWAY_PUBLIC_URL`: the generated application URL, including `https://`.
6. Set the GitHub repository **Actions secret** `RAILWAY_TOKEN` to a Railway
   project token. Do not put tokens or the PUBG API key in the repository.

The service listens on Railway's injected `PORT`; for local development the
default remains port 8000. Railway's `/ready` health probe checks database
connectivity before traffic is considered healthy.

## Deploy and verify

Push a change to `main` after configuring the Railway variables and secret.
GitHub Actions deploys the Dockerfile using `railway up --ci`, then checks
`/health` and `/ready` at `RAILWAY_PUBLIC_URL`. The workflow summary records
the deploy result and public URL; the app's root page is also available at that
URL.

If the Railway variables are not configured, the deployment job is skipped.
This lets forks and contributors run the full test/security CI without access
to production credentials.

Railway CLI documentation: <https://docs.railway.com/cli>,
<https://docs.railway.com/cli/up>, and
<https://docs.railway.com/databases/postgresql>.
