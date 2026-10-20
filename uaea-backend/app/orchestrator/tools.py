"""Tool definitions + implementations for the LLM orchestrator.

Every fact the assistant states comes from one of these functions, which read
the real database. Two kinds of tools:

* PUBLIC  — prospectus-type information anyone may ask for (fees, calendar,
  timetable, faculty, hostels, …).
* PRIVATE — a specific student's records (result, fee status, attendance,
  profile). These never return data until the chat session has verified the
  roll number with a WhatsApp OTP. Before that they return ``otp_required``
  and trigger the code. The check is enforced here, in code — not by the LLM.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Department, FeeTariff, Deadline, Service, EscalationTicket, Campus, Program,
    AcademicEvent, Faculty, Course, ClassSchedule, Scholarship, Hostel, TransportRoute,
    Student, ResultRecord, FeeRecord, AttendanceRecord,
)
from app.orchestrator import entities
from app.orchestrator.clock import today, days_until
from app.orchestrator.normalizer import normalise
from app.services import otp as otp_service


@dataclass
class ToolContext:
    session_id: str = ""
    conversation_id: str = ""
    question: str = ""


PRIVATE_TOOLS = {"get_student_result", "get_fee_status", "get_attendance", "get_student_profile"}

# ── OpenAI-compatible tool schemas (Groq) ─────────────────────────────────────

def _fn(name: str, description: str, props: dict | None = None, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": props or {}, "required": required or []},
        },
    }


_S = {"type": "string"}
_I = {"type": "integer"}

TOOL_DEFINITIONS = [
    _fn("search_knowledge_base",
        "Search official university documents (rules, policies, FAQs): attendance rule, grading, GPA, probation, "
        "refund policy, installments, plagiarism, library, LMS/portal, email/Wi-Fi, medical, internships, convocation, "
        "merit formula, quotas, entry test, re-admission, hostel timings, etc.",
        {"query": {**_S, "description": "Search query in English keywords (translate Urdu/Roman Urdu first)"}}, ["query"]),
    _fn("get_department",
        "Find a university office, academic department or regional campus office: phone, email, office hours, address.",
        {"name_or_region": {**_S, "description": "e.g. 'Examinations', 'Finance', 'Computer Science', 'Lahore'"}}, ["name_or_region"]),
    _fn("list_campuses", "List all campuses with address and phone."),
    _fn("list_programs",
        "List programmes offered, optionally filtered by level or campus.",
        {"level": {**_S, "description": "Undergraduate | Graduate | Postgraduate"},
         "campus": {**_S, "description": "City name, e.g. 'Lahore'"}}),
    _fn("get_program_info",
        "Details of one programme: eligibility, duration, credit hours, seats, shift, entry test, campuses, fee.",
        {"program": {**_S, "description": "Programme name or code, e.g. 'BSCS', 'BS Computer Science', 'MBA'"}}, ["program"]),
    _fn("get_fee_tariff",
        "Official fee for a programme (semester fee, repeat per credit hour) or a service (transcript, degree, "
        "rechecking, migration, NOC, hostel security, transport pass, late fine…). NEVER quote fees from memory.",
        {"program": {**_S, "description": "Programme or service name, e.g. 'BS Computer Science' or 'Transcript'"},
         "category": {**_S, "description": "Optional: 'Semester (new)', 'repeat', 'Urgent service'…"}}, ["program"]),
    _fn("get_deadline",
        "Official last dates for a service: admission, fee challan, degree, rechecking, scholarship, hostel, "
        "semester freeze, add/drop, transport pass. NEVER quote dates from memory.",
        {"service": {**_S, "description": "e.g. 'Admission', 'Fee Challan', 'Scholarship', 'Hostel'"}}, ["service"]),
    _fn("get_academic_calendar",
        "Academic calendar: when classes begin (per programme for new students), orientation, mid-terms, finals, "
        "result declaration, holidays, winter/summer break, convocation.",
        {"program": {**_S, "description": "Optional programme, e.g. 'BSCS'"},
         "term": {**_S, "description": "Optional term, e.g. 'Fall 2026', 'Spring 2027'"},
         "event": {**_S, "description": "Optional keyword: 'classes begin', 'mid-term', 'final', 'orientation', 'holiday', 'result'"}}),
    _fn("get_class_timetable",
        "Weekly class timetable (current term) for a programme and semester number: day, time, course, room, teacher.",
        {"program": _S, "semester_no": {**_I, "description": "1-8"}, "day": {**_S, "description": "Optional weekday"}},
        ["program"]),
    _fn("get_courses",
        "Scheme of studies: courses of a programme (optionally one semester), or look up a course by code/title.",
        {"program": _S, "semester_no": _I, "query": {**_S, "description": "Course code or title keyword"}}),
    _fn("get_faculty",
        "Faculty directory: teachers by name, department or subject — designation, email, office, office hours.",
        {"query": {**_S, "description": "Teacher name, department or subject"}}, ["query"]),
    _fn("get_document_checklist",
        "Required documents + procedure + fee for a service (admission, fee challan, degree, transcript, rechecking, "
        "migration, NOC, record correction, bonafide, hostel, scholarship, freeze, add/drop, ID card, transport, library).",
        {"service": _S}, ["service"]),
    _fn("get_scholarships", "Scholarships, financial aid and fee concessions with eligibility and deadlines.",
        {"query": {**_S, "description": "Optional keyword: 'need', 'merit', 'hafiz', 'sports', 'ehsaas'…"}}),
    _fn("get_hostel_info", "Hostels: fee, mess charges, vacant seats, facilities, warden contact.",
        {"campus": _S, "gender": {**_S, "description": "Male | Female"}}),
    _fn("get_transport_routes", "University bus routes, stops, timings and transport fee.",
        {"area": {**_S, "description": "Optional area / stop / campus, e.g. 'Bahria', 'Rawalpindi', 'Lahore'"}}),
    _fn("create_escalation_ticket",
        "Hand the conversation to a human staff member when data is missing or the student asks for a person.",
        {"reason": _S}, ["reason"]),
    # ── private ──
    _fn("get_student_result",
        "PRIVATE. Exam result (GPA, CGPA, grades) of a student by roll number. Requires WhatsApp OTP verification — "
        "if not verified the tool sends the code and returns otp_required. Roll number format like BSCS-2023-014.",
        {"roll_number": _S, "semester_no": {**_I, "description": "Optional; omit for latest result"},
         "term": {**_S, "description": "Optional, e.g. 'Spring 2026'"}}, ["roll_number"]),
    _fn("get_fee_status",
        "PRIVATE. Fee payment status / dues / challan of a student by roll number. Requires WhatsApp OTP.",
        {"roll_number": _S}, ["roll_number"]),
    _fn("get_attendance",
        "PRIVATE. Current-semester attendance of a student by roll number. Requires WhatsApp OTP.",
        {"roll_number": _S}, ["roll_number"]),
    _fn("get_student_profile",
        "PRIVATE. Enrolment details (name, programme, semester, campus, CGPA, status, advisor, hostel). Requires WhatsApp OTP.",
        {"roll_number": _S}, ["roll_number"]),
]

# ── helpers ───────────────────────────────────────────────────────────────────

_STOP = set("""a an the is are was of for to in on at and or what when where which who how much many
kya kab kahan kis kaun kitni kitna kitne hai hain ho hoga hogi hongi ka ki ke ko se sy me mein main mujhe mera meri
please plz bata batao batayen tell me about give get want need chahiye info information""".split())


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9؀-ۿ]+", normalise(s or "")) if w not in _STOP and len(w) > 1}


def _score(query: str, *fields: str | None) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    hay = " ".join(f or "" for f in fields)
    h = _tokens(hay)

    def match(t: str) -> bool:
        if t in h:
            return True
        st = t[:-1] if t.endswith("s") and len(t) > 4 else t
        return len(st) >= 4 and any(x.startswith(st) or (len(x) >= 4 and st.startswith(x)) for x in h)

    hits = sum(1 for t in q if match(t))
    phrase = 2.0 if normalise(query) and normalise(query) in normalise(hay) else 0.0
    return hits / len(q) * 3 + phrase


def _date(d) -> str | None:
    return str(d) if d else None


async def _all(db: AsyncSession, model):
    return (await db.execute(select(model))).unique().scalars().all()


async def _resolve_program(db: AsyncSession, value: str | None) -> Program | None:
    if not value:
        return None
    programs = await _all(db, Program)
    by_code = {p.code: p for p in programs}
    v = value.strip()
    if v.upper() in by_code:
        return by_code[v.upper()]
    code = entities.find_program(v)
    if code and code in by_code:
        return by_code[code]
    best = max(programs, key=lambda p: _score(v, p.name, p.code, " ".join(p.aliases or [])), default=None)
    if best and _score(v, best.name, best.code, " ".join(best.aliases or [])) >= 1.5:
        return best
    return None


def _contact(c) -> dict:
    return {"phone": c.phone, "email": c.email, "office_hours": c.office_hours} if c else {}


# ── public tools ──────────────────────────────────────────────────────────────

async def tool_get_department(db: AsyncSession, name_or_region: str) -> dict[str, Any]:
    query = (name_or_region or "").strip()
    departments = await _all(db, Department)
    q = query.lower()

    def info(dept: Department) -> dict:
        out = {"name_en": dept.name_en, "name_ur": dept.name_ur, "category": dept.category}
        if dept.region:
            out.update(campus=dept.region.name, address=dept.region.address)
        out.update(_contact(dept.contact))
        return out

    scored = []
    for dept in departments:
        s = _score(query, dept.name_en, dept.category, dept.region.name if dept.region else "",
                   dept.region.region if dept.region else "")
        if q and (q in (dept.name_en or "").lower() or q in (dept.name_ur or "")):
            s += 3
        if dept.region and q and (q in (dept.region.name or "").lower() or q == (dept.region.region or "").lower()):
            s += 2.5
        if s > 0:
            scored.append((s, dept))
    if not scored:
        return {"error": f"No department found matching '{name_or_region}'"}
    scored.sort(key=lambda x: (-x[0], x[1].id))
    top = info(scored[0][1])
    others = [info(d)["name_en"] for s, d in scored[1:5] if s >= scored[0][0] * 0.6]
    if others:
        top["other_matches"] = others
    top["source"] = "University Directory 2026"
    return top


async def tool_list_campuses(db: AsyncSession) -> dict[str, Any]:
    rows = await _all(db, Campus)
    return {"campuses": [{"name": c.name, "region": c.region, "address": c.address, **_contact(c.contact)} for c in rows],
            "source": "University Directory 2026"}


async def tool_list_programs(db: AsyncSession, level: str | None = None, campus: str | None = None) -> dict[str, Any]:
    programs = await _all(db, Program)
    camp_id = entities.find_campus(campus or "") if campus else None
    out = []
    fees = {(f.program, f.category): f.amount for f in await _all(db, FeeTariff)}
    for p in programs:
        if level and level.lower()[:5] not in p.level.lower():
            continue
        if camp_id and camp_id not in (p.campuses or []):
            continue
        out.append({"code": p.code, "name": p.name, "level": p.level, "duration_years": p.duration_years,
                    "shift": p.shift, "semester_fee_pkr": fees.get((p.name, "Semester (new)"))})
    return {"programs": out, "count": len(out), "source": "Prospectus 2026-27 §5"}


async def tool_get_program_info(db: AsyncSession, program: str) -> dict[str, Any]:
    p = await _resolve_program(db, program)
    if not p:
        return {"error": f"No programme found matching '{program}'",
                "available": [x.name for x in await _all(db, Program)]}
    campuses = {c.id: c.name for c in await _all(db, Campus)}
    fee_rows = [f for f in await _all(db, FeeTariff) if f.program == p.name]
    cls = (await db.execute(select(AcademicEvent).where(AcademicEvent.program_code == p.code))).scalars().first()
    return {
        "code": p.code, "name": p.name, "name_ur": p.name_ur, "level": p.level, "faculty": p.faculty,
        "department": p.department.name_en if p.department else None,
        "duration_years": p.duration_years, "semesters": p.semesters, "credit_hours": p.credit_hours,
        "seats": p.seats, "shift": p.shift, "eligibility": p.eligibility, "min_percentage": p.min_percentage,
        "entry_test": p.entry_test, "offered_at": [campuses.get(c, c) for c in (p.campuses or [])],
        "fees": [{"category": f.category, "amount": f.amount, "currency": "PKR"} for f in fee_rows],
        "first_semester_classes_begin": _date(cls.start_date) if cls else None,
        "source": p.source_doc_ref,
    }


_SERVICE_FEE_WORDS = {
    "transcript": "Transcript", "prc": "Transcript", "degree": "Degree", "recheck": "Rechecking",
    "migration": "Migration Certificate", "noc": "NOC", "correction": "Record Correction",
    "bonafide": "Bonafide / Character Certificate", "character": "Bonafide / Character Certificate",
    "id card": "Student ID Card", "card": "Student ID Card", "freeze": "Semester Freeze",
    "late": "Late Fee Fine", "fine": "Late Fee Fine", "exam": "Examination Fee", "library": "Library Card",
    "transport": "Transport Pass", "bus": "Transport Pass", "hostel": "Hostel", "admission fee": "Admission Processing Fee",
    "processing": "Admission Processing Fee", "verification": "Degree Verification (HEC attestation support)",
}


async def tool_get_fee_tariff(db: AsyncSession, program: str, category: str | None = None) -> dict[str, Any]:
    fees = await _all(db, FeeTariff)
    program = program or ""
    matches: list[FeeTariff] = []

    prog = await _resolve_program(db, program)
    if prog:
        matches = [f for f in fees if f.program == prog.name]
    if not matches:
        matches = [f for f in fees if program.lower() in f.program.lower()] if program else []
    if not matches:
        low = normalise(program)
        for word, name in _SERVICE_FEE_WORDS.items():
            if word in low:
                matches = [f for f in fees if f.program == name]
                break
    if not matches:
        words = [w for w in program.lower().split() if len(w) > 2]
        matches = [f for f in fees if any(w in f.program.lower() for w in words)]
    if not matches:
        return {"error": f"No fee found for program '{program}'"}

    if not category:
        low_p = normalise(program)
        for hint in ("urgent", "repeat", "evening", "duplicate", "per paper"):
            if hint in low_p:
                category = hint
                break
    if category:
        c = category.lower()
        cat_matches = [f for f in matches if c in f.category.lower()
                       or (("repeat" in c or "credit" in c) and "repeat" in f.category.lower())
                       or ("urgent" in c and "urgent" in f.category.lower())]
        if cat_matches:
            matches = cat_matches
    matches.sort(key=lambda f: (0 if f.category == "Semester (new)" else 1, f.category))
    fee = matches[0]
    out = {
        "program": fee.program, "category": fee.category, "amount": fee.amount, "currency": "PKR",
        "effective_from": str(fee.effective_from), "source": fee.source_doc_ref,
    }
    if len(matches) > 1:
        out["all_categories"] = [{"category": f.category, "amount": f.amount, "source": f.source_doc_ref} for f in matches]
    if prog:
        out["note"] = "Examination fee (Rs 3,000/semester) is charged with the semester fee; new students also pay a one-time Rs 2,500 admission processing fee."
    return out


_SERVICE_ALIASES = {
    "admission": "svc-01", "enrol": "svc-01", "dakhla": "svc-01", "داخل": "svc-01",
    "challan": "svc-02", "fee": "svc-02", "result": "svc-03", "degree": "svc-04", "ڈگری": "svc-04",
    "transcript": "svc-05", "prc": "svc-05", "recheck": "svc-06", "migration": "svc-07", "noc": "svc-08",
    "no objection": "svc-08", "correction": "svc-09", "bonafide": "svc-10", "character": "svc-10",
    "hostel": "svc-11", "scholarship": "svc-12", "wazifa": "svc-12", "freeze": "svc-13", "add": "svc-14",
    "drop": "svc-14", "withdraw": "svc-14", "id card": "svc-15", "card": "svc-15", "transport": "svc-16",
    "bus": "svc-16", "library": "svc-17",
}


async def _resolve_service(db: AsyncSession, service: str) -> Service | None:
    services = await _all(db, Service)
    s = (service or "").strip().lower()
    if not s:
        return None
    for svc in services:
        if s in svc.name_en.lower() or s == svc.id:
            return svc
    n = normalise(service)
    for word, sid in _SERVICE_ALIASES.items():
        if word in n or word in service:
            return next((x for x in services if x.id == sid), None)
    best = max(services, key=lambda x: _score(service, x.name_en, x.description), default=None)
    if best and _score(service, best.name_en, best.description) >= 1.5:
        return best
    return None


async def tool_get_deadline(db: AsyncSession, service: str) -> dict[str, Any]:
    svc = await _resolve_service(db, service)
    if not svc:
        return {"error": f"No deadline found for service '{service}'"}
    rows = (await db.execute(select(Deadline).where(Deadline.service_id == svc.id))).unique().scalars().all()
    if not rows:
        return {"error": f"No deadline found for service '{service}'"}
    rows = sorted(rows, key=lambda d: d.date)
    t = today()
    upcoming = [d for d in rows if d.date >= t]
    primary = upcoming[0] if upcoming else rows[-1]
    return {
        "service": svc.name_en, "semester": primary.semester, "date": str(primary.date),
        "days_left": days_until(primary.date), "passed": primary.date < t,
        "source": primary.source_doc_ref, "today": str(t),
        "all_deadlines": [{"semester": d.semester, "date": str(d.date), "passed": d.date < t,
                           "source": d.source_doc_ref} for d in rows],
    }


async def tool_get_academic_calendar(db: AsyncSession, program: str | None = None, term: str | None = None,
                                     event: str | None = None) -> dict[str, Any]:
    rows = await _all(db, AcademicEvent)
    prog = await _resolve_program(db, program) if program else None
    term_n = entities.find_term(term or "") if term else None
    t = today()
    out = []
    for e in rows:
        if e.program_code and (not prog or e.program_code != prog.code):
            continue
        if term_n and e.term != term_n:
            continue
        if event:
            ev = normalise(event)
            keys = {"class": ["class", "begin", "start", "shuru"], "mid": ["mid"], "final": ["final"],
                    "orientation": ["orientation"], "holiday": ["holiday", "break", "vacation", "chutti", "eid"],
                    "result": ["result"], "admission": ["admission", "merit"], "convocation": ["convocation"],
                    "exam": ["exam", "mid", "final"], "add": ["add", "drop"]}
            wanted = [w for k, ws in keys.items() if any(x in ev for x in ws) for w in ws] or ev.split()
            if not any(w in e.event.lower() for w in wanted):
                continue
        out.append({"term": e.term, "event": e.event, "event_ur": e.event_ur, "program": e.program_code or "All programmes",
                    "start_date": _date(e.start_date), "end_date": _date(e.end_date),
                    "days_from_today": days_until(e.start_date), "notes": e.notes, "source": e.source_doc_ref})
    out.sort(key=lambda x: x["start_date"])
    if not out:
        return {"error": "No calendar entries matched", "today": str(t)}
    return {"today": str(t), "events": out[:25], "count": len(out), "source": "Academic Calendar 2026-27"}


async def tool_get_class_timetable(db: AsyncSession, program: str, semester_no: int | None = None,
                                   day: str | None = None) -> dict[str, Any]:
    prog = await _resolve_program(db, program)
    if not prog:
        return {"error": f"No programme found matching '{program}'"}
    rows = (await db.execute(select(ClassSchedule).where(ClassSchedule.program_code == prog.code))).scalars().all()
    offered = sorted({r.semester_no for r in rows})
    if semester_no is None:
        return {"program": prog.name, "needs": "semester_no", "semesters_with_timetable": offered,
                "message": "Ask which semester (timetables exist for these semesters this term)."}
    sel = [r for r in rows if r.semester_no == int(semester_no)]
    if day:
        sel = [r for r in sel if r.day.lower().startswith(day.lower()[:3])]
    if not sel:
        return {"error": f"No timetable for {prog.name} semester {semester_no} this term",
                "semesters_with_timetable": offered}
    order = {d: i for i, d in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])}
    sel.sort(key=lambda r: (order.get(r.day, 9), r.start_time))
    return {"program": prog.name, "semester_no": int(semester_no), "term": sel[0].term, "section": sel[0].section,
            "slots": [{"day": r.day, "time": f"{r.start_time}-{r.end_time}", "course": f"{r.course_code} {r.course_title}",
                       "room": r.room, "teacher": r.instructor_name} for r in sel],
            "source": "Timetable Fall 2026 (Main Campus, Section A)"}


async def tool_get_courses(db: AsyncSession, program: str | None = None, semester_no: int | None = None,
                           query: str | None = None) -> dict[str, Any]:
    courses = await _all(db, Course)
    prog = await _resolve_program(db, program) if program else None
    if prog:
        courses = [c for c in courses if c.program_code == prog.code]
    if semester_no:
        courses = [c for c in courses if c.semester_no == int(semester_no)]
    if query:
        qn = query.strip().upper()
        exact = [c for c in courses if c.code.upper() == qn]
        courses = exact or [c for c in courses if _score(query, c.title, c.code) >= 1.5]
    if not courses:
        return {"error": "No matching courses found"}
    courses.sort(key=lambda c: (c.program_code, c.semester_no, c.code))
    return {"program": prog.name if prog else None, "count": len(courses),
            "courses": [{"code": c.code, "title": c.title, "credit_hours": c.credit_hours, "program": c.program_code,
                         "semester": c.semester_no, "teacher": c.instructor.name if c.instructor else None,
                         "prerequisite": c.prerequisite} for c in courses[:60]],
            "source": "Scheme of Studies 2026"}


async def tool_get_faculty(db: AsyncSession, query: str) -> dict[str, Any]:
    rows = await _all(db, Faculty)
    prog_code = entities.find_program(query or "")
    scored = []
    for f in rows:
        s = _score(query, f.name, f.designation, f.specialization, f.department.name_en if f.department else "")
        if prog_code and prog_code in (f.program_codes or []):
            s += 1.5
        if "chair" in normalise(query) or "hod" in normalise(query) or "head" in normalise(query):
            if "Chair" in f.designation or "Dean" in f.designation:
                s += 1
        if s >= 1:
            scored.append((s, f))
    if not scored:
        return {"error": f"No faculty member matched '{query}'"}
    scored.sort(key=lambda x: -x[0])
    return {"faculty": [{"name": f.name, "designation": f.designation,
                         "department": f.department.name_en if f.department else None, "email": f.email,
                         "office": f.office, "office_hours": f.office_hours, "specialization": f.specialization,
                         "qualification": f.qualification} for _, f in scored[:6]],
            "source": "Faculty Directory 2026"}


async def tool_get_document_checklist(db: AsyncSession, service: str) -> dict[str, Any]:
    svc = await _resolve_service(db, service)
    if not svc:
        return {"error": f"No checklist found for service '{service}'"}
    out = {
        "service": svc.name_en, "service_ur": svc.name_ur, "checklist": svc.document_checklist or [],
        "procedure": svc.procedure_text, "source": svc.source_doc_ref,
        "last_verified": str(svc.last_verified_at) if svc.last_verified_at else None,
    }
    if svc.fee:
        out["fee"] = {"category": svc.fee.category, "amount": svc.fee.amount, "currency": "PKR"}
    return out


async def tool_get_scholarships(db: AsyncSession, query: str | None = None) -> dict[str, Any]:
    rows = await _all(db, Scholarship)
    if query:
        scored = [(_score(query, s.name, s.kind, s.eligibility, s.coverage), s) for s in rows]
        best = [s for sc, s in sorted(scored, key=lambda x: -x[0]) if sc >= 1]
        rows = best or rows
    return {"today": str(today()),
            "scholarships": [{"name": s.name, "type": s.kind, "coverage": s.coverage, "eligibility": s.eligibility,
                              "deadline": _date(s.deadline), "deadline_passed": bool(s.deadline and s.deadline < today()),
                              "how_to_apply": s.how_to_apply, "source": s.source_doc_ref} for s in rows],
            "source": "Financial Aid Policy 2026"}


async def tool_get_hostel_info(db: AsyncSession, campus: str | None = None, gender: str | None = None) -> dict[str, Any]:
    rows = await _all(db, Hostel)
    cid = entities.find_campus(campus or "") if campus else None
    g = None
    if gender:
        g = entities.find_gender(gender) or (gender.strip().capitalize() if gender.strip().lower() in ("male", "female") else None)
    if cid:
        rows = [h for h in rows if h.campus_id == cid] or rows
    if g:
        rows = [h for h in rows if h.gender == g] or rows
    return {"hostels": [{"name": h.name, "campus": h.campus.name if h.campus else None, "for": h.gender,
                         "rooms": h.room_type, "fee_per_semester": h.fee_per_semester,
                         "mess_fee_per_month": h.mess_fee_per_month, "vacant_seats": h.vacant_seats,
                         "facilities": h.facilities, "warden": h.warden_name, "warden_phone": h.warden_phone}
                        for h in rows],
            "security_deposit": 10000, "currency": "PKR", "source": "Hostel Rules 2026 §3"}


async def tool_get_transport_routes(db: AsyncSession, area: str | None = None) -> dict[str, Any]:
    rows = await _all(db, TransportRoute)
    if area:
        cid = entities.find_campus(area)
        a = normalise(area)
        words = {w for w in a.split() if len(w) >= 4 and w not in ("route", "routes", "point", "transport")}

        def near(stop: str) -> bool:
            st = normalise(stop)
            return st in a or any(w in st.split() or st.startswith(w) for w in words)

        hit = [r for r in rows if any(near(s) for s in (r.stops or [])) or near(r.name) or (cid and r.campus_id == cid)]
        rows = hit or rows
    return {"routes": [{"route": r.route_no, "name": r.name, "campus": r.campus.name if r.campus else None,
                        "stops": r.stops, "morning_departure": r.morning_departure,
                        "return_from_campus": r.evening_departure, "fee_per_semester": r.fee_per_semester,
                        "driver_contact": r.driver_contact} for r in rows],
            "currency": "PKR", "source": "Transport Notice T-26/01"}


async def tool_create_escalation(db: AsyncSession, conversation_id: str, reason: str) -> dict[str, Any]:
    ticket = EscalationTicket(id=str(uuid.uuid4()), conversation_id=conversation_id, reason=reason or "Student asked for help", status="open")
    db.add(ticket)
    await db.flush()
    return {"ticket_id": ticket.id, "status": "open",
            "message": "Your request has been escalated to a staff member. They will reach out shortly."}


# ── private tools (OTP-gated) ─────────────────────────────────────────────────

async def _gate(db: AsyncSession, ctx: ToolContext, tool_name: str, args: dict) -> tuple[Student | None, dict | None]:
    """Return (student, None) if access is allowed, else (None, payload_for_llm)."""
    roll = entities.normalise_roll(str(args.get("roll_number", "")))
    if not roll:
        return None, {"error": "invalid_roll_number",
                      "message": "Ask for the roll number in the format PROGRAMME-YEAR-NUMBER, e.g. BSCS-2023-014."}
    student = (await db.execute(select(Student).where(Student.roll_number == roll))).unique().scalar_one_or_none()
    if not student:
        return None, {"error": f"No student found with roll number {roll}"}
    if await otp_service.is_verified(db, ctx.session_id, roll):
        return student, None
    call = {"name": tool_name, "args": {**args, "roll_number": roll}}
    payload = await otp_service.start_challenge(db, ctx.session_id, student, call, ctx.question)
    return None, payload


async def tool_get_student_result(db: AsyncSession, student: Student, semester_no: int | None = None,
                                  term: str | None = None) -> dict[str, Any]:
    rows = (await db.execute(select(ResultRecord).where(ResultRecord.roll_number == student.roll_number)
                             .order_by(ResultRecord.semester_no))).scalars().all()
    if not rows:
        return {"roll_number": student.roll_number, "name": student.name,
                "message": "No result has been declared yet for this student (first-semester students get results after final exams)."}
    sel = rows
    if semester_no:
        sel = [r for r in rows if r.semester_no == int(semester_no)]
    elif term:
        tn = entities.find_term(term) or term
        sel = [r for r in rows if r.term.lower() == tn.lower()]
    else:
        sel = [rows[-1]]
    if not sel:
        return {"roll_number": student.roll_number, "error": "No result for that semester",
                "available": [f"Semester {r.semester_no} ({r.term})" for r in rows]}
    r = sel[0]
    return {
        "verified": True, "roll_number": student.roll_number, "name": student.name, "program": student.program_code,
        "semester_no": r.semester_no, "term": r.term, "gpa": r.gpa, "cgpa": r.cgpa, "status": r.status,
        "credit_hours": r.credit_hours, "published_on": _date(r.published_on), "gazette_ref": r.gazette_ref,
        "courses": [{"code": c["code"], "title": c["title"], "credit_hours": c["credit_hours"], "marks": c["total"],
                     "grade": c["grade"]} for c in r.courses],
        "other_semesters": [{"semester_no": x.semester_no, "term": x.term, "gpa": x.gpa} for x in rows if x is not r],
        "source": f"Result Gazette {r.gazette_ref}",
    }


async def tool_get_fee_status(db: AsyncSession, student: Student) -> dict[str, Any]:
    rows = (await db.execute(select(FeeRecord).where(FeeRecord.roll_number == student.roll_number))).scalars().all()
    rows = sorted(rows, key=lambda f: f.due_date)
    current = rows[-1] if rows else None
    unpaid = [f for f in rows if f.status != "Paid"]
    return {
        "verified": True, "roll_number": student.roll_number, "name": student.name, "today": str(today()),
        "current": {"term": current.term, "challan_no": current.challan_no, "amount": current.amount,
                    "scholarship_discount": current.scholarship_discount, "late_fine": current.late_fine,
                    "total_payable": (current.amount + current.late_fine) if current.status != "Paid" else 0,
                    "due_date": _date(current.due_date), "status": current.status, "paid_on": _date(current.paid_on),
                    "bank": current.bank} if current else None,
        "outstanding_total": sum(f.amount + f.late_fine for f in unpaid), "currency": "PKR",
        "history": [{"term": f.term, "amount": f.amount, "status": f.status, "paid_on": _date(f.paid_on)} for f in rows[:-1]],
        "source": "Directorate of Finance ledger",
    }


async def tool_get_attendance(db: AsyncSession, student: Student) -> dict[str, Any]:
    rows = (await db.execute(select(AttendanceRecord).where(AttendanceRecord.roll_number == student.roll_number))).scalars().all()
    if not rows:
        return {"verified": True, "roll_number": student.roll_number, "name": student.name,
                "message": "No attendance recorded yet this term (1st-semester classes have not started)."}
    return {"verified": True, "roll_number": student.roll_number, "name": student.name, "term": rows[0].term,
            "updated_on": _date(rows[0].updated_on), "minimum_required_percent": 75,
            "courses": [{"course": f"{a.course_code} {a.course_title}", "attended": a.attended, "total": a.total,
                         "percentage": a.percentage, "short": a.percentage < 75} for a in rows],
            "overall_percentage": round(100 * sum(a.attended for a in rows) / max(1, sum(a.total for a in rows)), 1),
            "source": "Attendance register (LMS)"}


async def tool_get_student_profile(db: AsyncSession, student: Student) -> dict[str, Any]:
    prog = (await db.execute(select(Program).where(Program.code == student.program_code))).unique().scalar_one_or_none()
    advisor = (await db.get(Faculty, student.advisor_id)) if student.advisor_id else None
    hostel = (await db.get(Hostel, student.hostel_id)) if student.hostel_id else None
    return {"verified": True, "roll_number": student.roll_number, "name": student.name,
            "father_name": student.father_name, "program": prog.name if prog else student.program_code,
            "batch": student.batch, "section": student.section, "current_semester": student.current_semester,
            "campus": student.campus.name if student.campus else None, "status": student.status,
            "cgpa": student.cgpa, "email": student.email,
            "advisor": f"{advisor.name} ({advisor.email})" if advisor else None,
            "hostel": hostel.name if hostel else "Day scholar", "source": "Registrar student record"}


# ── dispatcher ────────────────────────────────────────────────────────────────

def _int(v) -> int | None:
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        m = re.search(r"\d", str(v))
        return int(m.group()) if m else None


async def execute_tool(db: AsyncSession, tool_name: str, args: dict, conversation_id: str = "",
                       ctx: ToolContext | None = None) -> dict[str, Any]:
    """Dispatch a tool call to the right implementation."""
    ctx = ctx or ToolContext(conversation_id=conversation_id)
    args = args or {}
    try:
        if tool_name in PRIVATE_TOOLS:
            student, blocked = await _gate(db, ctx, tool_name, args)
            if blocked is not None:
                return blocked
            if tool_name == "get_student_result":
                return await tool_get_student_result(db, student, _int(args.get("semester_no")), args.get("term"))
            if tool_name == "get_fee_status":
                return await tool_get_fee_status(db, student)
            if tool_name == "get_attendance":
                return await tool_get_attendance(db, student)
            return await tool_get_student_profile(db, student)

        if tool_name == "get_department":
            return await tool_get_department(db, args.get("name_or_region", ""))
        if tool_name == "list_campuses":
            return await tool_list_campuses(db)
        if tool_name == "list_programs":
            return await tool_list_programs(db, args.get("level"), args.get("campus"))
        if tool_name == "get_program_info":
            return await tool_get_program_info(db, args.get("program", ""))
        if tool_name == "get_fee_tariff":
            return await tool_get_fee_tariff(db, args.get("program", ""), args.get("category"))
        if tool_name == "get_deadline":
            return await tool_get_deadline(db, args.get("service", ""))
        if tool_name == "get_academic_calendar":
            return await tool_get_academic_calendar(db, args.get("program"), args.get("term"), args.get("event"))
        if tool_name == "get_class_timetable":
            return await tool_get_class_timetable(db, args.get("program", ""), _int(args.get("semester_no")), args.get("day"))
        if tool_name == "get_courses":
            return await tool_get_courses(db, args.get("program"), _int(args.get("semester_no")), args.get("query"))
        if tool_name == "get_faculty":
            return await tool_get_faculty(db, args.get("query", ""))
        if tool_name == "get_document_checklist":
            return await tool_get_document_checklist(db, args.get("service", ""))
        if tool_name == "get_scholarships":
            return await tool_get_scholarships(db, args.get("query"))
        if tool_name == "get_hostel_info":
            return await tool_get_hostel_info(db, args.get("campus"), args.get("gender"))
        if tool_name == "get_transport_routes":
            return await tool_get_transport_routes(db, args.get("area"))
        if tool_name == "create_escalation_ticket":
            return await tool_create_escalation(db, ctx.conversation_id or args.get("conversation_id", conversation_id),
                                                args.get("reason", ""))
        if tool_name == "search_knowledge_base":
            from app.rag.retrieve import search_knowledge_base
            return await search_knowledge_base(db, args.get("query", ""))
    except Exception as e:  # a broken tool must never crash the chat
        import logging
        logging.getLogger("tools").exception("Tool %s failed", tool_name)
        return {"error": f"Tool {tool_name} failed: {type(e).__name__}"}
    return {"error": f"Unknown tool: {tool_name}"}
