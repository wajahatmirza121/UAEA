"""Intent router — deterministic keyword classifier.

Used for analytics, routing cards in the UI, and by the offline engine when
the LLM is unavailable. With Groq enabled, the LLM decides which tools to
call; this classifier just labels the turn.

Keywords match at the start of a word ("enrol" matches "enrolment", "hi"
does NOT match inside "chahiye"). Urdu-script keywords match as substrings.
"""

from __future__ import annotations

import re

from app.orchestrator.normalizer import normalise

CONFIDENCE_FLOOR = 0.5
STRONG = 3
WEAK = 1

RULES = [
    {"intent": "fee_status", "label": "My fee status (private)", "service_id": "svc-02",
     "strong": ["fee status", "dues", "outstanding", "bakaya", "fee paid", "fee jama hui", "paid or not", "واجبات"],
     "weak": ["paid", "unpaid", "overdue", "pending", "my fee", "meri fee"]},
    {"intent": "fee_challan", "label": "Fee challan", "service_id": "svc-02",
     "strong": ["challan", "چالان"],
     "weak": ["bank", "jama", "deposit", "payment", "pay", "kahan", "banega", "generate", "1link", "بینک", "جمع", "ادائیگی"]},
    {"intent": "admission", "label": "Admission", "service_id": "svc-01",
     "strong": ["admission", "enrol", "enroll", "داخل", "اندراج"],
     "weak": ["apply", "last date", "date", "eligible", "eligibility", "merit", "درخواست", "اہلیت", "تاریخ"]},
    {"intent": "class_schedule", "label": "Academic calendar", "service_id": None,
     "strong": ["classes", "class start", "orientation", "calendar", "midterm", "mid term", "mid-term", "final exam",
                "finals", "date sheet", "datesheet", "holiday", "chutti", "chuttiyan", "vacation", "convocation",
                "semester start", "کلاس", "چھٹی", "امتحان"],
     "weak": ["shuru", "start", "begin", "kab", "when", "exam", "paper", "break", "eid", "شروع"]},
    {"intent": "timetable", "label": "Class timetable", "service_id": None,
     "strong": ["timetable", "time table", "class timing", "lecture timing", "routine", "ٹائم ٹیبل"],
     "weak": ["schedule", "room", "monday", "tuesday", "wednesday", "thursday", "friday", "lecture"]},
    {"intent": "courses", "label": "Courses / scheme of studies", "service_id": None,
     "strong": ["courses", "subjects", "scheme of studies", "syllabus", "course code", "مضامین"],
     "weak": ["course", "subject", "credit hours", "prerequisite", "parhaye"]},
    {"intent": "faculty", "label": "Faculty directory", "service_id": None,
     "strong": ["teacher", "professor", "faculty", "hod", "chairperson", "lecturer", "instructor", "ustad", "استاد"],
     "weak": ["sir", "madam", "dr", "who teaches", "kaun parhata", "head of"]},
    {"intent": "program_info", "label": "Programmes", "service_id": "svc-01",
     "strong": ["eligibility", "eligible", "programs", "programmes", "seats", "entry test", "duration", "پروگرام"],
     "weak": ["offer", "kaun se", "which program", "bs", "ms", "mphil", "phd", "test", "requirement"]},
    {"intent": "result", "label": "Result", "service_id": "svc-03",
     "strong": ["result", "نتیج", "نتائج", "gazette", "gpa", "cgpa", "grades"],
     "weak": ["marks", "grade", "announce", "pass", "fail", "نمبر", "اعلان"]},
    {"intent": "attendance", "label": "Attendance (private)", "service_id": None,
     "strong": ["attendance", "haazri", "hazri", "حاضری"],
     "weak": ["short", "present", "absent", "percent"]},
    {"intent": "profile", "label": "Student profile (private)", "service_id": None,
     "strong": ["profile", "my details", "mera record", "my record", "advisor", "enrolment status"],
     "weak": ["details", "record", "batch", "section"]},
    {"intent": "degree", "label": "Degree application", "service_id": "svc-04",
     "strong": ["degree", "ڈگری"],
     "weak": ["apply", "issue", "graduate", "درخواست", "اجرا"]},
    {"intent": "transcript", "label": "Transcript", "service_id": "svc-05",
     "strong": ["transcript", "prc", "ٹرانسکرپٹ"],
     "weak": ["urgent", "normal", "copy", "ارجنٹ"]},
    {"intent": "rechecking", "label": "Paper rechecking", "service_id": "svc-06",
     "strong": ["recheck", "rechecking", "re-check", "dobara jaanch", "دوبارہ جانچ"],
     "weak": ["paper", "marks kam"]},
    {"intent": "records", "label": "Records & certificates", "service_id": "svc-08",
     "strong": ["noc", "migration", "bonafide", "character certificate", "correction", "id card", "student card",
                "freeze", "add drop", "withdraw", "این او سی"],
     "weak": ["certificate", "name change", "lost", "duplicate"]},
    {"intent": "scholarships", "label": "Scholarships", "service_id": "svc-12",
     "strong": ["scholarship", "financial aid", "concession", "ehsaas", "peef", "وظیف"],
     "weak": ["discount", "need based", "merit", "hafiz", "sports quota", "free"]},
    {"intent": "hostel", "label": "Hostel", "service_id": "svc-11",
     "strong": ["hostel", "ہاسٹل", "warden"],
     "weak": ["mess", "room", "stay", "rehna", "accommodation"]},
    {"intent": "transport", "label": "Transport", "service_id": "svc-16",
     "strong": ["transport", "bus", "route", "van", "point", "ٹرانسپورٹ"],
     "weak": ["pick", "drop", "stop", "timing"]},
    {"intent": "library", "label": "Library", "service_id": "svc-17",
     "strong": ["library", "لائبریری"],
     "weak": ["book", "kitab", "borrow"]},
    {"intent": "fee_tariff", "label": "Fee amount", "service_id": "svc-01",
     "strong": ["fee", "tariff", "فیس", "dues structure"],
     "weak": ["kitni", "semester", "amount", "rupay", "paisa", "cost", "charges", "price", "رقم", "سمسٹر"]},
    {"intent": "policy", "label": "Rules & policies", "service_id": None,
     "strong": ["rule", "policy", "grading", "probation", "plagiarism", "refund", "installment", "dress code",
                "quota", "merit formula", "credit transfer", "summer semester", "dean's list"],
     "weak": ["allowed", "ijazat", "kya hota", "penalty", "fine"]},
    {"intent": "department_lookup", "label": "Contact a department", "service_id": None,
     "strong": ["contact", "phone", "number", "campus", "office", "email", "رابط", "کیمپس"],
     "weak": ["islamabad", "rawalpindi", "lahore", "karachi", "peshawar", "multan", "faisalabad", "quetta",
              "timing", "hours", "address", "اوقات", "نمبر"]},
    {"intent": "escalation", "label": "Talk to a person", "service_id": None,
     "strong": ["human", "staff member", "complaint", "talk to someone", "real person", "insaan", "شکایت"],
     "weak": ["help", "madad"]},
    {"intent": "small_talk", "label": "Small talk", "service_id": None,
     "strong": ["hello", "hi", "hey", "salam", "assalam", "aoa", "شکریہ", "thanks", "thank you", "shukriya", "bye", "السلام"],
     "weak": ["how are you", "kaise ho", "good morning", "who are you", "kaun ho"]},
]

# Kept for backwards compatibility (old guided-flow feature).
GUIDED_FLOW_INTENTS = {"admission", "fee_challan", "degree"}
PRIVATE_INTENTS = {"fee_status", "attendance", "profile"}

_cache: dict[str, re.Pattern] = {}


def _hit(keyword: str, text: str) -> bool:
    if not keyword.isascii():
        return keyword in text
    pat = _cache.get(keyword)
    if pat is None:
        # Short keywords must match a whole word ("pass" ≠ "password");
        # longer ones may be a word prefix ("enrol" → "enrolment").
        tail = r"(?![a-z0-9])" if len(keyword) <= 4 else ""
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + tail)
        _cache[keyword] = pat
    return bool(pat.search(text))


def classify(text: str) -> dict:
    """Classify user text into an intent with confidence score."""
    t = normalise(text)
    if not t:
        return {"intent": None, "label": "empty", "confidence": 0.0, "service_id": None, "matched": []}

    scored = []
    for rule in RULES:
        matched = [k for k in rule["strong"] if _hit(k, t)]
        strong_hits = len(matched)
        weak = [k for k in rule["weak"] if _hit(k, t)]
        score = strong_hits * STRONG + len(weak) * WEAK
        scored.append({**rule, "score": score, "strong_hits": strong_hits, "matched": matched + weak})

    # Stable sort keeps RULES order as the tie-breaker.
    scored.sort(key=lambda r: (-r["score"], -r["strong_hits"]))
    top = scored[0]

    if top["score"] == 0:
        return {"intent": "knowledge_question", "label": "Knowledge question",
                "confidence": 0.3, "service_id": None, "matched": []}

    return {
        "intent": top["intent"],
        "label": top["label"],
        "confidence": min(0.96, top["score"] / 6),
        "service_id": top["service_id"],
        "matched": sorted(set(top["matched"])),
    }
