"""Shared test fixtures — creates a test DB with seed data."""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Use a temp file for the test DB (shared across connections)
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "uaea_test.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Force test settings before any app imports
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["LLM_API_KEY"] = "xai-test-REPLACE"
os.environ["EMBEDDING_API_KEY"] = "sk-REPLACE-ME"
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["APP_ENV"] = "test"
os.environ["WHATSAPP_PROVIDER"] = "console"
os.environ["OTP_DEV_ECHO"] = "false"
os.environ["TODAY_OVERRIDE"] = "2026-10-20"
# The suite sends hundreds of chat requests from one "IP" — lift rate limits.
os.environ["RATE_LIMIT_PER_IP"] = "100000/minute"
os.environ["RATE_LIMIT_PER_SESSION"] = "100000/minute"

# Patch Vector type for SQLite before models are imported
from sqlalchemy import TypeDecorator, Text
from pgvector.sqlalchemy import Vector


# Render Vector as TEXT in SQLite DDL
from sqlalchemy.ext.compiler import compiles


@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"


from app.db.models import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def engine():
    # Remove old test DB if exists
    if os.path.exists(TEST_DB_PATH):
        os.unlink(TEST_DB_PATH)

    eng = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.unlink(TEST_DB_PATH)
        except Exception:
            pass


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


_SEEDED = {"done": False}


@pytest_asyncio.fixture
async def seeded_db(engine) -> AsyncGenerator[AsyncSession, None]:
    """A session on a DB holding the full demo dataset (seeded once per run).

    Per-test state (conversations, OTP challenges, tickets) is cleared so tests
    don't affect each other.
    """
    from app.db.seed import seed_all

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        if not _SEEDED["done"]:
            await seed_all(session)
            _SEEDED["done"] = True
        else:
            for table in ["otp_challenges", "escalation_tickets", "messages", "conversations"]:
                await session.execute(text(f"DELETE FROM {table}"))
            await session.commit()
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(seeded_db) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client with the DB dependency overridden."""

    async def _override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
