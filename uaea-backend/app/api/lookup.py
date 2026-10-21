"""Lookup API routes — /v1/lookup/*.

These endpoints use the SAME functions the LLM tools call internally —
no duplicate logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Department, FeeTariff, Deadline, Service, Campus
from app.schemas import (
    DepartmentOut, FeeTariffOut, DeadlineOut, ServiceOut,
)
from app.orchestrator.tools import (
    tool_get_department, tool_get_fee_tariff,
    tool_get_deadline, tool_get_document_checklist,
)

router = APIRouter(prefix="/v1/lookup", tags=["lookup"])


@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(
    region: str | None = Query(None),
    query: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List departments, optionally filtered by region or search query."""
    stmt = select(Department)

    if region:
        # Join with Campus and filter by region
        campus_stmt = select(Campus).where(Campus.region.ilike(f"%{region}%"))
        campus_result = await db.execute(campus_stmt)
        campus_ids = [c.id for c in campus_result.scalars().all()]
        if campus_ids:
            stmt = stmt.where(Department.region_id.in_(campus_ids))
        else:
            return []

    if query:
        stmt = stmt.where(
            Department.name_en.ilike(f"%{query}%")
            | Department.name_ur.ilike(f"%{query}%")
            | Department.category.ilike(f"%{query}%")
        )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/fee-tariff", response_model=list[FeeTariffOut])
async def list_fee_tariffs(
    program: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List fee tariffs, optionally filtered by program and category."""
    stmt = select(FeeTariff)

    if program:
        stmt = stmt.where(FeeTariff.program.ilike(f"%{program}%"))
    if category:
        stmt = stmt.where(FeeTariff.category.ilike(f"%{category}%"))

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/deadlines", response_model=list[DeadlineOut])
async def list_deadlines(
    service: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List deadlines, optionally filtered by service name."""
    if service:
        stmt = (
            select(Deadline)
            .join(Service, Deadline.service_id == Service.id)
            .where(Service.name_en.ilike(f"%{service}%"))
        )
    else:
        stmt = select(Deadline)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/document-checklist")
async def get_checklist(
    service: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get the document checklist for a service.

    Uses the same function as the LLM tool call.
    """
    result = await tool_get_document_checklist(db, service)
    return result


# ── Expanded public catalogue (same functions the chatbot's tools use) ────────

from app.orchestrator import tools as T  # noqa: E402


@router.get("/campuses")
async def lookup_campuses(db: AsyncSession = Depends(get_db)):
    return await T.tool_list_campuses(db)


@router.get("/programs")
async def lookup_programs(level: str | None = Query(None), campus: str | None = Query(None),
                          db: AsyncSession = Depends(get_db)):
    return await T.tool_list_programs(db, level, campus)


@router.get("/programs/{program}")
async def lookup_program(program: str, db: AsyncSession = Depends(get_db)):
    return await T.tool_get_program_info(db, program)


@router.get("/calendar")
async def lookup_calendar(program: str | None = Query(None), term: str | None = Query(None),
                          event: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_academic_calendar(db, program, term, event)


@router.get("/timetable")
async def lookup_timetable(program: str = Query(...), semester_no: int | None = Query(None),
                           day: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_class_timetable(db, program, semester_no, day)


@router.get("/courses")
async def lookup_courses(program: str | None = Query(None), semester_no: int | None = Query(None),
                         query: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_courses(db, program, semester_no, query)


@router.get("/faculty")
async def lookup_faculty(query: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_faculty(db, query)


@router.get("/scholarships")
async def lookup_scholarships(query: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_scholarships(db, query)


@router.get("/hostels")
async def lookup_hostels(campus: str | None = Query(None), gender: str | None = Query(None),
                         db: AsyncSession = Depends(get_db)):
    return await T.tool_get_hostel_info(db, campus, gender)


@router.get("/transport")
async def lookup_transport(area: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    return await T.tool_get_transport_routes(db, area)
