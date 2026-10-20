"""Chat API routes — /v1/chat/*."""

# NOTE: no `from __future__ import annotations` here — the slowapi @limiter.limit
# decorator re-wraps the endpoint, hiding this module's globals from FastAPI's
# string-annotation resolution, which breaks request-model parsing.

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Conversation, Message, EscalationTicket
from app.schemas import (
    ChatMessageRequest, ChatMessageResponse, ToolCallOut,
    EscalateRequest, EscalateResponse, SessionOut,
)
from app.orchestrator.orchestrator import handle_message
from app.config import settings

router = APIRouter(prefix="/v1/chat", tags=["chat"])

# Per-IP rate limiter (shared with app via app.state.limiter)
limiter = Limiter(key_func=get_remote_address)


@router.post("/message", response_model=ChatMessageResponse)
@limiter.limit(settings.rate_limit_per_ip)
async def post_message(request: Request, req: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    """Send a chat message and get the assistant's reply."""
    result = await handle_message(
        db=db,
        session_id=req.session_id,
        channel=req.channel,
        text=req.text,
    )

    return ChatMessageResponse(
        reply=result["reply"],
        intent=result.get("intent"),
        tool_calls=[ToolCallOut(**tc) for tc in result.get("tool_calls", [])],
        escalated=result.get("escalated", False),
        confidence=result.get("confidence", 0.0),
        language=result.get("language", "en"),
        sources=result.get("sources", []),
        intent_label=result.get("intent_label"),
        otp=result.get("otp"),
        verified_roll=result.get("verified_roll"),
        engine=result.get("engine"),
        model=result.get("model"),
        resolved=result.get("resolved", True),
    )


@router.get("/session/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get full conversation history for a session."""
    stmt = (
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch messages
    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
    )
    msg_result = await db.execute(msg_stmt)
    messages = msg_result.scalars().all()

    return SessionOut(
        id=conv.id,
        session_id=conv.session_id,
        channel=conv.channel,
        started_at=conv.started_at,
        resolved=conv.resolved,
        escalated=conv.escalated,
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "text": m.text,
                "intent": m.intent,
                "tool_calls": m.tool_calls or [],
                "feedback": m.feedback,
                "created_at": str(m.created_at),
            }
            for m in messages
        ],
    )


@router.post("/escalate", response_model=EscalateResponse)
async def escalate(req: EscalateRequest, db: AsyncSession = Depends(get_db)):
    """Create an escalation ticket for a conversation."""
    # Find the conversation
    stmt = (
        select(Conversation)
        .where(Conversation.session_id == req.session_id, Conversation.resolved.is_(False))
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=404, detail="No active conversation for this session")

    ticket = EscalationTicket(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        reason=req.reason,
        status="open",
    )
    db.add(ticket)
    conv.escalated = True
    await db.commit()

    return EscalateResponse(ticket_id=ticket.id, status="open")
