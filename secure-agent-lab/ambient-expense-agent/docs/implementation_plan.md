# Refactor FastAPI app to share InMemoryRunner instance across routes

## Goal Description

The GET endpoint `/apps/expense_agent/sessions/{session_id}` currently creates a new `InMemoryRunner`, which results in an empty session store and a "Session not found" error. We need to ensure a single shared `InMemoryRunner` (and its underlying `session_service`) is used by all FastAPI routes so that session state persists across requests.

## User Review Required

> [!IMPORTANT]
> This change modifies the FastAPI application's startup and dependency handling. Confirm that you are comfortable with either a module‑level singleton or using FastAPI's `Depends`/startup event for the shared runner.

## Open Questions

> [!CAUTION]
> - Do you prefer the runner to be instantiated at import time (module‑level) or via a FastAPI startup event using dependency injection?
> - Should the shared `runner` be exported (e.g., `app.runner`) for potential external use, or kept private within `app/main.py`?

## Proposed Changes

---
### app/main.py

- **Create a single `runner` instance**
  ```python
  from expense_agent.runner import InMemoryRunner
  runner = InMemoryRunner()
  ```
  Place this at module level or inside a `@app.on_event("startup")` handler.
- **Update POST `/apps/expense_agent/trigger/pubsub`** to use the shared `runner` instead of constructing a new one.
- **Update GET `/apps/expense_agent/sessions/{session_id}`** to retrieve session data via `runner.session_service.get_session(session_id)`.
- **Add type hints** and docstrings for clarity.
- **Ensure imports are tidy** and no circular dependencies exist.

---
### expense_agent/nodes.py (Optional)

- Verify that any console logging symbols (`→`, `≥`) have been replaced with ASCII equivalents (`->`, `>=`) to avoid Windows encoding issues.

---
## Verification Plan

### Automated Tests
- Run `uv run pytest tests/unit tests/integration` to ensure all existing tests pass.
- Add a new test that posts a Pub/Sub payload, then GETs the session state and asserts the expected fields (`security_flagged`, `status`, redacted description).

### Manual Verification
- Use the provided `curl` command to POST to `/apps/expense_agent/trigger/pubsub`.
- Immediately GET `/apps/expense_agent/sessions/{session_id}` and confirm the JSON contains the session data rather than an error.
- Check that SSN values are redacted and `security_flagged` is `true` when injection is detected.
