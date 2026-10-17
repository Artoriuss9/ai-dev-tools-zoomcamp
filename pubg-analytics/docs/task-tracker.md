# Public project task tracker

This repository-backed backlog is the public tracker for work on the project.
Each task has acceptance criteria and points to implementation or verification
evidence. Custom agents must read the matching task before acting and record
their role and evidence here when they finish.

| ID | Task | Status | Agent role | Acceptance criteria | Evidence |
| --- | --- | --- | --- | --- | --- |
| PUBG-001 | Define the repository agent team and handoffs | Done | Product planner | Project-scoped agent roles, boundaries, and a review/verification handoff are documented and discoverable from `AGENTS.md`. | [Custom agent roles](../../.github/agents/); [`AGENTS.md`](../AGENTS.md); [AI workflow](./ai-workflow.md) |
| PUBG-002 | Add actionable health alerts and bounded on-call response | Done | Operations responder | Alert rules, internal Alertmanager routing, and responder/proxy behavior are configured; only a liveness incident can restart the app once per fingerprint; a readiness-only/database failure escalates; repeated liveness failure escalates without another restart. Unit tests and live Compose flow cover the behavior. | [`docker-compose.yml`](../docker-compose.yml); [`alert-rules.yml`](../config/prometheus/alert-rules.yml); [`alertmanager.yml`](../config/alertmanager/alertmanager.yml); [`test_on_call.py`](../tests/test_on_call.py) |
| PUBG-003 | Verify project behavior and operations documentation | Done | QA reviewer | Relevant backend and frontend tests pass; alert configuration and Compose setup are validated; operational and security docs describe limitations accurately. Prometheus/Alertmanager validation is added to CI and must pass there. | 53 backend tests, 6 frontend tests, Compose config, and Bandit scan; [CI workflow](../../.github/workflows/pubg-analytics.yml); [permissions](./permissions.md); [threat model](../security/threat-model.md) |
| PUBG-004 | Confirm trace and log correlation | Done | QA reviewer | A request trace ID is present in application logs and documented with a reproducible local verification path. | [`telemetry.py`](../backend/app/telemetry.py); [`test_api.py`](../tests/test_api.py); [README verification](../README.md) |
| PUBG-005 | Document the deployment workflow boundary | Done | Product planner | The repository explains CI gating and deployment behavior without claiming an active deployment while Railway is intentionally paused. | [Railway deployment guide](./railway-deploy.md); [AI workflow](./ai-workflow.md) |

## Activity log

- The project coordinator created this backlog before implementation and used
  PUBG-001 through PUBG-005 to scope the work. Repository custom agents are
  being added so future tasks can be picked up with the same task IDs and
  verifiable acceptance criteria.
- The implementer used PUBG-001 to define the team documentation, PUBG-002 to
  scope the local alert/responder and safety tests, and PUBG-004 to add trace
  correlation. QA verification recorded the executed test and configuration
  checks under PUBG-003 and PUBG-004.
- PUBG-002 remains in progress because the Compose stack was not started for a
  live alert demonstration; doing so would require operating the local Docker
  socket/restart path. Its configuration and bounded response tests pass, but
  the live stack path should be exercised by an operator before marking it
  done.
- The current pass was completed by the project coordinator without invoking
  separate subagents. The repository agent profiles define the roles for
  subsequent VS Code agent sessions; this activity log does not claim
  multi-agent delegation that did not occur.
- The local Docker daemon was unavailable in the session that wrote the
  previous entry; the Compose stack and the promtool/amtool configuration
  checks were later run successfully with Docker Desktop available.
- The Railway deployment initially crashed because the application service's
  `DATABASE_URL` still referenced a removed Postgres service. The operator
  re-pointed `DATABASE_URL` at the new Postgres service; after the redeploy,
  `/health` and `/ready` returned HTTP 200 and `/version` reported commit
  `c0591d587080715f83a538c822eca3f3f231cfce` at the public URL.
- A later session completed the live verification that PUBG-002 and PUBG-003
  required. The full Compose stack was started (`docker compose up --build -d
  --wait`) with all containers healthy. `promtool check config --syntax-only`,
  `promtool check rules`, and `amtool check-config` validated the Prometheus,
  alert-rule, and Alertmanager configuration files. A live incident was
  exercised by stopping the `app` container: the on-call agent correctly
  escalated (`readiness_failed_requires_operator`) because readiness also
  failed, so no restart was attempted. The bounded liveness restart path was
  then exercised directly against the restart proxy: the first request for an
  incident fingerprint returned 200 `restart_requested` and the app came back
  healthy, and a second request with the same fingerprint returned 409 "Restart
  already attempted for this incident", confirming the once-per-fingerprint
  limit. The local backend (54 tests), frontend (6 tests), OpenAPI export, and
  diagnose checks also pass. PUBG-002 and PUBG-003 are marked done.

## Status definitions

- **Open**: not started.
- **In progress**: an agent is actively implementing or verifying the task.
- **Done**: acceptance criteria are met and evidence is linked.
- **Blocked**: progress requires an external decision or unavailable access;
  explain the blocker in the task evidence.
