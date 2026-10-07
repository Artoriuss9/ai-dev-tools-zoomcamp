# Tool and data permissions

This project has not completed the course's Module 5 agent-extension work.
There are no project-defined MCP servers, agent hooks, plugins, or delegated
agents. This document describes the permissions the normal application and
development workflow require; it is not an agent extension pack.

| Component | Required access | Must not receive |
| --- | --- | --- |
| Browser | Same-origin `POST /analyze` with the player's entered nickname | PUBG API key or database credentials |
| FastAPI service | PUBG API outbound HTTPS; read configured environment; read/write database | Unrelated host files or source-control credentials |
| CI tests | Repository read access; local isolated database; mocked PUBG client | Production PUBG API key or player data |
| CI image build | Repository read access and Docker build capability | Deployment credentials on pull requests |
| Deployment health workflow | Read the non-secret `RAILWAY_PUBLIC_URL` Actions variable and make public HTTP checks | Railway deployment token or PUBG API key |

Do not include `.env`, database files, real player match exports, authorization
headers, or API tokens in prompts, issues, pull requests, or CI artifacts.
Constrain third-party actions to read-only repository permissions unless a
specific deployment job requires more.
