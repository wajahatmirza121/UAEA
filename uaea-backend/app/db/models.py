"""SQLAlchemy models — all tables for UAEA backend."""

from __future__ import annotations

import datetime
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


# pgvector columns render as TEXT on SQLite so the whole schema also runs in
# local "no Docker" mode and in the test-suite.
@compiles(Vector, "sqlite")
def _compile_vector_sqlite(type_, compiler, **kw):  # pragma: no cover - trivial
    return "TEXT"


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


# ══════════════════════════════════════════════════════════════════════════════
#  Academic catalogue (public information — anyone can ask)
# ══════════════════════════════════════════════════════════════════════════════

class Program(Base):
    """A degree programme, e.g. BSCS. Public."""
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ur: Mapped[str] = mapped_column(String(255), nullable=True)
    level: Mapped[str] = mapped_column(String(40), nullable=False)          # Undergraduate / Graduate / Postgraduate
    faculty: Mapped[str] = mapped_column(String(120), nullable=False)       # Faculty of Computing ...
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=True)
    duration_years: Mapped[float] = mapped_column(Float, nullable=False)
    semesters: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=True)
    shift: Mapped[str] = mapped_column(String(60), nullable=True)
    eligibility: Mapped[str] = mapped_column(Text, nullable=True)
    min_percentage: Mapped[int] = mapped_column(Integer, nullable=True)
    entry_test: Mapped[str] = mapped_column(String(255), nullable=True)
    campuses: Mapped[list] = mapped_column(JSON, nullable=True, default=list)   # campus ids
    aliases: Mapped[list] = mapped_column(JSON, nullable=True, default=list)    # bscs, bs cs, computer science
    description: Mapped[str] = mapped_column(Text, nullable=True)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)

    department: Mapped[Department | None] = relationship(lazy="joined")


class AcademicEvent(Base):
    """Academic calendar entry: classes start, mid-terms, finals, breaks. Public."""
    __tablename__ = "academic_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    term: Mapped[str] = mapped_column(String(40), nullable=False, index=True)   # Fall 2026
    program_code: Mapped[str] = mapped_column(String(20), nullable=True, index=True)  # NULL = all programmes
    level: Mapped[str] = mapped_column(String(40), nullable=True)               # optional level filter
    event: Mapped[str] = mapped_column(String(120), nullable=False)
    event_ur: Mapped[str] = mapped_column(String(120), nullable=True)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)


class Faculty(Base):
    """A teacher. Public directory information only (no personal phone)."""
    __tablename__ = "faculty"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    designation: Mapped[str] = mapped_column(String(80), nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=True)
    program_codes: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    email: Mapped[str] = mapped_column(String(160), nullable=True)
    office: Mapped[str] = mapped_column(String(120), nullable=True)
    office_hours: Mapped[str] = mapped_column(String(120), nullable=True)
    specialization: Mapped[str] = mapped_column(String(255), nullable=True)
    qualification: Mapped[str] = mapped_column(String(160), nullable=True)

    department: Mapped[Department | None] = relationship(lazy="joined")


class Course(Base):
    """A course in a programme's scheme of studies. Public."""
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    program_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    semester_no: Mapped[int] = mapped_column(Integer, nullable=False)
    instructor_id: Mapped[str] = mapped_column(String(36), ForeignKey("faculty.id"), nullable=True)
    prerequisite: Mapped[str] = mapped_column(String(20), nullable=True)

    instructor: Mapped[Faculty | None] = relationship(lazy="joined")


class ClassSchedule(Base):
    """One weekly timetable slot. Public."""
    __tablename__ = "class_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    term: Mapped[str] = mapped_column(String(40), nullable=False)
    program_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    semester_no: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    campus_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    day: Mapped[str] = mapped_column(String(12), nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    course_title: Mapped[str] = mapped_column(String(200), nullable=False)
    room: Mapped[str] = mapped_column(String(40), nullable=True)
    instructor_name: Mapped[str] = mapped_column(String(160), nullable=True)


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ur: Mapped[str] = mapped_column(String(200), nullable=True)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)     # Need-based / Merit / Special
    coverage: Mapped[str] = mapped_column(String(200), nullable=False)
    eligibility: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    seats: Mapped[int] = mapped_column(Integer, nullable=True)
    how_to_apply: Mapped[str] = mapped_column(Text, nullable=True)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)


class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    campus_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)    # Male / Female
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    vacant_seats: Mapped[int] = mapped_column(Integer, nullable=True)
    room_type: Mapped[str] = mapped_column(String(120), nullable=True)
    fee_per_semester: Mapped[int] = mapped_column(Integer, nullable=False)
    mess_fee_per_month: Mapped[int] = mapped_column(Integer, nullable=True)
    facilities: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    warden_name: Mapped[str] = mapped_column(String(160), nullable=True)
    warden_phone: Mapped[str] = mapped_column(String(40), nullable=True)
    source_doc_ref: Mapped[str] = mapped_column(String(255), nullable=True)

    campus: Mapped[Campus | None] = relationship(lazy="joined")


class TransportRoute(Base):
    __tablename__ = "transport_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    route_no: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    campus_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    stops: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    morning_departure: Mapped[str] = mapped_column(String(10), nullable=True)
    evening_departure: Mapped[str] = mapped_column(String(10), nullable=True)
    fee_per_semester: Mapped[int] = mapped_column(Integer, nullable=True)
    driver_contact: Mapped[str] = mapped_column(String(40), nullable=True)

    campus: Mapped[Campus | None] = relationship(lazy="joined")


# ══════════════════════════════════════════════════════════════════════════════
#  Student records (PRIVATE — only after OTP verification)
# ══════════════════════════════════════════════════════════════════════════════

class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    roll_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    father_name: Mapped[str] = mapped_column(String(160), nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    program_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    campus_id: Mapped[str] = mapped_column(String(36), ForeignKey("campuses.id"), nullable=True)
    batch: Mapped[str] = mapped_column(String(20), nullable=True)          # Fall 2023
    section: Mapped[str] = mapped_column(String(10), nullable=True)
    current_semester: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
    cgpa: Mapped[float] = mapped_column(Float, nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)          # WhatsApp number for OTP
    email: Mapped[str] = mapped_column(String(160), nullable=True)
    cnic_masked: Mapped[str] = mapped_column(String(20), nullable=True)
    hostel_id: Mapped[str] = mapped_column(String(36), ForeignKey("hostels.id"), nullable=True)
    advisor_id: Mapped[str] = mapped_column(String(36), ForeignKey("faculty.id"), nullable=True)

    campus: Mapped[Campus | None] = relationship(lazy="joined")


class ResultRecord(Base):
    __tablename__ = "result_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    roll_number: Mapped[str] = mapped_column(String(30), ForeignKey("students.roll_number"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(40), nullable=False)
    semester_no: Mapped[int] = mapped_column(Integer, nullable=False)
    gpa: Mapped[float] = mapped_column(Float, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)          # Pass / Probation / Fail
    courses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    published_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    gazette_ref: Mapped[str] = mapped_column(String(80), nullable=True)


class FeeRecord(Base):
    __tablename__ = "fee_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    roll_number: Mapped[str] = mapped_column(String(30), ForeignKey("students.roll_number"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(40), nullable=False)
    challan_no: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    late_fine: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scholarship_discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    paid_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)          # Paid / Unpaid / Overdue
    bank: Mapped[str] = mapped_column(String(80), nullable=True)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    roll_number: Mapped[str] = mapped_column(String(30), ForeignKey("students.roll_number"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(40), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    course_title: Mapped[str] = mapped_column(String(200), nullable=False)
    attended: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    updated_on: Mapped[datetime.date] = mapped_column(Date, nullable=True)


# ══════════════════════════════════════════════════════════════════════════════
#  OTP verification (WhatsApp)
# ══════════════════════════════════════════════════════════════════════════════

class OtpChallenge(Base):
    """One OTP sent for one (chat session, roll number).

    status: pending → verified | expired | locked | cancelled.
    When verified, ``verified_until`` grants this session access to that
    student's private records for a short window.
    """
    __tablename__ = "otp_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    roll_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_tool: Mapped[dict] = mapped_column(JSON, nullable=True)          # {"name":..., "args":...}
    pending_question: Mapped[str] = mapped_column(Text, nullable=True)
    delivery: Mapped[str] = mapped_column(String(40), nullable=True)         # whatsapp:twilio / console / failed
    delivery_ref: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_until: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
