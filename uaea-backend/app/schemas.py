"""Pydantic request/response schemas for all API endpoints."""

from __future__ import annotations

import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Lookup ────────────────────────────────────────────────────────────────────

class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    phone: str | None = None
    email: str | None = None
    office_hours: str | None = None


class CampusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    region: str
    address: str | None = None
    contact: ContactOut | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name_en: str
    name_ur: str | None = None
    category: str
    region: CampusOut | None = None
    contact: ContactOut | None = None


class FeeTariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    program: str
    category: str
    amount: int
    effective_from: datetime.date
    source_doc_ref: str | None = None


class ChecklistItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    en: str
    ur: str | None = None
    needs_copy: bool = Field(default=False, alias="copy")


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name_en: str
    name_ur: str | None = None
    category: str
    description: str | None = None
    document_checklist: list[ChecklistItem] = []
    procedure_text: str | None = None
    source_doc_ref: str | None = None
    last_verified_at: datetime.datetime | None = None
    fee: FeeTariffOut | None = None


class DeadlineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    service_id: str
    semester: str
    date: datetime.date
    source_doc_ref: str | None = None


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    channel: str = "web"
    text: str = Field(min_length=1, max_length=2000)


class ToolCallOut(BaseModel):
    name: str
    args: dict[str, Any] | None = None
    result: Any = None


class ChatMessageResponse(BaseModel):
    reply: str
    intent: str | None = None
    tool_calls: list[ToolCallOut] = []
    escalated: bool = False
    confidence: float = 0.0
    language: str = "en"
    sources: list[dict[str, Any]] = []
    intent_label: str | None = None
    otp: dict[str, Any] | None = None          # set when a WhatsApp code was sent / is pending
    verified_roll: str | None = None           # set on the turn the OTP was accepted
    engine: str | None = None                  # groq | offline | otp
    model: str | None = None
    resolved: bool = True


class EscalateRequest(BaseModel):
    session_id: str
    reason: str


class EscalateResponse(BaseModel):
    ticket_id: str
    status: str = "open"


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: str
    channel: str
    started_at: datetime.datetime
    resolved: bool = False
    escalated: bool = False
    messages: list[dict[str, Any]] = []


# ── Admin ─────────────────────────────────────────────────────────────────────

class FAQCreate(BaseModel):
    source_doc_id: str
    text: str
    section: str | None = None


class FAQOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_doc_id: str
    text: str
    section: str | None = None
    last_verified_at: datetime.datetime | None = None


class FeeTariffCreate(BaseModel):
    program: str
    category: str
    amount: int
    effective_from: datetime.date
    source_doc_ref: str | None = None


class AdminWriteResponse(BaseModel):
    id: str
    status: str = "ok"


class IntentCount(BaseModel):
    intent: str
    count: int


class UnansweredQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    text: str
    intent: str | None = None
    confidence: float | None = None
    count: int = 1
    reason: str | None = None


# ── RAG Retrieval ─────────────────────────────────────────────────────────────

class ChunkResult(BaseModel):
    id: str
    text: str
    source_doc_id: str
    section: str | None = None
    score: float
    last_verified_at: datetime.datetime | None = None
