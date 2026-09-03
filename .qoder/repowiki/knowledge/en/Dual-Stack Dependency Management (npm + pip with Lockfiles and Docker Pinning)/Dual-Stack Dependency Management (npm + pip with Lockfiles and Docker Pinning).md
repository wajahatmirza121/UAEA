---
kind: dependency_management
name: Dual-Stack Dependency Management (npm + pip with Lockfiles and Docker Pinning)
category: dependency_management
scope:
    - '**'
source_files:
    - package.json
    - package-lock.json
    - vite.config.js
    - uaea-backend/requirements.txt
    - uaea-backend/Dockerfile
    - uaea-backend/docker-compose.yml
    - uaea-backend/.env.example
---

## Overview

This monorepo manages dependencies for two distinct stacks in a single repository:
- **Frontend** (React SPA built with Vite) — managed via npm.
- **Backend** (FastAPI service) — managed via Python `pip`.

There is no unified workspace tool (no `pnpm`, `yarn`, or npm workspaces); each stack maintains its own manifest and lockfile at the repo root / subproject level.

## Frontend Dependencies (npm)

- **Manifest**: `package.json` declares runtime dependencies (`react`, `react-dom`, `react-router-dom`, `lucide-react`) and dev dependencies (`vite`, `@vitejs/plugin-react`). All versions use caret ranges (`^x.y.z`), allowing minor/patch upgrades within the same major line.
- **Lockfile**: `package-lock.json` (lockfileVersion 3) pins every transitive dependency to an exact version and records the resolved URL from `https://registry.npmjs.org/`. This is the source of truth for reproducible installs.
- **Build aliasing**: `vite.config.js` configures an `@` path alias pointing to `src/`, which is a build-time resolution, not a package manager feature.
- **No vendoring**: There is no `node_modules/` committed; dependencies are installed on demand by `npm install`.
- **No private registry or scoped packages**: All packages come from the public npm registry.

## Backend Dependencies (pip)

- **Manifest**: `uaea-backend/requirements.txt` pins every dependency to an exact version using `==` (e.g. `fastapi==0.115.0`, `uvicorn[standard]==0.30.6`, `sqlalchemy[asyncio]==2.0.35`, `anthropic==0.34.2`, `openai==1.51.0`, `pgvector==0.3.5`, `pytest==8.3.3`, etc.). This is stricter than semver ranges and ensures deterministic builds.
- **No lockfile**: There is no `requirements.lock`, `Pipfile.lock`, `poetry.lock`, or `uv.lock`; reproducibility relies on the exact `==` pins in `requirements.txt`.
- **Docker pinning**: The `Dockerfile` uses `FROM python:3.11-slim` (a rolling tag) and runs `pip install --no-cache-dir -r requirements.txt`. It also installs system-level build deps (`build-essential`, `libpq-dev`) needed by `psycopg2-binary` and `asyncpg`.
- **Runtime entrypoint**: The container CMD runs Alembic migrations, seeds the DB, then starts uvicorn on port 8000.
- **No vendoring**: No `vendor/` directory; packages are fetched from PyPI at build time.
- **No private registry**: No `--index-url`, `--extra-index-url`, or `.netrc` configuration is present.

## Cross-Cutting Conventions Observed

1. **Exact pins for backend, caret ranges for frontend**: The Python side uses `==` pins for full determinism; the Node side uses `^` ranges, deferring exact pinning to `package-lock.json`.
2. **Single lockfile per stack**: npm uses `package-lock.json`; Python has no lockfile counterpart.
3. **Containerized backend build**: The Dockerfile is the authoritative deployment recipe and re-installs all Python dependencies from `requirements.txt` on every build.
4. **No shared dependency graph**: The frontend and backend have no cross-imports at the package-manager level; they communicate over HTTP (the frontend calls the backend API).
5. **No monorepo workspace**: There is no `workspaces` field in `package.json` and no `pyproject.toml`; each language stack is self-contained.
6. **System-level deps co-located with Python deps**: C-extension wheels (`psycopg2-binary`, `asyncpg`) require OS headers installed via `apt-get` inside the Docker image before `pip install`.

## Key Files

- `package.json` — npm manifest (runtime + dev deps, scripts).
- `package-lock.json` — npm lockfile pinning every transitive dependency.
- `vite.config.js` — build-time module aliasing (`@` → `src`).
- `uaea-backend/requirements.txt` — pinned Python dependencies.
- `uaea-backend/Dockerfile` — base image, system deps, and `pip install` step.
- `uaea-backend/docker-compose.yml` — orchestrates the backend container (implied by presence).
- `uaea-backend/.env.example` — environment-driven configuration (secrets/keys not checked in).

## Constraints & Rules Enforced by the Repo

- Backend Python dependencies must be declared in `requirements.txt` with exact `==` pins; the Docker build will fail if any listed package cannot be resolved from PyPI.
- Frontend dependencies must be declared in `package.json`; `npm install` will generate/update `package-lock.json` as the canonical lock.
- The Docker image rebuilds the entire Python dependency tree from scratch on every `docker build`, so changes to `requirements.txt` always propagate into images.
- No private registries, scoped packages, or vendored third-party code are used anywhere in this repo.