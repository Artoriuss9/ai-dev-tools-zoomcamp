# Product specification: PUBG Match Analytics

## Problem

PUBG players need season-wide performance totals and a quick way to understand
recent match performance and identify what to focus on in the next match.

## Target user and goal

- **User:** a PUBG player who can be looked up by in-game nickname.
- **Goal:** review current-season totals and up to ten recent detailed matches
  in Solo, Duo, or Squad FPP/TPP, then get concise, explainable insights.

## User flow

1. The player enters a nickname in the browser.
2. The application looks up the player, current season totals, and recent
   mode-specific match references via the PUBG API.
3. The backend fetches up to ten individual match details and stores the
   player, matches, and participant statistics in SQLite.
4. The page displays full-season aggregate metrics separately from recent
   match metrics, map performance, trends, and coaching insights.
5. The player may refresh to fetch current data again.

## Functional requirements

- Keep the PUBG API key on the server; never send it to the browser.
- Let the user select Solo, Duo, or Squad in FPP or TPP.
- Show full-season aggregates from the PUBG season-stats endpoint and analyze
  no more than ten recent individual matches for detailed insights.
- Clearly distinguish full-season totals from individual match data, which the
  PUBG API retains for only 14 days.
- Calculate recent-match K/D as total kills divided by confirmed deaths from
  participant `deathType`; do not infer deaths from matches lost.
- Compare recent kills-per-match and damage-per-match against the season
  averages as context, not as an independent trend.
- De-duplicate match references and persist updates to existing records.
- Compute statistics from the analyzed matches and make the JSON response
  usable by the browser without client-side database access.
- Return a consistent `{ "error": { "code": "...", "message": "..." } }` error
  shape for validation and upstream API errors.
- Expose liveness and database readiness endpoints.

## Non-functional requirements

- A local developer can run tests without a PUBG API key or network access.
- SQLite is persistent in Docker Compose and configurable using `DATABASE_URL`.
- Configuration and credentials are kept outside the container image.
- HTTP requests are logged without logging API keys or request payloads.

## Out of scope

- PUBG account authentication or writes to player accounts.
- Competitive rankings across players.
- LLM-generated advice; current insights are deterministic calculations.
- Module 5 agent extensions (not completed for this project).
