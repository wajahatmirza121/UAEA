"""Seed script — populates the DB with a large, realistic demo dataset.

Run:
    python -m app.db.seed                 # tables must already exist (alembic upgrade head)
    python -m app.db.seed --create-tables # create tables first (handy for SQLite local mode)

Everything is generated deterministically (fixed random seed), so the same
roll numbers, results and fee records appear on every machine.

Every student record carries the demo WhatsApp number from
``settings.demo_student_phone`` (default +92 333 3797617). Any private lookup
(result, fee status, attendance, profile) sends the OTP to that number.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import random

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    Base, Campus, Contact, Department, FeeTariff, Service, Deadline,
    KnowledgeChunk, UnansweredQuery, Program, AcademicEvent, Faculty, Course,
    ClassSchedule, Scholarship, Hostel, TransportRoute, Student, ResultRecord,
    FeeRecord, AttendanceRecord,
)
from app.db import seed_data as D

CURRENT_TERM = "Fall 2026"
CURRENT_YEAR = 2026
AS_OF = datetime.date(2026, 10, 20)        # attendance / fee status snapshot date

GRADE_SCALE = [  # (min marks, grade, points)
    (85, "A", 4.00), (80, "A-", 3.67), (75, "B+", 3.33), (71, "B", 3.00), (68, "B-", 2.67),
    (64, "C+", 2.33), (61, "C", 2.00), (58, "C-", 1.67), (54, "D+", 1.33), (50, "D", 1.00), (0, "F", 0.00),
]

MALE_FIRST = ["Ali", "Ahmed", "Hamza", "Usman", "Bilal", "Hassan", "Hussain", "Umar", "Zain", "Abdullah",
              "Fahad", "Saad", "Talha", "Haris", "Danish", "Shoaib", "Waleed", "Arslan", "Imran", "Junaid",
              "Kashif", "Mohsin", "Nabeel", "Owais", "Rizwan", "Salman", "Taimoor", "Yasir", "Zeeshan", "Faizan"]
FEMALE_FIRST = ["Aisha", "Ayesha", "Fatima", "Zainab", "Maryam", "Sara", "Hira", "Iqra", "Amna", "Mahnoor",
                "Laiba", "Areeba", "Noor", "Hafsa", "Kinza", "Eman", "Rabia", "Sana", "Mehwish", "Anum",
                "Bushra", "Javeria", "Mariam", "Nimra", "Saba", "Tayyaba", "Urooj", "Wajiha", "Zara", "Khadija"]
SURNAMES = ["Khan", "Ahmed", "Ali", "Raza", "Hussain", "Iqbal", "Malik", "Qureshi", "Butt", "Chaudhry",
            "Sheikh", "Siddiqui", "Abbasi", "Javed", "Tariq", "Mirza", "Awan", "Rana", "Hashmi", "Bhatti",
            "Shah", "Rehman", "Aslam", "Akhtar", "Baig", "Kazmi", "Niazi", "Yousaf", "Saleem", "Nawaz"]
FATHER_FIRST = ["Muhammad", "Abdul", "Ghulam", "Tariq", "Javed", "Khalid", "Rashid", "Shahid", "Nasir", "Zafar",
                "Pervaiz", "Arshad", "Asif", "Saeed", "Iftikhar", "Riaz", "Mushtaq", "Naeem", "Liaqat", "Anwar"]

# Named demo students (easy to remember when testing). Everything else is generated.
DEMO_STUDENTS = [
    # roll, name, gender, campus, ability(mean marks), hostel, scholarship%
    ("BSCS-2023-014", "Aisha Khan", "F", "camp-01", 84, "hos-03", 0),
    ("BSSE-2024-011", "Ayesha Siddiqui", "F", "camp-01", 78, None, 25),
    ("BSCS-2024-007", "Ali Raza", "M", "camp-01", 72, "hos-01", 0),
    ("BBA-2023-021", "Fatima Noor", "F", "camp-03", 80, "hos-05", 0),
    ("BSIT-2025-003", "Hamza Iqbal", "M", "camp-02", 66, None, 0),
    ("BSAI-2024-002", "Zainab Ahmed", "F", "camp-01", 88, None, 50),
    ("MSCS-2025-002", "Usman Tariq", "M", "camp-01", 79, None, 0),
    ("BSCS-2023-031", "Bilal Hussain", "M", "camp-01", 53, "hos-01", 0),
    ("BSPSY-2024-009", "Maryam Javed", "F", "camp-03", 76, None, 0),
    ("BSMATH-2025-012", "Hassan Ali", "M", "camp-06", 70, None, 0),
    ("BED15-2025-040", "Sara Khan", "F", "camp-04", 74, None, 0),
    ("BSCS-2026-001", "Ahmed Raza", "M", "camp-01", 75, None, 0),
    ("MBA-2025-015", "Hira Malik", "F", "camp-04", 77, None, 0),
    ("BSENG-2024-018", "Noor Fatima", "F", "camp-05", 81, None, 0),
]

RANDOM_STUDENTS_PER_BATCH = {"Undergraduate": 3, "Graduate": 4, "Postgraduate": 3}


# ── helpers ───────────────────────────────────────────────────────────────────

def grade_for(marks: float) -> tuple[str, float]:
    for floor, g, gp in GRADE_SCALE:
        if marks >= floor:
            return g, gp
    return "F", 0.0


def term_for(intake_year: int, semester_no: int) -> str:
    """Fall intake: sem 1 = Fall Y, sem 2 = Spring Y+1, sem 3 = Fall Y+1, …"""
    k = semester_no - 1
    year = intake_year + (k + 1) // 2
    return ("Fall " if k % 2 == 0 else "Spring ") + str(year)


def semester_now(intake_year: int) -> int:
    return (CURRENT_YEAR - intake_year) * 2 + 1


def result_publish_date(term: str) -> datetime.date:
    season, year = term.split()
    y = int(year)
    return datetime.date(y + 1, 2, 5) if season == "Fall" else datetime.date(y, 7, 20)


def fee_due_date(term: str, first_semester_now: bool) -> datetime.date:
    season, year = term.split()
    y = int(year)
    if term == CURRENT_TERM and first_semester_now:
        return datetime.date(2026, 10, 28)
    return datetime.date(y, 9, 20) if season == "Fall" else datetime.date(y, 2, 5)


def _course_code(prefix: str, sem: int, i: int) -> str:
    return f"{prefix}-{sem}{i + 1:02d}"


def build_courses(faculty_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for prog in D.PROGRAMS:
        teachers = [f for f in faculty_rows if prog["code"] in f["program_codes"]] or faculty_rows[:3]
        plan = D.course_plan(prog["code"])
        t = 0
        for s_idx, sem in enumerate(plan, start=1):
            for i, (title, ch) in enumerate(sem):
                code = _course_code(prog["prefix"], s_idx, i)
                rows.append({
                    "id": f"crs-{prog['code']}-{s_idx}{i + 1:02d}",
                    "code": code, "title": title, "credit_hours": ch,
                    "program_code": prog["code"], "semester_no": s_idx,
                    "instructor_id": teachers[t % len(teachers)]["id"],
                    "prerequisite": _course_code(prog["prefix"], s_idx - 1, i) if s_idx > 1 and i == 0 else None,
                })
                t += 1
    return rows


SLOTS = [("08:30", "09:50"), ("10:00", "11:20"), ("11:30", "12:50"), ("13:30", "14:50"), ("15:00", "16:20")]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAY_PAIRS = [("Monday", "Wednesday"), ("Tuesday", "Thursday"), ("Wednesday", "Friday"),
             ("Monday", "Thursday"), ("Tuesday", "Friday")]


def build_timetable(courses: list[dict], faculty_by_id: dict[str, dict]) -> list[dict]:
    """Weekly timetable for the current (Fall) term: odd semesters, section A, main campus."""
    rows: list[dict] = []
    n = 0
    for prog in D.PROGRAMS:
        block = prog["prefix"]
        for sem_no in range(1, prog["semesters"] + 1, 2):
            sem_courses = [c for c in courses if c["program_code"] == prog["code"] and c["semester_no"] == sem_no]
            for i, c in enumerate(sem_courses):
                d1, d2 = DAY_PAIRS[i % len(DAY_PAIRS)]
                start, end = SLOTS[(i + sem_no) % len(SLOTS)]
                if prog["shift"] and prog["shift"].startswith("Evening"):
                    start, end = [("15:00", "16:20"), ("16:30", "17:50"), ("18:00", "19:20"), ("19:30", "20:50")][i % 4]
                if prog["shift"] == "Weekend":
                    d1, d2 = ("Saturday", "Sunday")
                    start, end = [("09:00", "10:20"), ("10:30", "11:50"), ("12:00", "13:20"), ("14:00", "15:20"), ("15:30", "16:50")][i % 5]
                teacher = faculty_by_id.get(c["instructor_id"], {}).get("name")
                for day in (d1, d2):
                    n += 1
                    rows.append({
                        "id": f"tt-{n:05d}", "term": CURRENT_TERM, "program_code": prog["code"],
                        "semester_no": sem_no, "section": "A", "campus_id": "camp-01", "day": day,
                        "start_time": start, "end_time": end, "course_code": c["code"],
                        "course_title": c["title"], "room": f"{block}-{100 * sem_no + (i + 1)}",
                        "instructor_name": teacher,
                    })
    return rows


def build_students(rng: random.Random) -> list[dict]:
    phone = settings.demo_student_phone
    students: list[dict] = []
    used: set[str] = set()

    def add(roll: str, name: str, gender: str, campus: str, ability: float,
            hostel: str | None, scholarship: int) -> None:
        code, year, _ = roll.rsplit("-", 2)
        prog = D.PROGRAM_BY_CODE[code]
        sem = min(semester_now(int(year)), prog["semesters"])
        father = f"{rng.choice(D_FATHERS)} {name.split()[-1]}"
        cnic_tail = rng.randint(1000, 9999)
        students.append({
            "roll_number": roll, "name": name, "father_name": father, "gender": "Female" if gender == "F" else "Male",
            "program_code": code, "campus_id": campus if campus in prog["campuses"] else prog["campuses"][0],
            "batch": f"Fall {year}", "section": "A", "current_semester": sem, "status": "Active",
            "phone": phone, "email": f"{roll.lower()}@student.uaea.edu.pk",
            "cnic_masked": f"XXXXX-XXX{cnic_tail}-X",
            "hostel_id": hostel, "_ability": ability, "_scholarship": scholarship,
        })
        used.add(roll)

    for roll, name, g, campus, ability, hostel, sch in DEMO_STUDENTS:
        add(roll, name, g, campus, ability, hostel, sch)

    for prog in D.PROGRAMS:
        if prog["semesters"] >= 8:
            years = [2023, 2024, 2025, 2026]
        elif prog["semesters"] == 6:
            years = [2024, 2025]
        else:
            years = [2025, 2026]
        per = RANDOM_STUDENTS_PER_BATCH[prog["level"]]
        for year in years:
            count = per if year != 2026 else 1
            for k in range(count):
                n = rng.randint(1, 160)
                roll = f"{prog['code']}-{year}-{n:03d}"
                while roll in used:
                    n = rng.randint(1, 199)
                    roll = f"{prog['code']}-{year}-{n:03d}"
                female = rng.random() < 0.5
                first = rng.choice(FEMALE_FIRST if female else MALE_FIRST)
                last = rng.choice(SURNAMES)
                campus = rng.choice(prog["campuses"])
                ability = rng.uniform(56, 90)
                sch = rng.choice([0, 0, 0, 0, 25, 50]) if prog["level"] == "Undergraduate" else 0
                add(roll, f"{first} {last}", "F" if female else "M", campus, ability, None, sch)
    return students


D_FATHERS = FATHER_FIRST


def build_records(students: list[dict], courses: list[dict], rng: random.Random):
    results: list[dict] = []
    fees: list[dict] = []
    attendance: list[dict] = []
    by_prog_sem: dict[tuple[str, int], list[dict]] = {}
    for c in courses:
        by_prog_sem.setdefault((c["program_code"], c["semester_no"]), []).append(c)

    challan_seq = 40000
    for s in students:
        prog = D.PROGRAM_BY_CODE[s["program_code"]]
        intake = int(s["batch"].split()[1])
        ability = s.pop("_ability")
        sch_pct = s.pop("_scholarship")
        total_points = 0.0
        total_ch = 0
        cgpa = None
        for sem_no in range(1, s["current_semester"]):
            term = term_for(intake, sem_no)
            course_rows = []
            sem_points = 0.0
            sem_ch = 0
            for c in by_prog_sem.get((s["program_code"], sem_no), []):
                marks = max(28.0, min(98.0, rng.gauss(ability, 8)))
                sessional = round(marks * 0.25)
                mid = round(marks * 0.25 + rng.uniform(-2, 2))
                final = max(0, min(50, round(marks) - sessional - mid))
                total = sessional + mid + final
                g, gp = grade_for(total)
                course_rows.append({"code": c["code"], "title": c["title"], "credit_hours": c["credit_hours"],
                                    "sessional": sessional, "mid": mid, "final": final, "total": total,
                                    "grade": g, "grade_points": gp})
                sem_points += gp * c["credit_hours"]
                sem_ch += c["credit_hours"]
            if not sem_ch:
                continue
            total_points += sem_points
            total_ch += sem_ch
            gpa = round(sem_points / sem_ch, 2)
            cgpa = round(total_points / total_ch, 2)
            fails = [r["code"] for r in course_rows if r["grade"] == "F"]
            if cgpa < 2.0:
                status = "Probation"
            elif fails:
                status = "Pass (repeat " + ", ".join(fails) + ")"
            else:
                status = "Pass"
            results.append({
                "roll_number": s["roll_number"], "term": term, "semester_no": sem_no,
                "gpa": gpa, "cgpa": cgpa, "credit_hours": sem_ch, "status": status,
                "courses": course_rows, "published_on": result_publish_date(term),
                "gazette_ref": f"GZ-{term.replace(' ', '')}-{prog['code']}",
            })
        s["cgpa"] = cgpa
        if cgpa is not None and cgpa < 2.0:
            s["status"] = "Probation"

        # Fee records: one per term up to and including the current one
        base = prog["fee_new"] + 3000  # tuition + examination fee
        for sem_no in range(1, s["current_semester"] + 1):
            term = term_for(intake, sem_no)
            challan_seq += 1
            discount = round(prog["fee_new"] * sch_pct / 100) if sem_no > 1 else 0
            due = fee_due_date(term, s["current_semester"] == 1)
            amount = base + (2500 if sem_no == 1 else 0)
            rec = {"roll_number": s["roll_number"], "term": term, "challan_no": f"CH-{term.split()[1]}-{challan_seq}",
                   "amount": amount - discount, "scholarship_discount": discount, "due_date": due,
                   "late_fine": 0, "paid_on": None, "status": "Paid", "bank": None}
            if term == CURRENT_TERM:
                r = rng.random()
                unpaid = (s["roll_number"] in ("BSCS-2023-031", "BSIT-2025-003", "BSCS-2026-001")) or r < 0.15
                if unpaid:
                    if due < AS_OF:
                        weeks = (AS_OF - due).days // 7 + 1
                        rec.update(status="Overdue", late_fine=500 * weeks)
                    else:
                        rec.update(status="Unpaid")
                else:
                    rec.update(paid_on=due - datetime.timedelta(days=rng.randint(1, 12)),
                               bank=rng.choice(["HBL", "Bank Alfalah", "Meezan Bank", "Allied Bank", "1Link (mobile)"]))
            else:
                late = rng.random() < 0.12
                paid = due + datetime.timedelta(days=rng.randint(3, 20)) if late else due - datetime.timedelta(days=rng.randint(1, 15))
                rec.update(paid_on=paid, late_fine=500 * (((paid - due).days // 7) + 1) if late else 0,
                           bank=rng.choice(["HBL", "Bank Alfalah", "Meezan Bank", "Allied Bank", "1Link (mobile)"]))
            fees.append(rec)

        # Attendance for the current term (1st-semester classes have not started yet)
        if s["current_semester"] > 1:
            weeks_elapsed = (AS_OF - datetime.date(2026, 9, 7)).days // 7
            total = weeks_elapsed * 2
            for c in by_prog_sem.get((s["program_code"], s["current_semester"]), []):
                base_rate = 0.62 + (ability - 50) / 100
                if s["roll_number"] == "BSCS-2023-031":
                    base_rate = 0.66
                rate = max(0.45, min(1.0, rng.gauss(base_rate, 0.07)))
                attended = min(total, round(total * rate))
                attendance.append({
                    "roll_number": s["roll_number"], "term": CURRENT_TERM, "course_code": c["code"],
                    "course_title": c["title"], "attended": attended, "total": total,
                    "percentage": round(100 * attended / total, 1) if total else 0.0, "updated_on": AS_OF,
                })
    return results, fees, attendance


def build_fee_tariffs() -> list[dict]:
    rows = list(D.FEE_TARIFFS_FIXED)
    existing = {(r["program"], r["category"]) for r in rows}
    for p in D.PROGRAMS:
        new_row = (p["name"], "Semester (new)")
        if new_row not in existing:
            rows.append({"id": f"fee-p-{p['code'].lower()}-new", "program": p["name"], "category": "Semester (new)",
                         "amount": p["fee_new"], "effective_from": D._d("2026-07-01"),
                         "source_doc_ref": "Fee Circular A-26 §3 (programme schedule)"})
        rep = (p["name"], "Per credit hour (repeat)")
        if rep not in existing:
            per_ch = int(round(p["fee_new"] / 15 / 50.0) * 50) + 150
            rows.append({"id": f"fee-p-{p['code'].lower()}-rep", "program": p["name"], "category": "Per credit hour (repeat)",
                         "amount": per_ch, "effective_from": D._d("2026-07-01"),
                         "source_doc_ref": "Fee Circular A-26 §3 (repeat courses)"})
        if p["shift"] and "Evening" in p["shift"] and p["level"] == "Undergraduate":
            rows.append({"id": f"fee-p-{p['code'].lower()}-eve", "program": p["name"], "category": "Semester (evening shift)",
                         "amount": int(p["fee_new"] * 1.1 // 100 * 100), "effective_from": D._d("2026-07-01"),
                         "source_doc_ref": "Fee Circular A-26 §3.9"})
    return rows


def build_events() -> list[dict]:
    rows = []
    n = 0
    for term, prog, ev, ev_ur, start, end, notes in D.ACADEMIC_EVENTS_GLOBAL:
        n += 1
        rows.append({"id": f"ev-{n:03d}", "term": term, "program_code": prog, "event": ev, "event_ur": ev_ur,
                     "start_date": D._d(start), "end_date": D._d(end) if end else None, "notes": notes,
                     "source_doc_ref": "Academic Calendar 2026-27"})
    for p in D.PROGRAMS:
        n += 1
        start = D.FIRST_SEMESTER_START[p["code"]]
        rows.append({"id": f"ev-{n:03d}", "term": "Fall 2026", "program_code": p["code"], "level": p["level"],
                     "event": f"Classes begin — {p['name']} 1st semester (new intake)",
                     "event_ur": f"{p['name_ur']} پہلے سمسٹر کی کلاسز کا آغاز",
                     "start_date": D._d(start), "end_date": None,
                     "notes": f"Shift: {p['shift']}. Orientation is on 29 October 2026.",
                     "source_doc_ref": "Academic Calendar 2026-27, Annex B"})
    return rows


def build_faculty() -> list[dict]:
    rows = []
    for i, (name, desig, dept, progs, spec, qual, office) in enumerate(D.FACULTY, start=1):
        handle = name.replace("Dr. ", "").replace("Mr. ", "").replace("Ms. ", "").replace("Mrs. ", "")
        handle = ".".join(handle.lower().split()[:2])
        rows.append({"id": f"fac-{i:02d}", "name": name, "designation": desig, "department_id": dept,
                     "program_codes": progs, "email": f"{handle}@uaea.edu.pk", "office": office,
                     "office_hours": ["Mon & Wed 11:30–13:00", "Tue & Thu 10:00–11:30", "Mon–Thu 14:00–15:00"][i % 3],
                     "specialization": spec, "qualification": qual})
    return rows


# ── main ──────────────────────────────────────────────────────────────────────

async def _add_all(db: AsyncSession, model, rows: list[dict]) -> None:
    for r in rows:
        db.add(model(**r))
    await db.flush()


async def clear_all(db: AsyncSession) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(text(f"DELETE FROM {table.name}"))
    await db.flush()


async def seed_all(db: AsyncSession, *, commit: bool = True) -> dict[str, int]:
    """Wipe every table and insert the full demo dataset. Returns row counts."""
    rng = random.Random(2026)
    await clear_all(db)

    faculty = build_faculty()
    courses = build_courses(faculty)
    timetable = build_timetable(courses, {f["id"]: f for f in faculty})
    students = build_students(rng)
    results, fee_records, attendance = build_records(students, courses, rng)

    # Advisors: a teacher of the student's programme
    for s in students:
        teachers = [f for f in faculty if s["program_code"] in f["program_codes"]]
        s["advisor_id"] = teachers[sum(map(ord, s["roll_number"])) % len(teachers)]["id"] if teachers else None

    programs = []
    for p in D.PROGRAMS:
        row = {k: v for k, v in p.items() if k not in ("fee_new", "prefix")}
        row["id"] = f"prg-{p['code'].lower()}"
        row["source_doc_ref"] = "Prospectus 2026-27 §5"
        row["description"] = (f"{p['name']} is a {p['duration_years']:g}-year {p['level'].lower()} programme "
                              f"({p['semesters']} semesters, {p['credit_hours']} credit hours) offered by the {p['faculty']}.")
        programs.append(row)

    await _add_all(db, Contact, D.CONTACTS)
    await _add_all(db, Campus, D.CAMPUSES)
    await _add_all(db, Department, D.DEPARTMENTS)
    await _add_all(db, FeeTariff, build_fee_tariffs())
    await _add_all(db, Service, D.SERVICES)
    await _add_all(db, Deadline, D.DEADLINES)
    await _add_all(db, Program, programs)
    await _add_all(db, AcademicEvent, build_events())
    await _add_all(db, Faculty, faculty)
    await _add_all(db, Course, courses)
    await _add_all(db, ClassSchedule, timetable)
    await _add_all(db, Scholarship, D.SCHOLARSHIPS)
    await _add_all(db, Hostel, D.HOSTELS)
    await _add_all(db, TransportRoute, D.TRANSPORT_ROUTES)
    await _add_all(db, Student, students)
    await _add_all(db, ResultRecord, results)
    await _add_all(db, FeeRecord, fee_records)
    await _add_all(db, AttendanceRecord, attendance)
    await _add_all(db, KnowledgeChunk, D.KNOWLEDGE_CHUNKS)
    await _add_all(db, UnansweredQuery, UNANSWERED)

    if commit:
        await db.commit()

    return {
        "contacts": len(D.CONTACTS), "campuses": len(D.CAMPUSES), "departments": len(D.DEPARTMENTS),
        "programs": len(programs), "fee_tariffs": len(build_fee_tariffs()), "services": len(D.SERVICES),
        "deadlines": len(D.DEADLINES), "academic_events": len(build_events()), "faculty": len(faculty),
        "courses": len(courses), "timetable_slots": len(timetable), "scholarships": len(D.SCHOLARSHIPS),
        "hostels": len(D.HOSTELS), "transport_routes": len(D.TRANSPORT_ROUTES), "students": len(students),
        "result_records": len(results), "fee_records": len(fee_records), "attendance_records": len(attendance),
        "knowledge_chunks": len(D.KNOWLEDGE_CHUNKS),
    }


UNANSWERED = [
    {"id": "uq-01", "text": "BS CS ki fees per semester kitni hai agar main repeat course le raha hoon", "intent": "fee_tariff", "confidence": 0.41, "count": 34, "reason": "Low classifier confidence"},
    {"id": "uq-02", "text": "assignment late jama karwane pe kitna fine hai", "intent": "assignments", "confidence": 0.55, "count": 47, "reason": "Tool returned no data"},
    {"id": "uq-03", "text": "scholarship ka result kab announce hoga Fall 2026", "intent": "scholarships", "confidence": 0.63, "count": 25, "reason": "Stale source document"},
]


async def _embed_chunks_if_configured(db: AsyncSession) -> None:
    """If a real embedding key is set and we're on Postgres, embed the knowledge chunks."""
    if settings.embedding_api_key in ("", "sk-REPLACE-ME") or settings.database_url.startswith("sqlite"):
        return
    try:
        from sqlalchemy import select
        from app.rag.ingest import get_embedding
        rows = (await db.execute(select(KnowledgeChunk))).scalars().all()
        for r in rows:
            r.embedding = await get_embedding(r.text)
        await db.commit()
        print(f"Embedded {len(rows)} knowledge chunks.")
    except Exception as e:  # embeddings are optional — keyword search still works
        print(f"Skipping embeddings: {e}")


async def main(create_tables: bool = False) -> None:
    from app.db.session import async_session, engine

    if create_tables:
        async with engine.begin() as conn:
            if not settings.database_url.startswith("sqlite"):
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        counts = await seed_all(db)
        await _embed_chunks_if_configured(db)
    await engine.dispose()
    print("Seeded database:")
    for k, v in counts.items():
        print(f"  {k:<20} {v}")
    print(f"All student records use WhatsApp number {settings.demo_student_phone}.")
    print("Demo roll numbers: " + ", ".join(r[0] + f" ({r[1]})" for r in DEMO_STUDENTS[:6]) + ", …")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the UAEA demo database")
    parser.add_argument("--create-tables", action="store_true", help="create tables before seeding (SQLite/local)")
    args = parser.parse_args()
    asyncio.run(main(create_tables=args.create_tables))
