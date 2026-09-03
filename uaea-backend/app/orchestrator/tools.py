"""Tool definitions + implementations for the LLM orchestrator.

Each tool is a real function backed by the DB or adapter.
The LLM registers these via the OpenAI-compatible tool-calling API (Grok/xAI).
"""

from __future__ import annotations
import json
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Department, FeeTariff, Deadline, Service, EscalationTicket

# ── OpenAI-compatible tool schemas (for Grok / xAI) ──────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the university knowledge base for relevant information from official documents. Returns cited chunks from verified sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query in any language"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_department",
            "description": "Look up a university department or campus by name or region. Returns contact details and office hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_or_region": {"type": "string", "description": "Department name, campus name, or region to search for"},
                },
                "required": ["name_or_region"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fee_tariff",
            "description": "Look up the official fee for a programme. NEVER quote fees from memory — always use this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {"type": "string", "description": "Programme name, e.g. 'BS Computer Science'"},
                    "category": {"type": "string", "description": "Fee category, e.g. 'Semester (new)' or 'Urgent service'"},
                },
                "required": ["program"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_deadline",
            "description": "Look up the official deadline for a service. NEVER quote dates from memory — always use this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name, e.g. 'Admission & Enrolment'"},
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_checklist",
            "description": "Look up the required documents for a university service. NEVER list documents from memory — always use this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name, e.g. 'Degree Application'"},
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_escalation_ticket",
            "description": "Create a human handoff ticket when the assistant cannot resolve a query. Use when data is missing or the student requests a human.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "description": "The conversation ID"},
                    "reason": {"type": "string", "description": "Why the ticket is being created"},
                },
                "required": ["conversation_id", "reason"],
            },
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

async def tool_get_department(db: AsyncSession, name_or_region: str) -> dict[str, Any]:
    query = name_or_region.lower()
    stmt = select(Department)
    result = await db.execute(stmt)
    departments = result.scalars().all()

    for dept in departments:
        if (query in (dept.name_en or "").lower()
                or query in (dept.name_ur or "")
                or (dept.region and query in (dept.region.name or "").lower())
                or (dept.region and query in (dept.region.region or "").lower())):
            contact_info = {}
            if dept.contact:
                contact_info = {
                    "phone": dept.contact.phone,
                    "email": dept.contact.email,
                    "office_hours": dept.contact.office_hours,
                }
            campus_info = {}
            if dept.region:
                campus_info = {"campus": dept.region.name, "address": dept.region.address}

            return {
                "name_en": dept.name_en,
                "name_ur": dept.name_ur,
                "category": dept.category,
                **campus_info,
                **contact_info,
            }

    return {"error": f"No department found matching '{name_or_region}'"}


async def tool_get_fee_tariff(db: AsyncSession, program: str, category: str | None = None) -> dict[str, Any]:
    stmt = select(FeeTariff)
    result = await db.execute(stmt)
    fees = result.scalars().all()

    # Fuzzy match on program name
    matches = [f for f in fees if program.lower() in f.program.lower()]
    if not matches:
        # Try matching by keywords
        matches = [f for f in fees if any(w in f.program.lower() for w in program.lower().split() if len(w) > 2)]

    if category:
        cat_matches = [f for f in matches if category.lower() in f.category.lower()]
        if cat_matches:
            matches = cat_matches

    if not matches:
        return {"error": f"No fee found for program '{program}'"}

    fee = matches[0]
    return {
        "program": fee.program,
        "category": fee.category,
        "amount": fee.amount,
        "currency": "PKR",
        "effective_from": str(fee.effective_from),
        "source": fee.source_doc_ref,
    }


async def tool_get_deadline(db: AsyncSession, service: str) -> dict[str, Any]:
    stmt = select(Deadline).join(Service, Deadline.service_id == Service.id)
    result = await db.execute(stmt)
    deadlines = result.scalars().all()

    for dl in deadlines:
        if dl.service and service.lower() in dl.service.name_en.lower():
            return {
                "service": dl.service.name_en,
                "semester": dl.semester,
                "date": str(dl.date),
                "source": dl.source_doc_ref,
            }

    # Fallback: match by service name directly
    for dl in deadlines:
        if service.lower() in (dl.service_id or "").lower():
            return {
                "semester": dl.semester,
                "date": str(dl.date),
                "source": dl.source_doc_ref,
            }

    return {"error": f"No deadline found for service '{service}'"}


async def tool_get_document_checklist(db: AsyncSession, service: str) -> dict[str, Any]:
    stmt = select(Service)
    result = await db.execute(stmt)
    services = result.scalars().all()

    for svc in services:
        if service.lower() in svc.name_en.lower():
            items = svc.document_checklist or []
            return {
                "service": svc.name_en,
                "checklist": items,
                "procedure": svc.procedure_text,
                "source": svc.source_doc_ref,
                "last_verified": str(svc.last_verified_at) if svc.last_verified_at else None,
            }

    return {"error": f"No checklist found for service '{service}'"}


async def tool_create_escalation(db: AsyncSession, conversation_id: str, reason: str) -> dict[str, Any]:
    import uuid
    ticket = EscalationTicket(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        reason=reason,
        status="open",
    )
    db.add(ticket)
    await db.commit()

    return {
        "ticket_id": ticket.id,
        "status": "open",
        "message": "Your request has been escalated to a staff member. They will reach out shortly.",
    }


async def execute_tool(db: AsyncSession, tool_name: str, args: dict, conversation_id: str = "") -> dict[str, Any]:
    """Dispatch a tool call to the right implementation."""
    if tool_name == "get_department":
        return await tool_get_department(db, args.get("name_or_region", ""))
    elif tool_name == "get_fee_tariff":
        return await tool_get_fee_tariff(db, args.get("program", ""), args.get("category"))
    elif tool_name == "get_deadline":
        return await tool_get_deadline(db, args.get("service", ""))
    elif tool_name == "get_document_checklist":
        return await tool_get_document_checklist(db, args.get("service", ""))
    elif tool_name == "create_escalation_ticket":
        return await tool_create_escalation(db, args.get("conversation_id", conversation_id), args.get("reason", ""))
    elif tool_name == "search_knowledge_base":
        from app.rag.retrieve import search_knowledge_base
        return await search_knowledge_base(db, args.get("query", ""))
    else:
        return {"error": f"Unknown tool: {tool_name}"}
