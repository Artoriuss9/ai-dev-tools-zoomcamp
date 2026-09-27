# Shared Chores Tool Backlog

The backlog below is derived from [docs/plan.md](docs/plan.md). It keeps the first release intentionally small: one user, one weekly chore list, and Markdown as the source of truth.

## 1. Add the Django chores page

Create a view, URL, and template that display the current chore list with each item marked as done or not done.

**Acceptance criteria**
- The root page renders the chores from the Markdown file.
- Empty and missing files produce a usable empty-list state.
- The page does not introduce fields beyond the chore name and done state.

## 2. Implement Markdown parsing and serialization

Add a small service module that reads and writes the agreed checkbox format:

```markdown
# Weekly Chores (reset every Friday)

- [ ] Vacuum living room
- [x] Clean bathroom sink
```

**Acceptance criteria**
- Checkbox states parse into a list of chore names and booleans.
- Saving preserves the header and writes valid Markdown.
- Malformed or unknown lines do not silently become chores.
- File writes are safe against partial output, for example by writing a temporary file and replacing the original.

## 3. Add the done/not done toggle

Add a POST endpoint and template controls for toggling one chore at a time.

**Acceptance criteria**
- Toggling a chore changes only that chore's checkbox.
- POST requests are protected by Django CSRF middleware.
- The user is redirected back to the list after a successful toggle.
- Invalid chore identifiers return a clear 404 or validation response.

## 4. Implement the Friday reset rule

Add a service-level reset check that resets every checkbox to not done on the first load occurring on Friday when the stored week has not already been reset.

**Acceptance criteria**
- A reset occurs at Friday midnight or on the first Friday request.
- Repeated Friday requests do not repeatedly rewrite the file.
- No completion history is created.
- The reset behavior is independent of the server process lifetime.

## 5. Add focused automated tests

Cover the parser, writer, toggle flow, and weekly reset behavior using temporary Markdown files and Django test clients.

**Acceptance criteria**
- Tests cover checked and unchecked items.
- Tests cover missing, empty, and malformed input.
- Tests verify a toggle persists to Markdown.
- Tests verify the reset is idempotent and does not affect chore names.

## 6. Configure the storage path and local workflow

Make the Markdown file location configurable through Django settings and document the commands needed to run the app locally.

**Acceptance criteria**
- The default file lives in a predictable project-local location.
- Tests can override the path without modifying repository files.
- `python manage.py migrate` and `python manage.py runserver` are documented.
- The project does not use the database as a second source of truth for chore state.
