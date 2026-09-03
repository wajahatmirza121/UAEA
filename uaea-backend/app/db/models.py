"""SQLAlchemy models — all tables for UAEA backend."""

from __future__ import annotations

import datetime
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── Contact ───────────────────────────────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    office_hours: Mapped[str] = mapped_column(String(100), nullable=True)


# ── Campus ────────────────────────────────────────────────────────────────────

class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)

    contact: Mapped[Contact | None] = relationship(lazy="joined")


# ── Department ────────────────────────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ur: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    region_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)

    region: Mapped[Campus | None] = relationship(lazy="joined")
    contact: Mapped[Contact | None] = relationship(lazy="joined")


# ── FeeTariff ─────────────────────────────────────────────────────────────────

class FeeTariff(Base):
    __tablename__ = "fee_tariffs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    program: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)


# ── Service ───────────────────────────────────────────────────────────────────

class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ur: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    document_checklist: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    fee_id: Mapped[str] = mapped_column(String(36), ForeignKey("fee_tariffs.id"), nullable=True)
    deadline_id: Mapped[str] = mapped_column(String(36), nullable=True)
    procedure_text: Mapped[str] = mapped_column(Text, nullable=True)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)
    last_verified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )

    fee: Mapped[FeeTariff | None] = relationship(lazy="joined")


# ── Deadline ──────────────────────────────────────────────────────────────────

class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    service_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("services.id"), nullable=False
    )
    semester: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)

    service: Mapped[Service | None] = relationship(
        lazy="joined", foreign_keys="Deadline.service_id",
    )


# ── KnowledgeChunk (with pgvector) ───────────────────────────────────────────

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_doc_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(settings.embedding_dimensions), nullable=True)
    section: Mapped[str] = mapped_column(String(500), nullable=True)
    last_verified_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
    superseded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_chunks.id"), nullable=True
    )


# ── Conversation ──────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, tool, system
    text: Mapped[str] = mapped_column(Text, nullable=True)
    intent: Mapped[str] = mapped_column(String(60), nullable=True)
    tool_calls: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    feedback: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# ── EscalationTicket ─────────────────────────────────────────────────────────

class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    assigned_to: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


# ── AuditLog ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str] = mapped_column(String(60), nullable=False)
    record_id: Mapped[str] = mapped_column(String(60), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


# ── UnansweredQueue ──────────────────────────────────────────────────────────

class UnansweredQuery(Base):
    __tablename__ = "unanswered_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(60), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
