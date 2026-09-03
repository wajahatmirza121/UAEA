"""Seed script — populates the DB with realistic demo data.

Run: python -m app.db.seed
"""

import asyncio
import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    Base, Campus, Contact, Department, FeeTariff, Service, Deadline,
    KnowledgeChunk, Conversation, Message, UnansweredQuery,
)
from app.db.session import async_session, engine


def _d(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


# ── Seed data ─────────────────────────────────────────────────────────────────

CONTACTS = [
    {"id": "ct-01", "phone": "051-9250101", "email": "admissions@uaea.edu.pk", "office_hours": "09:00 – 16:30"},
    {"id": "ct-02", "phone": "051-9250142", "email": "exams@uaea.edu.pk", "office_hours": "09:00 – 16:30"},
    {"id": "ct-03", "phone": "051-9250188", "email": "degree@uaea.edu.pk", "office_hours": "09:00 – 15:00"},
    {"id": "ct-04", "phone": "051-9250133", "email": "finance@uaea.edu.pk", "office_hours": "09:00 – 16:00"},
    {"id": "ct-05", "phone": "051-4567890", "email": "rwp@uaea.edu.pk", "office_hours": "08:30 – 16:00"},
    {"id": "ct-06", "phone": "042-35800210", "email": "lhr@uaea.edu.pk", "office_hours": "08:30 – 16:00"},
]

CAMPUSES = [
    {"id": "camp-01", "name": "Islamabad Main Campus", "region": "Islamabad", "address": "H-8, Islamabad", "contact_id": "ct-01"},
    {"id": "camp-02", "name": "Regional Campus Rawalpindi", "region": "Punjab", "address": "Satellite Town, Rawalpindi", "contact_id": "ct-05"},
    {"id": "camp-03", "name": "Regional Campus Lahore", "region": "Punjab", "address": "Gulberg III, Lahore", "contact_id": "ct-06"},
]

DEPARTMENTS = [
    {"id": "dep-01", "name_en": "Directorate of Admissions", "name_ur": "شعبۂ داخلہ", "category": "Admissions", "region_id": "camp-01", "contact_id": "ct-01"},
    {"id": "dep-02", "name_en": "Examinations Department", "name_ur": "شعبۂ امتحانات", "category": "Examinations", "region_id": "camp-01", "contact_id": "ct-02"},
    {"id": "dep-03", "name_en": "Degree & Transcript Section", "name_ur": "شعبۂ ڈگری و ٹرانسکرپٹ", "category": "Certification", "region_id": "camp-01", "contact_id": "ct-03"},
    {"id": "dep-04", "name_en": "Directorate of Finance", "name_ur": "شعبۂ مالیات", "category": "Finance", "region_id": "camp-01", "contact_id": "ct-04"},
]

FEE_TARIFFS = [
    {"id": "fee-01", "program": "BS Computer Science", "category": "Semester (new)", "amount": 28500, "effective_from": _d("2026-07-01"), "source_doc_ref": "Fee Circular A-26 §3.1"},
    {"id": "fee-02", "program": "BS Computer Science", "category": "Per credit hour (repeat)", "amount": 2150, "effective_from": _d("2026-07-01"), "source_doc_ref": "Fee Circular A-26 §3.2"},
    {"id": "fee-03", "program": "B.Ed (1.5 Year)", "category": "Semester (new)", "amount": 18600, "effective_from": _d("2026-07-01"), "source_doc_ref": "Fee Circular A-26 §3.4"},
    {"id": "fee-04", "program": "MA Urdu", "category": "Semester (new)", "amount": 16200, "effective_from": _d("2026-07-01"), "source_doc_ref": "Fee Circular A-26 §3.6"},
    {"id": "fee-05", "program": "MSc Mathematics", "category": "Semester (new)", "amount": 19800, "effective_from": _d("2026-07-01"), "source_doc_ref": "Fee Circular A-26 §3.7"},
    {"id": "fee-06", "program": "Transcript", "category": "Normal service", "amount": 1500, "effective_from": _d("2026-01-01"), "source_doc_ref": "Degree Manual §4.1"},
    {"id": "fee-07", "program": "Transcript", "category": "Urgent service", "amount": 3500, "effective_from": _d("2026-01-01"), "source_doc_ref": "Degree Manual §4.2"},
    {"id": "fee-08", "program": "Degree", "category": "Normal service", "amount": 2000, "effective_from": _d("2026-01-01"), "source_doc_ref": "Degree Manual §3.5"},
]

SERVICES = [
    {
        "id": "svc-01", "name_en": "Admission & Enrolment", "name_ur": "داخلہ و اندراج",
        "category": "Admissions", "fee_id": "fee-01",
        "description": "Apply for admission to any programme offered by the University.",
        "document_checklist": [
            {"en": "CNIC or B-Form", "ur": "شناختی کارڈ یا ب فارم", "copy": True},
            {"en": "Previous degree or certificate", "ur": "پچھلی ڈگری یا سرٹیفکیٹ", "copy": True},
            {"en": "Two passport-size photographs", "ur": "دو پاسپورٹ سائز تصاویر", "copy": False},
            {"en": "Paid fee challan receipt", "ur": "ادا شدہ فیس چالان کی رسید", "copy": False},
        ],
        "procedure_text": "Apply online through the admission portal during the announced window. Attach scanned documents, generate the challan, pay at any designated bank branch, then upload the stamped receipt.",
        "source_doc_ref": "Prospectus 2026-27 §2.1",
    },
    {
        "id": "svc-02", "name_en": "Fee Challan", "name_ur": "فیس چالان",
        "category": "Finance", "fee_id": "fee-01",
        "description": "Generate and pay the semester fee challan.",
        "document_checklist": [
            {"en": "Portal-generated challan form", "ur": "پورٹل سے بنایا گیا چالان فارم", "copy": False},
            {"en": "CNIC for bank counter", "ur": "بینک کاؤنٹر کے لیے شناختی کارڈ", "copy": True},
        ],
        "procedure_text": "Generate the challan from the student portal, print all three copies, and deposit at a designated branch before the due date.",
        "source_doc_ref": "Fee Circular A-26 §4",
    },
    {
        "id": "svc-03", "name_en": "Result Enquiry", "name_ur": "نتیجہ",
        "category": "Examinations",
        "description": "Check examination results and gazette notifications.",
        "document_checklist": [
            {"en": "Roll number", "ur": "رول نمبر", "copy": False},
        ],
        "procedure_text": "Results are published on the results portal by semester. Provisional results appear before the gazette is notified.",
        "source_doc_ref": "Exam Regs 2026 §7",
    },
    {
        "id": "svc-04", "name_en": "Degree Application", "name_ur": "ڈگری کی درخواست",
        "category": "Certification", "fee_id": "fee-08",
        "description": "Apply for issuance of degree after completion of programme.",
        "document_checklist": [
            {"en": "Degree application form", "ur": "ڈگری درخواست فارم", "copy": False},
            {"en": "All semester result cards", "ur": "تمام سمسٹر کے رزلٹ کارڈ", "copy": True},
            {"en": "CNIC", "ur": "شناختی کارڈ", "copy": True},
            {"en": "Two passport-size photographs", "ur": "دو پاسپورٹ سائز تصاویر", "copy": False},
            {"en": "Paid degree fee challan", "ur": "ادا شدہ ڈگری فیس چالان", "copy": False},
            {"en": "No-dues clearance from the campus", "ur": "کیمپس سے واجبات کی کلیئرنس", "copy": False},
        ],
        "procedure_text": "Submit the complete set to the Degree Section after the gazette is notified. Published processing time is 6 to 8 weeks for normal issuance.",
        "source_doc_ref": "Degree Manual §3",
    },
    {
        "id": "svc-05", "name_en": "Transcript / PRC", "name_ur": "ٹرانسکرپٹ / پی آر سی",
        "category": "Certification", "fee_id": "fee-06",
        "description": "Request official transcript or Provisional Result Certificate.",
        "document_checklist": [
            {"en": "Transcript request form", "ur": "ٹرانسکرپٹ درخواست فارم", "copy": False},
            {"en": "CNIC", "ur": "شناختی کارڈ", "copy": True},
            {"en": "Paid fee challan", "ur": "ادا شدہ فیس چالان", "copy": False},
            {"en": "Authority letter, if collected by another person", "ur": "اجازت نامہ", "copy": False},
        ],
        "procedure_text": "Normal issuance is 3 to 4 weeks; urgent is 5 working days at the higher tariff.",
        "source_doc_ref": "Degree Manual §4",
    },
]

DEADLINES = [
    {"id": "dl-01", "service_id": "svc-01", "semester": "Autumn 2026", "date": _d("2026-09-30"), "source_doc_ref": "Admission Notice A-26/11"},
    {"id": "dl-02", "service_id": "svc-02", "semester": "Autumn 2026", "date": _d("2026-09-20"), "source_doc_ref": "Fee Circular A-26 §4.1"},
    {"id": "dl-03", "service_id": "svc-04", "semester": "Spring 2026 graduates", "date": _d("2026-11-30"), "source_doc_ref": "Degree Manual §3.1"},
]

KNOWLEDGE_CHUNKS = [
    {"id": "kc-01", "source_doc_id": "prospectus-2026", "section": "§2 Admission Policy",
     "text": "Admission to all undergraduate programmes requires at least 50% marks in the qualifying examination. Candidates awaiting results may apply provisionally."},
    {"id": "kc-02", "source_doc_id": "prospectus-2026", "section": "§3 Fee Structure",
     "text": "Programme dues are revised each academic year and published in the accompanying fee circular. Late payment attracts a surcharge of Rs 500 per week."},
    {"id": "kc-03", "source_doc_id": "prospectus-2026", "section": "§4 Scholarships",
     "text": "Need-based scholarships cover up to 50% of tuition. Applications close 25 October each semester. Results announced within 6 weeks of the deadline."},
    {"id": "kc-04", "source_doc_id": "exam-regs-2026", "section": "§5 Date Sheet",
     "text": "The date sheet is published roughly four weeks before the examination window. Clashes between two papers in the same slot must be reported within seven days."},
    {"id": "kc-05", "source_doc_id": "exam-regs-2026", "section": "§7 Results",
     "text": "Results are published on the results portal once the gazette is notified. The gazette is the official record; the portal display is provisional."},
    {"id": "kc-06", "source_doc_id": "exam-regs-2026", "section": "§9 Rechecking",
     "text": "Rechecking confirms totalling and that no question was left unmarked. It is not a re-evaluation. Applications close 30 days after the result is declared. Fee is Rs 1,500 per paper."},
    {"id": "kc-07", "source_doc_id": "degree-manual", "section": "§3 Degree Issuance",
     "text": "Normal processing time for degree issuance is 6 to 8 weeks after the gazette is notified. Urgent processing is available at double the fee."},
    {"id": "kc-08", "source_doc_id": "degree-manual", "section": "§4 Transcripts",
     "text": "Transcript requests are processed in 3 to 4 weeks for normal and 5 working days for urgent. Collection is in person or by courier at the applicant's cost."},
    {"id": "kc-09", "source_doc_id": "student-handbook", "section": "§6 Assignments",
     "text": "Assignments must be submitted to the allocated tutor by the published date. Late submissions may incur a penalty as determined by the department."},
    {"id": "kc-10", "source_doc_id": "fee-circular-2026", "section": "§4 Challan Payment",
     "text": "Generate the challan from the student portal. Deposit at any designated bank branch. Portal status updates within two working days of the bank posting the payment."},
]

UNANSWERED = [
    {"id": "uq-01", "text": "BS CS ki fees per semester kitni hai agar main repeat course le raha hoon", "intent": "fee_tariff", "confidence": 0.41, "count": 34, "reason": "Low classifier confidence"},
    {"id": "uq-02", "text": "assignment late jama karwane pe kitna fine hai", "intent": "assignments", "confidence": 0.55, "count": 47, "reason": "Tool returned no data"},
    {"id": "uq-03", "text": "scholarship ka result kab announce hoga Autumn 2026", "intent": "scholarships", "confidence": 0.63, "count": 25, "reason": "Stale source document"},
]


async def seed() -> None:
    async with async_session() as db:
        # Check if already seeded
        count = (await db.execute(select(text("1")).select_from(
            text("departments")
        ).limit(1))).scalar_one_or_none()

        # Clear tables in reverse dependency order
        for table in ["unanswered_queries", "audit_logs", "escalation_tickets",
                       "messages", "conversations", "knowledge_chunks",
                       "deadlines", "services", "fee_tariffs", "departments",
                       "campuses", "contacts"]:
            await db.execute(text(f"DELETE FROM {table}"))

        # Insert seed data
        for c in CONTACTS:
            db.add(Contact(**c))
        for c in CAMPUSES:
            db.add(Campus(**c))
        for d in DEPARTMENTS:
            db.add(Department(**d))
        for f in FEE_TARIFFS:
            db.add(FeeTariff(**f))
        for s in SERVICES:
            db.add(Service(**s))
        for dl in DEADLINES:
            db.add(Deadline(**dl))
        for kc in KNOWLEDGE_CHUNKS:
            db.add(KnowledgeChunk(**kc))
        for uq in UNANSWERED:
            db.add(UnansweredQuery(**uq))

        await db.commit()
        print(f"Seeded database with {len(CONTACTS)} contacts, {len(CAMPUSES)} campuses, "
              f"{len(DEPARTMENTS)} departments, {len(FEE_TARIFFS)} fee tariffs, "
              f"{len(SERVICES)} services, {len(DEADLINES)} deadlines, "
              f"{len(KNOWLEDGE_CHUNKS)} knowledge chunks, {len(UNANSWERED)} unanswered queries.")


if __name__ == "__main__":
    asyncio.run(seed())
else:
    asyncio.run(seed())
