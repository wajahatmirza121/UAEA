---
kind: external_dependency
name: Web Framework — FastAPI with Uvicorn ASGI server
slug: fastapi-uvicorn
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
---

### Role
HTTP framework exposing the `/v1/chat/*`, `/v1/lookup/*`, and `/v1/admin/*` routers. Served by Uvicorn in standard mode.

### Integration points
- `app/main.py` mounts the three routers under the `/v1` prefix, configures CORS from `settings.cors_origins`, and attaches the `slowapi` rate-limiting middleware.
- Entry point is `uvicorn app.main:app --reload --port 8000` for local dev; containerized via the project `Dockerfile`.

### Stable usage notes
- Admin routes are protected by a simple API-key check reading `settings.admin_api_key`; full OTP auth is deferred to Phase 2.