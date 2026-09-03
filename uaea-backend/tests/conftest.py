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


@pytest_asyncio.fixture
async def seeded_db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a session with seed data inserted."""
    import datetime

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        from app.db.models import (
            Contact, Campus, Department, FeeTariff, Service, Deadline,
            KnowledgeChunk, UnansweredQuery,
        )

        # Clear existing data (idempotent)
        for table in ["unanswered_queries", "audit_logs", "escalation_tickets",
                       "messages", "conversations", "knowledge_chunks",
                       "deadlines", "services", "fee_tariffs", "departments",
                       "campuses", "contacts"]:
            try:
                await session.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass

        # Seed contacts
        contacts = [
            Contact(id="ct-01", phone="051-9250101", email="admissions@uaea.edu.pk", office_hours="09:00-16:30"),
            Contact(id="ct-02", phone="051-9250142", email="exams@uaea.edu.pk", office_hours="09:00-16:30"),
        ]
        for c in contacts:
            session.add(c)

        # Seed campuses
        campuses = [
            Campus(id="camp-01", name="Islamabad Main Campus", region="Islamabad", address="H-8, Islamabad", contact_id="ct-01"),
        ]
        for c in campuses:
            session.add(c)

        # Seed departments
        depts = [
            Department(id="dep-01", name_en="Directorate of Admissions", name_ur="شعبۂ داخلہ", category="Admissions", region_id="camp-01", contact_id="ct-01"),
            Department(id="dep-02", name_en="Examinations Department", name_ur="شعبۂ امتحانات", category="Examinations", region_id="camp-01", contact_id="ct-02"),
        ]
        for d in depts:
            session.add(d)

        # Seed fee tariffs
        fees = [
            FeeTariff(id="fee-01", program="BS Computer Science", category="Semester (new)", amount=28500, effective_from=datetime.date(2026, 7, 1), source_doc_ref="Fee Circular A-26 §3.1"),
            FeeTariff(id="fee-02", program="BS Computer Science", category="Per credit hour (repeat)", amount=2150, effective_from=datetime.date(2026, 7, 1), source_doc_ref="Fee Circular A-26 §3.2"),
            FeeTariff(id="fee-08", program="Degree", category="Normal service", amount=2000, effective_from=datetime.date(2026, 1, 1), source_doc_ref="Degree Manual §3.5"),
        ]
        for f in fees:
            session.add(f)

        # Seed services
        services = [
            Service(id="svc-01", name_en="Admission & Enrolment", name_ur="داخلہ و اندراج", category="Admissions", fee_id="fee-01",
                    description="Apply for admission.", procedure_text="Apply online.",
                    document_checklist=[
                        {"en": "CNIC or B-Form", "ur": "شناختی کارڈ", "copy": True},
                        {"en": "Previous degree or certificate", "ur": "پچھلی ڈگری", "copy": True},
                    ],
                    source_doc_ref="Prospectus 2026-27 §2.1"),
            Service(id="svc-04", name_en="Degree Application", name_ur="ڈگری کی درخواست", category="Certification", fee_id="fee-08",
                    description="Apply for degree issuance.", procedure_text="Submit to Degree Section.",
                    document_checklist=[
                        {"en": "Degree application form", "ur": "ڈگری درخواست فارم", "copy": False},
                        {"en": "All semester result cards", "ur": "تمام سمسٹر کے رزلٹ کارڈ", "copy": True},
                        {"en": "CNIC", "ur": "شناختی کارڈ", "copy": True},
                    ],
                    source_doc_ref="Degree Manual §3"),
        ]
        for s in services:
            session.add(s)

        # Seed deadlines
        deadlines = [
            Deadline(id="dl-01", service_id="svc-01", semester="Autumn 2026", date=datetime.date(2026, 9, 30), source_doc_ref="Admission Notice A-26/11"),
            Deadline(id="dl-03", service_id="svc-04", semester="Spring 2026 graduates", date=datetime.date(2026, 11, 30), source_doc_ref="Degree Manual §3.1"),
        ]
        for dl in deadlines:
            session.add(dl)

        # Seed knowledge chunks (embedding stored as TEXT in SQLite)
        chunks = [
            KnowledgeChunk(id="kc-01", source_doc_id="prospectus-2026", section="§2 Admission Policy",
                           text="Admission to all undergraduate programmes requires at least 50% marks in the qualifying examination."),
            KnowledgeChunk(id="kc-05", source_doc_id="exam-regs-2026", section="§7 Results",
                           text="Results are published on the results portal once the gazette is notified."),
        ]
        for kc in chunks:
            session.add(kc)

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
