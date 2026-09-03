---
kind: build_system
name: 'Monorepo Build & Deployment: Vite SPA + FastAPI via Docker Compose'
category: build_system
scope:
    - '**'
source_files:
    - package.json
    - vite.config.js
    - index.html
    - uaea-backend/Dockerfile
    - uaea-backend/docker-compose.yml
    - uaea-backend/requirements.txt
    - uaea-backend/alembic.ini
    - uaea-backend/pytest.ini
---

## What system/approach is used

The repository is a monorepo with two independently built services that are orchestrated together:

- **Frontend**: A React single-page application built with **Vite** (`vite build`), using the `@vitejs/plugin-react` plugin. The dev server runs on port 5173 and auto-opens the browser.
- **Backend**: A **FastAPI** service served by **Uvicorn**, with an async PostgreSQL database (pgvector) managed through **SQLAlchemy + Alembic**. Tests run under **pytest** with `asyncio_mode = auto`.
- **Packaging & deployment**: The backend is containerized in a multi-stage-free **Dockerfile** (single stage from `python:3.11-slim`) and both services are composed via **docker-compose.yml** (PostgreSQL + backend). There is no frontend container — the frontend is built as static assets and would be served by a separate web server or CDN.
- **No Makefile, no CI pipeline, no cross-compile scripts** were found at the repository root or within subprojects.

## Key files and packages

- `package.json` — defines npm scripts `dev`, `build`, `preview`; pins React 18, React Router 6, Lucide icons; declares Vite 5 and the React plugin as devDependencies.
- `vite.config.js` — configures the React plugin, an `@` path alias resolving to `src/`, dev server port 5173 with auto-open.
- `index.html` — Vite entry HTML (referenced by Vite).
- `uaea-backend/Dockerfile` — installs OS-level build deps (`build-essential`, `libpq-dev`), installs Python deps from `requirements.txt`, then copies source and runs Alembic migrations, seeds data, and starts Uvicorn on `0.0.0.0:8000`.
- `uaea-backend/docker-compose.yml` — defines two services: `db` (image `pgvector/pgvector:pg16` with healthcheck via `pg_isready`) and `backend` (builds from `.`, mounts source as `/app` for hot reload, forwards env from `.env`, depends on `db` being healthy).
- `uaea-backend/requirements.txt` — pinned dependency list for FastAPI, Uvicorn, SQLAlchemy+asyncpg, Alembic, Pydantic v2, Anthropic/OpenAI clients, pgvector, pypdf, httpx, slowapi (rate limiting), pytest suite.
- `uaea-backend/alembic.ini` — sets script location to `alembic/`, default connection string to `postgresql+psycopg2://uaea:uaea@localhost:5432/uaea`, and logging levels for root/sqlalchemy/alembic.
- `uaea-backend/pytest.ini` — enables `asyncio_mode = auto` and sets test discovery root to `tests/`.

## Architecture and conventions

- **Separate build roots**: The frontend and backend have independent build toolchains with no shared workspace configuration. Frontend builds produce static assets; backend builds produce a Python container image.
- **Environment-driven configuration**: Backend runtime settings come from environment variables loaded via `pydantic-settings` (see `uaea-backend/.env.example`); docker-compose injects `DATABASE_URL` / `DATABASE_URL_SYNC` pointing at the `db` service hostname.
- **Database lifecycle**: On container start, the entrypoint runs `alembic upgrade head` followed by `python -m app.db.seed`, ensuring schema and seed data are applied before the API starts accepting requests.
- **Development workflow**: `npm run dev` launches the Vite dev server; `docker compose up` brings up PostgreSQL and the backend with source mounted into `/app` for live code changes.
- **Testing**: Backend tests are discovered under `uaea-backend/tests/` and executed with `pytest` (asyncio auto-mode). No frontend test runner is configured in `package.json`.

## Conventions and constraints

- **Python dependency pinning**: All backend dependencies in `requirements.txt` are pinned to exact versions (e.g. `fastapi==0.115.0`, `uvicorn[standard]==0.30.6`, `sqlalchemy[asyncio]==2.0.35`), which ensures reproducible builds across environments.
- **Container base image**: The backend uses `python:3.11-slim` as its base image, keeping the runtime minimal while installing only `build-essential` and `libpq-dev` for native extensions.
- **Port conventions**: Frontend dev server listens on `5173`; backend API exposes `8000`; PostgreSQL exposes `5432`. These are hard-coded in `vite.config.js`, `Dockerfile` CMD, and `docker-compose.yml`.
- **Database credentials**: Default credentials `uaea:uaea` are embedded in `alembic.ini` and docker-compose defaults; production overrides should go through environment variables.
- **No versioning strategy beyond npm `version: "0.1.0"`**: The package manifest carries a version field but there is no documented release process, changelog, or tagging convention in the repository.
- **No CI/CD**: No GitHub Actions, GitLab CI, Jenkinsfile, or similar pipeline configuration was found; builds and deployments are intended to be run locally via `npm run build`, `docker compose up`, and `pytest`.