# Product specification: PUBG Match Analytics

## Problem

PUBG players have match history but need a quick way to understand recent
performance and identify what to focus on in the next match.

## Target user and goal

- **User:** a PUBG player who can be looked up by in-game nickname.
- **Goal:** review up to ten recent matches in the configured game mode and get
  concise, explainable performance trends.

## User flow

1. The player enters a nickname in the browser.
2. The application looks up the player and their recent match references via
   the PUBG API.
3. The backend fetches match details, filters the configured mode, and stores
   the player, matches, and participant statistics in SQLite.
4. The page displays summary metrics, map performance, recent-vs-previous
   trends, coaching insights, and the selected matches.
5. The player may refresh to fetch current data again.

## Functional requirements

- Keep the PUBG API key on the server; never send it to the browser.
- Analyze no more than ten matches in the configured mode (Solo FPP by default).
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
