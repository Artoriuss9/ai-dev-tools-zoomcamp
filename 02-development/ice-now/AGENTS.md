# AGENTS.md

## Product context

IceNow is a responsive public NHL scoreboard. Read [_docs/specs.md](_docs/specs.md) before changing product behavior.

## Engineering principles

- Keep games as the primary workflow.
- Keep the data provider behind a replaceable interface.
- Treat freshness and failure states as first-class UI states.
- Preserve responsive behavior across desktop and mobile.
- Target WCAG 2.1 AA.
- Do not add NHL branding or data-provider assets without confirming display rights.
- Keep the MVP focused; defer accounts, notifications, play-by-play, player statistics, historical seasons, and playoff analysis unless the specification is updated.

## Validation

Before submitting changes:

- Run the narrowest relevant tests or checks.
- Verify loading, cached-data, error, empty, scheduled, live, final, postponed, and canceled states.
- Check keyboard navigation and responsive layouts.
- Update [_docs/specs.md](_docs/specs.md) when a product decision changes.
