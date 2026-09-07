# Shared Chores Tool – Specification

## Core Features (settled)
1. **Fixed weekly schedule** – All chores reset to "not done" every Friday.
2. **Simple done/not done toggle** – No extra fields (effort, time, location).
3. **Markdown file storage** – Chore list and statuses are read from and written to a `.md` file.

## User & Purpose
- **User:** Single person
- **Purpose:** Remember weekly recurring personal chores.

## Behavior Rules
- Chores are defined as a list of names.
- Each chore has a boolean state: `done` or `not done`.
- Every Friday at midnight (or on first load on Friday), all chores auto-reset to `not done`.
- No completion history is tracked – only current week.

## Suggested Markdown File Format (example)
```markdown
# Weekly Chores (reset every Friday)

- [ ] Vacuum living room
- [ ] Clean bathroom sink
- [ ] Take out recycling
- [ ] Water plants