---
kind: logging_system
name: Python stdlib logging with hierarchical module loggers and env-driven level
category: logging_system
scope:
    - '**'
source_files:
    - uaeA-backend/app/main.py
    - uaeA-backend/app/config.py
    - uaeA-backend/app/api/admin.py
    - uaeA-backend/app/orchestrator/orchestrator.py
    - uaeA-backend/app/orchestrator/guardrails.py
    - uaeA-backend/app/rag/ingest.py
    - uaeA-backend/app/rag/retrieve.py
    - uaeA-backend/alembic/env.py
---

## What system/approach is used

The backend uses Python's built-in `logging` module exclusively — no third-party logging framework (e.g. structlog, loguru, or a JSON formatter) is configured. The FastAPI application bootstraps logging once at startup in `app/main.py` via `logging.basicConfig`, which sets the global root handler, output format, and minimum severity level.

The frontend SPA does not implement any application-level logging; it surfaces user-facing feedback through a local `ToastContext`/`Toast.jsx` component rather than console logs or analytics. Therefore the logging system applies only to the `uaeA-backend` service.

## Key files and packages

- `uaeA-backend/app/main.py` — single point of logging configuration: `logging.basicConfig(level=..., format="%(asctime)s %(name)-24s %(levelname)-7s %(message)s")`; creates the root `uaea` logger; emits startup/shutdown and CORS/rate-limit config lines.
- `uaeA-backend/app/config.py` — `Settings.log_level: str = "INFO"` loaded from `.env` / environment variables; this value drives the root logger level via `getattr(logging, settings.log_level.upper(), logging.INFO)`.
- `uaeA-backend/app/api/admin.py` — module logger `logging.getLogger("admin")`, used to record admin write actions (FAQ, fee tariff creation).
- `uaeA-backend/app/orchestrator/orchestrator.py` — module logger `logging.getLogger("orchestrator")`, used for LLM tool-call tracing (`logger.info(f"Tool call: {tool_name}({tool_args})")`) and API error reporting.
- `uaeA-backend/app/orchestrator/guardrails.py` — module logger `logging.getLogger("guardrails")`.
- `uaeA-backend/app/rag/ingest.py` — module logger `logging.getLogger("rag.ingest")`, used for ingestion progress and warnings (e.g. empty chunks).
- `uaeA-backend/app/rag/retrieve.py` — module logger `logging.getLogger("rag.retrieve")`.
- `uaeA-backend/alembic/env.py` — imports `logging.config.fileConfig`, indicating Alembic can be driven by an external logging config file if one is provided (not currently used by the app itself).

## Architecture and conventions

1. **Hierarchical logger names per module**: Each subsystem defines its own logger via `logging.getLogger("<domain>")` — `uaea` (root), `admin`, `orchestrator`, `guardrails`, `rag.ingest`, `rag.retrieve`. This produces a dotted hierarchy that lets consumers filter by domain (e.g. `uaea.rag`).

2. **Single global configuration**: All handlers are attached by `logging.basicConfig` in `main.py` before any router is mounted. There is no per-module handler setup; every module inherits the root handler(s).

3. **Log level is runtime-configurable**: The minimum level comes from `settings.log_level` (default `INFO`), read from `.env` or environment variables. No separate debug/production configs exist.

4. **Plain-text structured fields via f-strings**: Log messages are plain strings built with f-strings that embed contextual keys such as `source_doc_id`, `tool_name`, `tool_args`, `actor`, `chunk_id`. There is no JSON serialization or dedicated structured-log event schema — downstream parsing would need to parse these free-form lines.

5. **Audit trail is separate from log output**: Administrative mutations are persisted to the `AuditLog` database table via `_audit_log()` helper in `app/api/admin.py`. This is distinct from the stdout/stderr `logging` calls and serves as the durable audit record.

6. **Frontend has no server-side logging**: The React SPA uses a toast notification system (`src/context/ToastContext.jsx`, `src/components/ui/Toast.jsx`) for user feedback and does not emit application logs to a backend sink.

## Conventions and constraints

- **Every module that needs logging declares a module-level `logger = logging.getLogger("<name>")`** — observed consistently across `api/admin.py`, `orchestrator/orchestrator.py`, `orchestrator/guardrails.py`, `rag/ingest.py`, `rag/retrieve.py`, and `main.py`.
- **Severity usage follows standard levels**: `logger.info` for normal operational events (startup, tool calls, ingestion counts, admin writes), `logger.warning` for non-fatal issues (empty chunks), `logger.error` for failures (Anthropic API errors). No `debug` or `critical` calls were observed.
- **Log level is controlled externally via `LOG_LEVEL` / `log_level` env var** through `pydantic_settings`; changing it requires redeploying the container or setting the env at process start.
- **No request/response middleware logging**: The codebase does not log HTTP requests/responses centrally; visibility into chat flows relies on the orchestrator's internal `info`/`error` calls plus the persisted `Message`/`AuditLog` tables.
- **Alembac logging is decoupled**: `alembic/env.py` imports `logging.config.fileConfig`, allowing Alembic migrations to use a separate config file, but the app itself does not configure it.