"""Orchestrator — ties normalizer → intent → state → LLM tools → guardrails.

This is the main pipeline for every incoming chat message.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from openai import AsyncOpenAI, APIError as OpenAIAPIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Conversation, Message, UnansweredQuery
from app.orchestrator.normalizer import normalise, detect_language, strip_injection
from app.orchestrator.intent_router import classify, GUIDED_FLOW_INTENTS
from app.orchestrator.state_machine import (
    FlowState, FLOW_DEFINITIONS, next_step, fill_slot,
)
from app.orchestrator.tools import TOOL_DEFINITIONS, execute_tool
from app.orchestrator.guardrails import check_reply

logger = logging.getLogger("orchestrator")

SYSTEM_PROMPT = """You are UAEA Assistant — a helpful university student-services chatbot.

CRITICAL RULES:
1. NEVER state a fee amount, deadline date, or document requirement unless you have obtained it from a tool call in THIS conversation turn.
2. If a tool returns no data or an error, say so honestly and offer to escalate to a human.
3. Do NOT guess, fabricate, or rely on your training data for university-specific facts.
4. Reply in the same language the student uses (English, Urdu, or Roman Urdu).
5. Be concise, friendly, and professional.
6. When presenting fee amounts, always include the currency (PKR) and the source document.
7. When presenting deadlines, always include the source document reference.
8. When listing document checklists, present each item clearly with whether a copy is needed.
"""

# Maximum LLM rounds (tool-call loops) per message
MAX_ROUNDS = 6


async def handle_message(
    db: AsyncSession,
    session_id: str,
    channel: str,
    text: str,
) -> dict[str, Any]:
    """Process one user message end-to-end.

    Returns a dict matching ChatMessageResponse schema.
    """
    # 1. Sanitize input
    cleaned_text = strip_injection(text)
    language = detect_language(cleaned_text)
    normalized = normalise(cleaned_text)

    # 2. Classify intent
    intent_result = classify(cleaned_text)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]

    # 3. Get or create conversation
    conversation = await _get_or_create_conversation(db, session_id, channel)

    # 4. Persist user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        text=cleaned_text,
        intent=intent,
    )
    db.add(user_msg)
    await db.flush()

    # 5. Check guided flow state
    history = await _get_message_history(db, conversation.id)
    flow_state = FlowState.from_messages(history)

    # Start a new guided flow if applicable
    if intent in GUIDED_FLOW_INTENTS and not flow_state.active:
        flow_state = FlowState(intent=intent, active=True, filled_slots={}, completed=False)

    # 6. Handle guided flow slot-filling
    guided_reply = await _handle_guided_flow(db, flow_state, cleaned_text, conversation.id)
    if guided_reply:
        return guided_reply

    # 7. Call LLM with tools
    llm_reply, tool_calls, escalated = await _run_llm_with_tools(
        db, cleaned_text, history, conversation.id, language,
    )

    # 8. Run guardrails
    guardrail_result = check_reply(llm_reply, tool_calls)

    # 9. Persist assistant message
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        text=guardrail_result.cleaned_reply,
        intent=intent,
        tool_calls=[{"name": tc["name"], "args": tc.get("args"), "result": tc.get("result")} for tc in tool_calls],
    )
    db.add(assistant_msg)

    # Track flow state in message for persistence
    if flow_state.active:
        flow_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="tool",
            text="flow_state",
            tool_calls=[{"name": "flow_state", "result": flow_state.to_dict()}],
        )
        db.add(flow_msg)

    # Handle low-confidence / unanswered
    if confidence < 0.4 and intent not in GUIDED_FLOW_INTENTS:
        await _track_unanswered(db, cleaned_text, intent, confidence)

    if escalated:
        conversation.escalated = True

    await db.commit()

    # Collect sources from tool calls
    sources = _extract_sources(tool_calls)

    return {
        "reply": guardrail_result.cleaned_reply,
        "intent": intent,
        "tool_calls": [{"name": tc["name"], "args": tc.get("args"), "result": tc.get("result")} for tc in tool_calls],
        "escalated": escalated,
        "confidence": confidence,
        "language": language,
        "sources": sources,
    }


async def _handle_guided_flow(
    db: AsyncSession,
    flow_state: FlowState,
    text: str,
    conversation_id: str,
) -> dict[str, Any] | None:
    """Handle guided flow slot-filling and step execution.

    Returns a response dict if the flow produced a reply, None if we should
    fall through to the LLM.
    """
    if not flow_state.active or not flow_state.intent:
        return None

    flow_def = FLOW_DEFINITIONS.get(flow_state.intent)
    if not flow_def:
        return None

    # If there are unfilled slots, try to fill them
    step = next_step(flow_state)
    if step is None:
        # Flow is complete — let LLM produce the final summary with tool results
        return None

    if "slot" in step:
        # If this is the first message (just triggered the flow), prompt for the slot
        if not flow_state.filled_slots:
            reply_text = f"**{flow_def['name']}** — I'll help you with that.\n\n{step['prompt']}"
            # Persist flow state
            flow_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                text=reply_text,
                intent=flow_state.intent,
                tool_calls=[{"name": "flow_state", "result": flow_state.to_dict()}],
            )
            db.add(flow_msg)
            await db.commit()
            return {
                "reply": reply_text,
                "intent": flow_state.intent,
                "tool_calls": [],
                "escalated": False,
                "confidence": 0.9,
                "language": "en",
                "sources": [],
            }

        # Fill the slot from user text
        slot_name = fill_slot(flow_state, text)
        if slot_name:
            next_s = next_step(flow_state)
            if next_s and "slot" in next_s:
                reply_text = f"Got it — **{slot_name}**: {text.strip()}.\n\n{next_s['prompt']}"
            else:
                reply_text = f"Got it — **{slot_name}**: {text.strip()}.\n\nLet me fetch the details for you…"
                # Execute all action steps to gather data, then fall through to LLM
                return None

            flow_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                text=reply_text,
                intent=flow_state.intent,
                tool_calls=[{"name": "flow_state", "result": flow_state.to_dict()}],
            )
            db.add(flow_msg)
            await db.commit()
            return {
                "reply": reply_text,
                "intent": flow_state.intent,
                "tool_calls": [],
                "escalated": False,
                "confidence": 0.9,
                "language": "en",
                "sources": [],
            }

    return None


async def _run_llm_with_tools(
    db: AsyncSession,
    text: str,
    history: list[dict],
    conversation_id: str,
    language: str,
) -> tuple[str, list[dict], bool]:
    """Call the LLM (Grok/xAI) with tool definitions, execute tool calls in a loop.

    Uses the OpenAI-compatible API via xAI's endpoint.
    Returns (reply_text, tool_calls_list, escalated_bool).
    """
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )

    # Build message history for the LLM (last 20 messages max)
    system_msg = {
        "role": "system",
        "content": SYSTEM_PROMPT + f"\n\nThe student is communicating in {language}. Reply in the same language.",
    }
    messages: list[dict] = [system_msg]
    for msg in history[-20:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["text"] or ""})

    # Add the current user message
    if not messages[-1:][0:1] or messages[-1]["role"] != "user" or messages[-1]["content"] != text:
        messages.append({"role": "user", "content": text})

    all_tool_calls: list[dict] = []
    escalated = False
    reply_text = ""

    for round_num in range(MAX_ROUNDS):
        try:
            response = await client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=1024,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except OpenAIAPIError as e:
            logger.error(f"LLM API error: {e}")
            return (
                "I'm having trouble connecting right now. Please try again in a moment, "
                "or I can connect you to a staff member.",
                all_tool_calls,
                False,
            )

        choice = response.choices[0]
        assistant_msg = choice.message

        # If no tool calls, this is the final reply
        if not assistant_msg.tool_calls:
            reply_text = assistant_msg.content or ""
            return reply_text, all_tool_calls, escalated

        # Append the assistant's message (with tool_calls) to history
        messages.append(assistant_msg.model_dump())

        # Execute each tool call
        for tool_call in assistant_msg.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            logger.info(f"Tool call: {tool_name}({tool_args})")

            result = await execute_tool(db, tool_name, tool_args, conversation_id)
            all_tool_calls.append({"name": tool_name, "args": tool_args, "result": result})

            if tool_name == "create_escalation_ticket":
                escalated = True

            # Append tool result as a tool-role message
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=str, ensure_ascii=False),
            })

    # If we exhausted rounds, return what we have
    if not reply_text:
        reply_text = "I'm working on your request but it's taking longer than expected. Let me connect you to a staff member."
        escalated = True

    return reply_text, all_tool_calls, escalated


async def _get_or_create_conversation(db: AsyncSession, session_id: str, channel: str) -> Conversation:
    """Get the latest open conversation for this session, or create one."""
    stmt = (
        select(Conversation)
        .where(Conversation.session_id == session_id, Conversation.resolved.is_(False))
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()

    if conv is None:
        conv = Conversation(
            id=str(uuid.uuid4()),
            session_id=session_id,
            channel=channel,
        )
        db.add(conv)
        await db.flush()

    return conv


async def _get_message_history(db: AsyncSession, conversation_id: str) -> list[dict]:
    """Fetch message history for a conversation."""
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "text": m.text,
            "intent": m.intent,
            "tool_calls": m.tool_calls or [],
            "created_at": str(m.created_at),
        }
        for m in messages
    ]


async def _track_unanswered(db: AsyncSession, text: str, intent: str | None, confidence: float):
    """Log low-confidence queries to the unanswered queue."""
    # Check if a similar query already exists
    stmt = select(UnansweredQuery).where(UnansweredQuery.text == text)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.count += 1
    else:
        db.add(UnansweredQuery(
            id=str(uuid.uuid4()),
            text=text,
            intent=intent,
            confidence=confidence,
            reason="Low classifier confidence",
        ))


def _extract_sources(tool_calls: list[dict]) -> list[dict[str, Any]]:
    """Pull source references from tool call results for citation display."""
    sources: list[dict[str, Any]] = []
    for tc in tool_calls:
        result = tc.get("result", {})
        if isinstance(result, dict):
            if "source" in result:
                sources.append({"tool": tc["name"], "source": result["source"]})
            if "source_doc_id" in result:
                sources.append({"tool": tc["name"], "source": result["source_doc_id"]})
            # RAG chunks have their own sources
            if "chunks" in result:
                for chunk in result["chunks"]:
                    sources.append({
                        "tool": tc["name"],
                        "source": chunk.get("source_doc_id", ""),
                        "section": chunk.get("section", ""),
                    })
    return sources
