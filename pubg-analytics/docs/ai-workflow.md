# AI-assisted development workflow

## How AI assistance is used

AI coding assistance is used to explore requirements, propose focused changes,
implement small tasks, and identify relevant tests. The developer remains
responsible for product decisions, reviewing every diff, checking credentials
and data boundaries, and running verification commands.

## Context and agent-team workflow

The project context is supplied from checked-in sources rather than copied from
secrets or production data: the current rubric, `product-spec.md`,
`docs/task-tracker.md`, `AGENTS.md`, relevant implementation and tests, and the
architecture/security documents named by the task. The task tracker is the
public source of task IDs, scope, acceptance criteria, status, and evidence.

Workspace agents in `.github/agents/` have bounded responsibilities:

1. **Product Planner** maps a rubric or product requirement to a tracker task
   and acceptance criteria; it does not implement code.
2. **Implementer** handles a single application change, adds tests, and reports
   its evidence.
3. **Operations Responder** owns monitoring and runbook changes, subject to the
   strict app-only, one-restart limit and escalation rules.
4. **QA Reviewer** independently runs targeted checks and reports gaps; it is
   read-only.

For multi-role work, the planner scopes a tracker task, the appropriate
implementer or operations responder makes the change, and QA reviews the
acceptance criteria independently. The developer reviews the diff and
verification output before marking the tracker item done. If a check or
deployment needs user approval, it remains blocked rather than being inferred
from an agent's report. This describes the repository's repeatable workflow;
it is not a claim that historical tasks were delegated to multiple agents.

For the current rubric pass, the project coordinator created the public tracker
before implementation and used PUBG-001 through PUBG-005 to bound the work.
The GitHub issue-creation surface was not authenticated, so these tasks are
tracked in the versioned public repository rather than claiming nonexistent
GitHub Issues.

Representative task prompts for this project include:

- “Compare this application with the final-project rubric and list any
  missing deliverables.”
- “Add an isolated integration test for the player lookup → filtering →
  persistence → API response flow using a fake PUBG client.”
- “Generate and test an OpenAPI contract from the application's response
  models.”
- “Review the proposed Docker, CI, and observability changes for portability
  and secret leakage.”

These are representative prompts, not a claim that every earlier interaction
was recorded verbatim. No external AI service receives `.env`, API keys, or
real player records.

## Review and verification loop

1. Read the existing implementation and relevant project requirements before
   editing.
2. Keep changes scoped to an explicit rubric item and use existing patterns.
3. Review generated code and configuration manually; do not merge AI output
   without inspection.
4. Run backend unit/integration tests and frontend tests.
5. Regenerate the OpenAPI contract and test for drift.
6. Run deterministic security scanners and build/smoke-test the container.
7. Review CI artifacts and operational diagnostics. Investigate findings rather
   than silently suppressing them.

The GitHub Actions workflow records test and scanner output in the job summary
and uploads machine-readable reports for each run.
