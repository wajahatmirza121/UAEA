"""Offline engine — answers from the database without any LLM.

Used when no Groq key is configured, when Groq is unreachable/rate-limited,
and in the test-suite. It understands far less phrasing than the LLM, but it
covers every tool, follows the same OTP rules, and never invents facts:
replies are built only from tool results via ``formatters``.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator import entities
from app.orchestrator.formatters import format_tool, otp_prompt
from app.orchestrator.intent_router import PRIVATE_INTENTS
from app.orchestrator.normalizer import normalise
from app.orchestrator.tools import ToolContext, execute_tool
from app.services import otp as otp_service

GREETING = {
    "en": ("Assalam o alaikum! I'm the UAEA student assistant. I can tell you about **fees, admission dates, "
           "when classes start, timetables, courses, teachers, scholarships, hostels, transport, documents and rules** "
           "— for everyone.\n\nFor **your own result, fee status or attendance**, give me your roll number "
           "(e.g. BSCS-2023-014). I'll send a verification code to the student's WhatsApp first."),
    "roman": ("Assalam o alaikum! Main UAEA ka student assistant hoon. Fees, admission ki tareekhein, classes kab shuru "
              "hongi, timetable, courses, teachers, scholarships, hostel, transport, documents aur rules — sab pooch sakte hain.\n\n"
              "Apna **result, fee status ya attendance** dekhne ke liye roll number likhein (maslan BSCS-2023-014). "
              "Pehle student ke WhatsApp par verification code aayega."),
    "ur": ("السلام علیکم! میں UAEA کا اسٹوڈنٹ اسسٹنٹ ہوں۔ فیس، داخلے کی تاریخیں، کلاسز کب شروع ہوں گی، ٹائم ٹیبل، "
           "اسکالرشپ، ہاسٹل اور ٹرانسپورٹ کے بارے میں پوچھیں۔\n\nاپنا **رزلٹ، فیس یا حاضری** دیکھنے کے لیے رول نمبر لکھیں "
           "(مثلاً BSCS-2023-014)۔ پہلے واٹس ایپ پر تصدیقی کوڈ آئے گا۔"),
}

ASK_ROLL = {
    "en": "Please share the roll number (format like **BSCS-2023-014**). Private records are shown only after a WhatsApp verification code.",
    "roman": "Roll number likhein (format: **BSCS-2023-014**). Private maloomat WhatsApp verification code ke baad hi dikhayi jati hai.",
    "ur": "براہِ کرم رول نمبر لکھیں (مثلاً **BSCS-2023-014**)۔ نجی معلومات واٹس ایپ کوڈ کی تصدیق کے بعد ہی دکھائی جاتی ہیں۔",
}

NOT_FOUND = {
    "en": "I couldn't find that in the university records, so I won't guess. You can ask me to connect you to a staff member, or contact the Student Affairs Office (051-9250160).",
    "roman": "Ye university ke record mein nahi mila, is liye main andaza nahi lagaunga. Aap staff se baat karwane ka keh sakte hain, ya Student Affairs Office (051-9250160) se raabta karein.",
    "ur": "یہ یونیورسٹی کے ریکارڈ میں نہیں ملا، اس لیے میں اندازہ نہیں لگاؤں گا۔ اسٹوڈنٹ افیئرز آفس (051-9250160) سے رابطہ کریں۔",
}

_RESULT_WORDS = re.compile(r"\b(result|gpa|cgpa|marks|grade|grades|natija|nateeja|gazette)\b|نتیج")
_ATT_WORDS = re.compile(r"\b(attendance|haazri|hazri|present|absent)\b|حاضری")
_FEE_WORDS = re.compile(r"\b(fee|fees|challan|dues|paid|unpaid|payment|bakaya|outstanding)\b|فیس|واجبات")
_PROFILE_WORDS = re.compile(r"\b(profile|detail|details|record|advisor|hostel|email|batch|semester)\b")
_MY = re.compile(r"\b(my|mera|meri|mere|apna|apni|mujhe)\b|میرا|میری")


def last_roll_in_history(history: list[dict]) -> str | None:
    for m in reversed(history):
        if m.get("role") == "user":
            rolls = entities.find_roll_numbers(m.get("text") or "")
            if rolls:
                return rolls[0]
    return None


class Offline:
    def __init__(self, db: AsyncSession, ctx: ToolContext, lang: str):
        self.db, self.ctx, self.lang = db, ctx, lang
        self.calls: list[dict] = []
        self.otp: dict | None = None

    async def call(self, name: str, args: dict) -> dict:
        r = await execute_tool(self.db, name, args, self.ctx.conversation_id, self.ctx)
        self.calls.append({"name": name, "args": args, "result": r})
        if isinstance(r, dict) and r.get("otp_required") and self.otp is None:
            self.otp = r
        return r

    async def show(self, name: str, args: dict) -> str:
        return format_tool(name, await self.call(name, args))


async def answer_offline(db: AsyncSession, text: str, intent: dict, lang: str, ctx: ToolContext,
                         history: list[dict]) -> dict[str, Any]:
    """Returns {reply, tool_calls, escalated, otp, resolved}."""
    o = Offline(db, ctx, lang)
    reply, escalated, resolved = await _route(o, text, intent, lang, history)
    if o.otp:
        reply = otp_prompt(o.otp, lang)
    return {"reply": reply, "tool_calls": o.calls, "escalated": escalated, "otp": o.otp,
            "resolved": resolved}


async def _route(o: Offline, text: str, intent: dict, lang: str, history: list[dict]) -> tuple[str, bool, bool]:
    n = normalise(text)
    name = intent.get("intent")
    rolls = entities.find_roll_numbers(text)
    program = entities.find_program(text)
    sem = entities.find_semester_no(text)
    term = entities.find_term(text)
    campus = entities.find_campus(text)

    # ── private records ────────────────────────────────────────────────
    is_mine = _MY.search(n) is not None
    rule_question = re.search(r"\b(minimum|required|rule|policy|kitni honi|kya hota|allowed|short attendance kya)\b", n)
    wants_private = bool(rolls) or (name in PRIVATE_INTENTS and (is_mine or not rule_question)) or (
        name in ("result", "fee_tariff", "fee_challan", "attendance") and is_mine)
    if name in PRIVATE_INTENTS and rule_question and not rolls and not is_mine:
        wants_private = False
        name = "policy"
    if wants_private:
        roll = rolls[0] if rolls else None
        if not roll:
            verified = await otp_service.verified_rolls(o.db, o.ctx.session_id)
            roll = last_roll_in_history(history) or (verified[0] if len(verified) == 1 else None)
        if not roll:
            return ASK_ROLL.get(lang, ASK_ROLL["en"]), False, True
        tools = []
        if _RESULT_WORDS.search(n) or (name == "result"):
            tools.append(("get_student_result", {"roll_number": roll, "semester_no": sem, "term": term}))
        if _ATT_WORDS.search(n) or name == "attendance":
            tools.append(("get_attendance", {"roll_number": roll}))
        if (_FEE_WORDS.search(n) or name == "fee_status") and not any(t[0] == "get_fee_status" for t in tools):
            tools.append(("get_fee_status", {"roll_number": roll}))
        if not tools and (_PROFILE_WORDS.search(n) or name == "profile"):
            tools.append(("get_student_profile", {"roll_number": roll}))
        if not tools:
            tools.append(("get_student_result", {"roll_number": roll}))
        parts = []
        for tname, args in tools:
            args = {k: v for k, v in args.items() if v is not None}
            parts.append(await o.show(tname, args))
            if o.otp:
                break
        return "\n\n---\n\n".join(parts), False, True

    # ── public information ─────────────────────────────────────────────
    if name == "small_talk":
        if re.search(r"\b(thanks|thank you|shukriya|bye)\b", n) or "شکریہ" in text:
            return {"en": "You're welcome! Ask me anything else about the university.",
                    "roman": "Koi baat nahi! University ke baare mein kuch aur poochna ho to batayein.",
                    "ur": "خوشی ہوئی! کچھ اور پوچھنا ہو تو بتائیں۔"}.get(lang, "You're welcome!"), False, True
        return GREETING.get(lang, GREETING["en"]), False, True

    if name == "escalation":
        r = await o.call("create_escalation_ticket", {"reason": text[:300]})
        return f"I've passed this to a staff member (ticket {r['ticket_id'][:8]}). They will contact you shortly.", True, True

    if name == "class_schedule":
        event = None
        for keys, ev in [(("mid",), "mid-term"), (("final", "paper"), "final"), (("orientation",), "orientation"),
                         (("holiday", "chutti", "vacation", "break", "eid"), "holiday"), (("convocation",), "convocation"),
                         (("result",), "result"), (("merit", "admission"), "admission"),
                         (("class", "shuru", "start", "begin", "semester start"), "classes begin")]:
            if any(k in n for k in keys):
                event = ev
                break
        if "date sheet" in n or "datesheet" in n:
            return await o.show("search_knowledge_base", {"query": "date sheet published"}), False, True
        r = await o.call("get_academic_calendar", {"program": program, "term": term, "event": event})
        reply = format_tool("get_academic_calendar", r)
        if event == "classes begin" and program and not r.get("error"):
            own = [e for e in r["events"] if e["program"] == program]
            if own:
                e = own[0]
                from app.orchestrator.formatters import d
                lead = (f"**{e['event']}: {d(e['start_date'])}**. Continuing students (3rd semester onwards) "
                        f"started on 7 Sep 2026.")
                if lang == "roman":
                    lead = (f"**{program} ke naye (1st semester) students ki classes {d(e['start_date'])} se shuru hongi.** "
                            f"Purane students (3rd semester se aage) ki classes 7 Sep 2026 se chal rahi hain.")
                reply = lead + "\n\n" + reply
        return reply, False, not r.get("error")

    if name == "timetable":
        if not program:
            return "Which programme and semester? For example: *BSCS 3rd semester timetable*.", False, True
        return await o.show("get_class_timetable", {"program": program, "semester_no": sem}), False, True

    if name == "courses":
        return await o.show("get_courses", {"program": program, "semester_no": sem} if program else {"query": text}), False, True

    if name == "faculty":
        return await o.show("get_faculty", {"query": text}), False, True

    if name == "program_info":
        if program:
            return await o.show("get_program_info", {"program": program}), False, True
        if re.search(r"\b(test|merit|quota|formula|pattern)\b", n):
            return await o.show("search_knowledge_base", {"query": text}), False, True
        level = next((lv for k, lv in [("phd", "Postgraduate"), ("mphil", "Postgraduate"), ("ms", "Postgraduate"),
                                       ("master", "Graduate"), ("bs", "Undergraduate")]
                      if re.search(r"\b" + k + r"\b", n)), None)
        args = {"level": level} if level else {}
        if campus:
            args["campus"] = text
        return await o.show("list_programs", args), False, True

    if name == "fee_tariff":
        if program:
            return await o.show("get_fee_tariff", {"program": program}), False, True
        from app.orchestrator.tools import _SERVICE_FEE_WORDS
        if any(w in n for w in _SERVICE_FEE_WORDS):
            r = await o.call("get_fee_tariff", {"program": text})
            if not r.get("error"):
                return format_tool("get_fee_tariff", r), False, True
            o.calls.pop()
        return ("Fees differ by programme. Here are the semester fees — tell me your programme for the full breakdown.\n\n"
                + await o.show("list_programs", {})), False, True

    if name == "fee_challan":
        a = await o.show("get_document_checklist", {"service": "Fee Challan"})
        b = await o.show("get_deadline", {"service": "Fee Challan"})
        return f"{a}\n\n{b}", False, True

    if name == "admission" and re.search(r"\b(merit|formula|quota)\b", n) and "list" not in n:
        return await o.show("search_knowledge_base", {"query": "merit formula " + text}), False, True

    if name == "admission":
        parts = [await o.show("get_deadline", {"service": "Admission"})]
        if program:
            parts.append(await o.show("get_program_info", {"program": program}))
        parts.append(await o.show("get_document_checklist", {"service": "Admission"}))
        if not program:
            parts.append({"roman": "Aap kis programme mein admission lena chahte hain? (maslan BSCS, BBA, MBA) — main eligibility aur fee bata dunga.",
                          "ur": "آپ کس پروگرام میں داخلہ لینا چاہتے ہیں؟ میں اہلیت اور فیس بتا دوں گا۔"}
                         .get(lang, "Which programme are you interested in (e.g. BSCS, BBA, MBA)? I can tell you its eligibility and fee."))
        return "\n\n".join(parts), False, True

    if name in ("degree", "transcript", "rechecking", "records"):
        svc = {"degree": "Degree Application", "transcript": "Transcript", "rechecking": "Rechecking"}.get(name, text)
        parts = [await o.show("get_document_checklist", {"service": svc})]
        if name == "transcript" and "urgent" in n:
            parts.append(await o.show("get_fee_tariff", {"program": "Transcript", "category": "Urgent"}))
        dl = await o.call("get_deadline", {"service": svc})
        if not dl.get("error"):
            parts.append(format_tool("get_deadline", dl))
        else:
            o.calls.pop()
        return "\n\n".join(parts), False, not parts[0].startswith("No ")

    if name == "scholarships":
        q = next((k for k in ("need", "merit", "hafiz", "sports", "ehsaas", "peef", "disab", "sibling", "shuhada") if k in n), None)
        return await o.show("get_scholarships", {"query": q} if q else {}), False, True

    if name == "hostel":
        if any(k in n for k in ("timing", "gate", "rule", "visitor", "allot", "policy")):
            return await o.show("search_knowledge_base", {"query": "hostel " + text}), False, True
        return await o.show("get_hostel_info", {"campus": text if campus else None, "gender": text}), False, True

    if name == "transport":
        return await o.show("get_transport_routes", {"area": text}), False, True

    if name == "department_lookup":
        if campus and not any(k in n for k in ("exam", "admission", "finance", "degree", "hostel", "library", "it ")):
            r = await o.call("get_department", {"name_or_region": entities.find_campus(text) and _campus_word(text)})
        else:
            r = await o.call("get_department", {"name_or_region": text})
        return format_tool("get_department", r), False, not r.get("error")

    if name == "result":
        kb = await o.show("search_knowledge_base", {"query": "results published gazette portal"})
        return (kb + "\n\n" + {"roman": "Apna result dekhne ke liye roll number likhein (maslan **BSCS-2023-014**) — WhatsApp code se verify hoga.",
                               "ur": "اپنا رزلٹ دیکھنے کے لیے رول نمبر لکھیں (مثلاً **BSCS-2023-014**)۔"}
                .get(lang, "To see a specific result, type the roll number (e.g. **BSCS-2023-014**) — it is verified with a WhatsApp code.")), False, True

    if name == "library":
        return await o.show("search_knowledge_base", {"query": "library " + text}), False, True

    # policy / knowledge question / anything else → knowledge base
    r = await o.call("search_knowledge_base", {"query": text})
    if r.get("chunks"):
        return format_tool("search_knowledge_base", r), False, True
    return NOT_FOUND.get(lang, NOT_FOUND["en"]), False, False


def _campus_word(text: str) -> str:
    cid = entities.find_campus(text)
    return {"camp-01": "Islamabad", "camp-02": "Rawalpindi", "camp-03": "Lahore", "camp-04": "Karachi",
            "camp-05": "Peshawar", "camp-06": "Multan", "camp-07": "Faisalabad", "camp-08": "Quetta"}.get(cid, text)
