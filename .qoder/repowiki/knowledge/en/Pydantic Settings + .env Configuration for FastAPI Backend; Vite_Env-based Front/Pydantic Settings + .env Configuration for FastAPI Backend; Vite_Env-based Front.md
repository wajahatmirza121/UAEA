---
kind: configuration_system
name: Pydantic Settings + .env Configuration for FastAPI Backend; Vite/Env-based Frontend Config
category: configuration_system
scope:
    - '**'
source_files:
    - uaea-backend/app/config.py
    - uaea-backend/.env.example
    - uaea-backend/app/main.py
    - uaea-backend/app/db/session.py
    - uaea-backend/docker-compose.yml
    - vite.config.js
    - package.json
---

## What system/approach is used

The repository uses two distinct configuration approaches — one for the FastAPI backend and a minimal one for the React/Vite frontend.

**Backend (FastAPI):** A single centralized `pydantic_settings.BaseSettings` class (`app/config.py`) defines every runtime setting with defaults. The class declares an `env_file = ".env"` in its `model_config`, so values are loaded from the `.env` file at import time, then overridable by OS environment variables. This is the only place settings are defined; all other modules consume them via the module-level `settings` singleton imported from `app.config`.

**Frontend (Vite/React):** Configuration is minimal — build/dev server options live in `vite.config.js` (port 5173, path alias `@` → `src/`). There is no runtime config loader in the SPA; API endpoints are hard-coded relative paths (e.g. `/v1/chat/message`), and the dev server proxies to port 8000. No `.env` or feature flags are consumed by the frontend code.

## Key files and packages

- `uaea-backend/app/config.py` — sole source of truth for all backend settings (database URLs, LLM keys, embedding provider/model/dimensions, CORS origins, rate limits, admin API key, `app_env`, `log_level`).
- `uaea-backend/.env` — local secrets and overrides (loaded automatically by Pydantic).
- `uaea-backend/.env.example` — template showing required env vars.
- `uaea-backend/app/main.py` — consumes `settings` to configure logging level, CORS middleware, and logs CORS/rate-limit values at startup.
- `uaea-backend/app/db/session.py` — constructs the async SQLAlchemy engine using `settings.database_url`.
- `uaea-backend/docker-compose.yml` — injects `DATABASE_URL` / `DATABASE_URL_SYNC` into the container and loads `.env` via `env_file: .env`.
- `vite.config.js` — frontend build/dev configuration (port, aliases).
- `package.json` — scripts (`dev`, `build`, `preview`) that drive Vite.

## Architecture and conventions

1. **Single-settings object.** Every module that needs configuration imports `from app.config import settings` and reads attributes directly (e.g. `settings.database_url`, `settings.cors_origins`, `settings.log_level`, `settings.rate_limit_per_ip`). There is no per-feature config file, no YAML/TOML, and no nested config hierarchy.
2. **Defaults everywhere.** Each setting has a sensible default in the `Settings` class (e.g. `postgresql+asyncpg://uaea:uaea@localhost:5432/uaea`, `development` for `app_env`, `INFO` for `log_level`, `60/minute` for IP rate limit). This lets the app start without a `.env` file, which is useful for local development and tests.
3. **Environment variable override.** Because Pydantic Settings merges `.env` with real OS env vars, production deployments can supply values entirely through environment variables (as demonstrated by `docker-compose.yml`, which sets `DATABASE_URL` and `DATABASE_URL_SYNC` explicitly while also loading `.env`).
4. **Feature toggling via string flags.** `app_env` is a plain string (`development` vs presumably `production`) and is used to conditionally enable CORS wildcard (`allow_origins=["*"]` when `app_env == "development"` and no explicit origins are set). `log_level` is read via `getattr(logging, settings.log_level.upper(), logging.INFO)` to select Python's logging level.
5. **Secrets as top-level settings.** API keys (`anthropic_api_key`, `embedding_api_key`, `admin_api_key`) are declared as plain `str` fields with placeholder defaults — there is no encryption, vault integration, or separate secrets store. They are expected to be provided via `.env` or container env.
6. **Dockerized deployment model.** `docker-compose.yml` runs PostgreSQL (`pgvector/pgvector:pg16`) alongside the backend, passing DB credentials through environment variables and mounting `.env`. The backend service depends on the DB being healthy before starting.
7. **Frontend config is static.** The SPA has no runtime configuration mechanism. Paths like `/v1/chat/message` are hardcoded in components, and the dev server proxy (not shown here but implied by port 5173) forwards them to the backend on port 8000.

## Conventions and constraints

- **All backend configuration goes through `app/config.Settings`.** Adding a new setting requires defining it as a field on the class with a default; there is no dynamic config loading elsewhere.
- **`.env` is the local-only secret carrier.** It is listed in `.gitignore` implicitly (the repo ships `.env.example` instead), and Docker Compose explicitly loads it via `env_file: .env`.
- **Database URLs come in pairs:** `database_url` (asyncpg) and `database_url_sync` (psycopg2) — both must be kept in sync when changing credentials or host.
- **CORS is permissive in development.** When `app_env == "development"` and no explicit `cors_origins` are set, the middleware allows all origins (`["*"]`). Production should set `cors_origins` explicitly.
- **Rate limiting is configured via human-readable strings** (`"60/minute"`, `"30/minute"`) passed to `slowapi.Limiter`; they are not parsed by the app but forwarded verbatim.
- **Admin access gate:** `admin_api_key` is a shared secret intended to protect admin endpoints (consumed by the `admin` router); it defaults to a development key and is documented as needing change in production.
- **Logging level is controlled by `log_level`** and applied once at startup via `logging.basicConfig`.
- **Frontend build/dev config lives only in `vite.config.js`**; there is no concept of per-environment configs (no `.env.*` files consumed by Vite in this repo). The dev server listens on port 5173 and opens the browser automatically.