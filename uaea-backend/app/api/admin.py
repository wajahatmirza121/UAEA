"""Admin API routes — /v1/admin/*.

All admin routes require an API key or bearer token (RBAC stub).
"""

from __future__ import annotations

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import (
    KnowledgeChunk, FeeTariff, Message, UnansweredQuery, AuditLog,
)
from app.schemas import (
    FAQCreate, FAQOut, FeeTariffCreate, FeeTariffOut,
    AdminWriteResponse, IntentCount, UnansweredQueryOut,
)
from app.rag.ingest import ingest_document, get_embedding

logger = logging.getLogger("admin")
router = APIRouter(prefix="/v1/admin", tags=["admin"])


# ── RBAC stub ─────────────────────────────────────────────────────────────────

async def verify_admin(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
):
    """Verify admin access via API key or bearer token.

    This is a stub — Phase 2 will implement full OTP auth.
    """
    token = None
    if x_api_key:
        token = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token or token != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin access denied. Valid API key required.")

    return token


# ── Audit helper ──────────────────────────────────────────────────────────────

async def _audit_log(db: AsyncSession, actor: str, action: str, table_name: str, record_id: str, detail: dict):
    """Write an audit log entry for admin content writes."""
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor=actor,
        action=action,
        table_name=table_name,
        record_id=record_id,
        detail=detail,
    ))


# ── Content: FAQ ──────────────────────────────────────────────────────────────

@router.post("/content/faq", response_model=AdminWriteResponse)
async def create_faq(
    req: FAQCreate,
    db: AsyncSession = Depends(get_db),
    actor: str = Depends(verify_admin),
):
    """Create or update a FAQ knowledge chunk. Embeds and stores via RAG pipeline."""
    chunk_id = str(uuid.uuid4())
    embedding = await get_embedding(req.text)

    chunk = KnowledgeChunk(
        id=chunk_id,
        source_doc_id=req.source_doc_id,
        text=req.text,
        embedding=embedding,
        section=req.section,
    )
    db.add(chunk)

    await _audit_log(db, actor, "create", "knowledge_chunks", chunk_id, {
        "source_doc_id": req.source_doc_id,
        "section": req.section,
        "text_preview": req.text[:100],
    })

    await db.commit()
    logger.info(f"Admin '{actor}' created FAQ chunk {chunk_id}")
    return AdminWriteResponse(id=chunk_id, status="ok")


# ── Content: Fee Tariff ───────────────────────────────────────────────────────

@router.post("/content/fee-tariff", response_model=AdminWriteResponse)
async def create_fee_tariff(
    req: FeeTariffCreate,
    db: AsyncSession = Depends(get_db),
    actor: str = Depends(verify_admin),
):
    """Create or update a fee tariff entry."""
    fee_id = str(uuid.uuid4())
    fee = FeeTariff(
        id=fee_id,
        program=req.program,
        category=req.category,
        amount=req.amount,
        effective_from=req.effective_from,
        source_doc_ref=req.source_doc_ref,
    )
    db.add(fee)

    await _audit_log(db, actor, "create", "fee_tariffs", fee_id, {
        "program": req.program,
        "category": req.category,
        "amount": req.amount,
    })

    await db.commit()
    logger.info(f"Admin '{actor}' created fee tariff {fee_id}")
    return AdminWriteResponse(id=fee_id, status="ok")


# ── Analytics: Intents ────────────────────────────────────────────────────────

@router.get("/analytics/intents", response_model=list[IntentCount])
async def get_intent_analytics(
    db: AsyncSession = Depends(get_db),
    _actor: str = Depends(verify_admin),
):
    """Get counts of messages grouped by intent."""
    stmt = (
        select(Message.intent, sql_func.count(Message.id).label("count"))
        .where(Message.role == "user", Message.intent.isnot(None))
        .group_by(Message.intent)
        .order_by(sql_func.count(Message.id).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [IntentCount(intent=row.intent or "unknown", count=row.count) for row in rows]


# ── Queue: Unanswered ─────────────────────────────────────────────────────────

@router.get("/queue/unanswered", response_model=list[UnansweredQueryOut])
async def get_unanswered_queue(
    db: AsyncSession = Depends(get_db),
    _actor: str = Depends(verify_admin),
):
    """Get the queue of unanswered / low-confidence queries."""
    stmt = (
        select(UnansweredQuery)
        .order_by(UnansweredQuery.count.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
