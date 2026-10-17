# Tool and data permissions

This document describes the permissions required by the application and its
development workflow.

| Component | Required access | Must not receive |
| --- | --- | --- |
| Browser | Same-origin `POST /analyze` with the player's entered nickname | PUBG API key or database credentials |
| FastAPI service | PUBG API outbound HTTPS; read configured environment; read/write database | Unrelated host files or source-control credentials |
| Blackbox Exporter | Probe the local app's `/health` and `/ready` endpoints | Host ports, app secrets, or Docker control |
| Alertmanager | Send authenticated firing/resolved health alerts to the internal on-call agent | Public ingress or Docker control |
| On-call agent | Read local app health/readiness; call the authenticated restart proxy for an approved incident | Docker socket, database credentials, Railway credentials, arbitrary container selection |
| Restart proxy | Read/write its incident ledger; mount the Docker socket to issue the single hardcoded restart request for `pubg-analytics-app` | Host-port exposure, database writes, or Railway access |
| CI tests | Repository read access; local isolated database; mocked PUBG client | Production PUBG API key or player data |
| CI image build | Repository read access and Docker build capability | Deployment credentials on pull requests |
| Deployment health workflow | Read the non-secret `RAILWAY_PUBLIC_URL` Actions variable and make public HTTP checks | Railway deployment token or PUBG API key |

Do not include `.env`, database files, real player match exports, authorization
headers, or API tokens in prompts, issues, pull requests, or CI artifacts.
Constrain third-party actions to read-only repository permissions unless a
specific deployment job requires more.

The two local responder tokens are Docker Compose file secrets under the
ignored `.secrets/` directory. Do not commit or upload them. The restart proxy
must not publish a host port. Its Docker socket mount grants powerful daemon
access if the proxy is compromised, even though the implemented API exposes
only a fixed app restart; use this arrangement only for the local demo, not as
a production Railway on-call integration.
