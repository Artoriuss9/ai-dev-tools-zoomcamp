# AI-assisted development workflow

## How AI assistance is used

AI coding assistance is used to explore requirements, propose focused changes,
implement small tasks, and identify relevant tests. The developer remains
responsible for product decisions, reviewing every diff, checking credentials
and data boundaries, and running verification commands.

Representative task prompts for this project include:

- “Compare this application with the final-project rubric and list missing
  deliverables without assuming Module 5 was completed.”
- “Add an isolated integration test for the player lookup → filtering →
  persistence → API response flow using a fake PUBG client.”
- “Generate and test an OpenAPI contract from the application's response
  models.”
- “Review the proposed Docker, CI, and observability changes for portability
  and secret leakage.”

These are representative prompts, not a claim that every earlier interaction
was recorded verbatim. No autonomous agent or external AI service receives
`.env`, API keys, or real player records.

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
