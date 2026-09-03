---
kind: error_handling
name: 'Error Handling: FastAPI HTTPException + Frontend Toast Context'
category: error_handling
scope:
    - '**'
source_files:
    - uaea-backend/app/main.py
    - uaea-backend/app/api/chat.py
    - uaea-backend/app/api/admin.py
    - uaea-backend/app/orchestrator/orchestrator.py
    - src/lib/api.js
    - src/context/ToastContext.jsx
    - src/components/ui/Toast.jsx
---

## Overview

The monorepo uses two distinct error-handling strategies, one per layer:

- **Backend (FastAPI)**: Structured errors via `fastapi.HTTPException` raised in route handlers and dependency functions, plus a global `RateLimitExceeded` handler. Business failures return typed Pydantic responses; network/LLM failures are caught and converted into user-friendly fallback replies.
- **Frontend (React SPA)**: A thin `fetch` wrapper in `src/lib/api.js` throws `Error` objects for any non-`resp.ok` response, propagating the backend's `detail` field. User-facing errors are surfaced through a centralized `ToastContext` (`useToast()`) that renders auto-dismissing toasts.

There is no shared error type between layers — the frontend simply forwards whatever string the backend puts in `detail`.

## Backend Error Patterns

### Centralized rate-limit handling
`uaea-backend/app/main.py` registers a single exception handler for `slowapi.errors.RateLimitExceeded`, returning a `429 JSONResponse` with `{ detail: "Rate limit exceeded: ..." }`. This is the only global exception handler in the app.

### Route-level `HTTPException`
Route handlers raise `fastapi.HTTPException` for domain errors:
- `app/api/chat.py`: raises `404` with `"Session not found"` when a conversation lookup returns `None`; raises `404` with `"No active conversation for this session"` on escalation of a resolved session.
- `app/api/admin.py`: the `verify_admin` dependency raises `403` with `"Admin access denied. Valid API key required."` when the `X-API-Key` header does not match `settings.admin_api_key`.

These are the only explicit error raises in the codebase; there are no custom exception classes or sentinel errors.

### LLM/network failure resilience
In `app/orchestrator/orchestrator.py`, calls to `anthropic.AsyncAnthropic.messages.create` are wrapped in `try/except anthropic.APIError`. On failure the orchestrator logs the error and returns a friendly fallback reply (`"I'm having trouble connecting right now..."`) instead of bubbling the exception up to the route layer. Exhaustion of the round-trip loop similarly returns a degraded message and sets `escalated = True`.

### Database/session errors
Database operations use SQLAlchemy async sessions obtained via `Depends(get_db)`. There are no explicit `try/except` blocks around DB queries in routes; unhandled DB exceptions will propagate to FastAPI's default 500 handler. The admin write paths do call `await db.commit()` after adding records but do not wrap them in try/except either.

### Logging
A root logger named `uaea` is configured at startup in `main.py` using `logging.basicConfig` with level taken from `settings.log_level`. Individual routers also create their own loggers (e.g., `logger = logging.getLogger("admin")`). Errors from the orchestrator are logged via `logger.error(...)` before returning a degraded response.

## Frontend Error Patterns

### Unified fetch wrapper
`src/lib/api.js` defines a single `request(path, options)` helper used by every exported function (`chatMessage`, `getSession`, `getDepartments`, etc.). It:
1. Calls `fetch(BASE_URL + path)`.
2. If `!resp.ok`, reads the JSON body (falling back to `{}` if parsing fails) and throws `new Error(body.detail || \`API error ${resp.status}\`)`.
3. Otherwise returns `resp.json()`.

This means all API consumers receive a plain `Error` object whose message contains either the backend's `detail` string or a generic status-based message.

### No global error boundary
There is no `ErrorBoundary` component or top-level `window.onerror` handler in `src/App.jsx` / `src/main.jsx`. Each page/component must catch errors from `api.*` calls locally. The grep search found no `.catch()` or `try/catch` blocks in JSX files, suggesting most UI code assumes success paths and relies on React's default unhandled rejection behavior for failures.

### Toast notifications
User-visible feedback is delivered through `src/context/ToastContext.jsx`, which exposes `useToast()` returning a `push(title, description, tone?)` function. Toasts auto-dismiss after 3600ms. Components can call `push('Error', 'Something went wrong', 'red')` to surface errors. The context itself throws `Error("useToast must be used inside <ToastProvider>")` if used outside its provider, which is a development-time invariant rather than a runtime error path.

## Conventions Observed

| Area | Convention | Evidence |
|---|---|---|
| Backend validation | Use Pydantic request/response models; invalid input is handled by FastAPI automatically (no manual validation in routes). | All route signatures use annotated request/response models from `app/schemas.py`. |
| Not-found errors | Raise `HTTPException(status_code=404, detail="...")` with a human-readable message. | `chat.py` session lookup and escalation. |
| Auth failures | Raise `HTTPException(status_code=403, detail="...")` from a `Depends` function. | `admin.py` `verify_admin`. |
| Rate limiting | Global `exception_handler` for `RateLimitExceeded` returning 429. | `main.py`. |
| External service failures | Catch specific SDK exceptions (`anthropic.APIError`) and return degraded responses instead of failing the request. | `orchestrator.py` LLM call loop. |
| Frontend API errors | Throw `Error` with `response.detail` as message from a single `request()` helper. | `src/lib/api.js`. |
| User feedback | Push messages via `useToast().push(title, desc, tone)`; tones default to `"jade"` (success). | `ToastContext.jsx`. |
| Admin audit | Write an `AuditLog` record for every admin write operation via `_audit_log`. | `admin.py`. |

## Key Files

- `uaea-backend/app/main.py` — global exception handler for rate limits, CORS middleware, router mounting.
- `uaea-backend/app/api/chat.py` — raises `HTTPException(404)` for missing sessions and inactive conversations.
- `uaea-backend/app/api/admin.py` — `verify_admin` dependency raises `HTTPException(403)`; audit logging helper.
- `uaea-backend/app/orchestrator/orchestrator.py` — catches `anthropic.APIError` and returns fallback replies; tracks unanswered queries.
- `src/lib/api.js` — single `request()` wrapper that converts non-OK responses to thrown `Error`s.
- `src/context/ToastContext.jsx` — centralized toast provider consumed via `useToast()`.
- `src/components/ui/Toast.jsx` — visual toast component rendered by the provider.