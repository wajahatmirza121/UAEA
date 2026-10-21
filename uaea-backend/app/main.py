"""FastAPI application — CORS, rate limiting, router mounting."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.api import chat, lookup, admin

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)-24s %(levelname)-7s %(message)s",
)
logger = logging.getLogger("uaea")

# ── Rate limiter (per-IP via slowapi) ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Per-session rate limit state ─────────────────────────────────────────────
# Simple in-memory sliding window: session_id → list of timestamps
_session_requests: dict[str, list[float]] = defaultdict(list)

def _parse_rate_limit(rate_str: str) -> tuple[int, float]:
    """Parse '30/minute' into (30, 60.0)."""
    count, _, window = rate_str.partition("/")
    seconds_map = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
    max_count = int(count)
    window_sec = float(seconds_map.get(window, 60))
    return max_count, window_sec


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("UAEA backend starting…")
    yield
    logger.info("UAEA backend shutting down…")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="UAEA Backend",
    description="Urdu AI Educational Assistant — university student-services chatbot backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount rate limiter
app.state.limiter = limiter


# ── Rate limit error handler ──────────────────────────────────────────────────

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


# ── CORS ──────────────────────────────────────────────────────────────────────

cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if settings.app_env == "development" and not cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(chat.router)
app.include_router(lookup.router)
app.include_router(admin.router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "uaea-backend"}


# ── Per-session rate limit middleware ─────────────────────────────────────────

SESSION_MAX, SESSION_WINDOW = _parse_rate_limit(settings.rate_limit_per_session)

@app.middleware("http")
async def session_rate_limit(request: Request, call_next):
    """Apply per-session rate limiting on chat message endpoint.

    Reads session_id from the JSON body and enforces a sliding-window
    rate limit. Falls back to IP-based limiting if session_id is missing.
    """
    if request.url.path == "/v1/chat/message" and request.method == "POST":
        try:
            body = await request.body()
            import json
            payload = json.loads(body) if body else {}
            session_id = payload.get("session_id")

            if session_id:
                now = time.time()
                cutoff = now - SESSION_WINDOW
                # Prune old entries
                _session_requests[session_id] = [
                    t for t in _session_requests[session_id] if t > cutoff
                ]
                if len(_session_requests[session_id]) >= SESSION_MAX:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": f"Session rate limit: max {SESSION_MAX} requests per {int(SESSION_WINDOW)}s"},
                    )
                _session_requests[session_id].append(now)
        except Exception:
            pass  # Body parsing failure — let IP limiter handle it

    response = await call_next(request)
    return response


logger.info(f"CORS origins: {cors_origins}")
logger.info(f"Rate limit (per IP): {settings.rate_limit_per_ip}")
logger.info(f"Rate limit (per session): {settings.rate_limit_per_session}")
