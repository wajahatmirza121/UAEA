"""Deterministic Markdown formatting of tool results.

Used (a) by the offline engine when the LLM is unavailable and (b) to show
private records right after OTP verification — exact numbers, no paraphrase.
"""

from __future__ import annotations

import datetime
from typing import Any


def rs(n: Any) -> str:
    try:
        return f"Rs {int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def d(s: Any) -> str:
    if not s:
        return "—"
    try:
        x = datetime.date.fromisoformat(str(s)[:10])
        return x.strftime("%d %b %Y").lstrip("0")
    except ValueError:
        return str(s)


def _when(days: int | None) -> str:
    if days is None:
        return ""
    if days > 1:
        return f" (in {days} days)"
    if days == 1:
        return " (tomorrow)"
    if days == 0:
        return " (today)"
    return " (already passed)"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "/") for c in r) + " |")
    return "\n".join(out)


def otp_prompt(r: dict, lang: str = "en") -> str:
    if r.get("rate_limited"):
        return r.get("message", "Too many codes requested. Please try again later.")
    if r.get("delivery_failed"):
        return ("I couldn't deliver the verification code on WhatsApp just now. "
                "Type **resend** in a minute to try again.")
    who = f" ({r['student']})" if r.get("student") else ""
    mins = max(1, -(-int(r.get("expires_in_seconds", 300)) // 60))  # round up
    if lang == "roman":
        text = (f"🔒 **{r['roll_number']}**{who} ki maloomat private hai. Verification ke liye 6-digit code "
                f"WhatsApp par **{r['masked_phone']}** par bhej diya gaya hai. Code yahan chat mein likh dein "
                f"(code {mins} minute mein expire ho jayega).\n\nCode nahi mila? **resend** likhein. Cancel karne ke liye **cancel** likhein.")
    elif lang == "ur":
        text = (f"🔒 **{r['roll_number']}** کی معلومات نجی ہیں۔ تصدیق کے لیے 6 ہندسوں کا کوڈ واٹس ایپ نمبر "
                f"**{r['masked_phone']}** پر بھیج دیا گیا ہے۔ کوڈ یہاں چیٹ میں لکھیں ({mins} منٹ میں ختم ہو جائے گا)۔\n\n"
                f"کوڈ نہیں ملا؟ **resend** لکھیں۔")
    else:
        text = (f"🔒 Records for **{r['roll_number']}**{who} are private. I've sent a 6-digit verification code on "
                f"WhatsApp to **{r['masked_phone']}**. Type the code here in the chat to continue "
                f"(it expires in {mins} minutes).\n\nDidn't get it? Type **resend**. Type **cancel** to stop.")
    if r.get("dev_code"):
        text += f"\n\n_(Demo mode — code: **{r['dev_code']}**)_"
    return text


def fmt_result(r: dict) -> str:
    if r.get("otp_required"):
        return otp_prompt(r)
    if r.get("error"):
        extra = ("\nAvailable: " + ", ".join(r["available"])) if r.get("available") else ""
        return f"{r['error']}.{extra}"
    if r.get("message") and not r.get("courses"):
        return r["message"]
    head = (f"**Result — {r['name']} ({r['roll_number']})**\n"
            f"Semester {r['semester_no']} · {r['term']} · **GPA {r['gpa']:.2f}** · **CGPA {r['cgpa']:.2f}** · Status: {r['status']}")
    table = _table(["Code", "Course", "Cr.", "Marks", "Grade"],
                   [[c["code"], c["title"], c["credit_hours"], c["marks"], c["grade"]] for c in r["courses"]])
    tail = f"Published {d(r.get('published_on'))} · {r.get('source', '')}"
    others = r.get("other_semesters") or []
    if others:
        tail += "\n\nOther semesters: " + ", ".join(f"Sem {o['semester_no']} ({o['term']}) GPA {o['gpa']:.2f}" for o in others)
        tail += "\nAsk e.g. *“semester 3 result”* to see any of them."
    return f"{head}\n\n{table}\n\n{tail}"


def fmt_fee_status(r: dict) -> str:
    if r.get("otp_required"):
        return otp_prompt(r)
    if r.get("error"):
        return r["error"]
    c = r.get("current") or {}
    lines = [f"**Fee status — {r['name']} ({r['roll_number']})**"]
    if c:
        status = c["status"]
        icon = {"Paid": "✅", "Unpaid": "🟡", "Overdue": "🔴"}.get(status, "")
        lines.append(f"{c['term']}: {icon} **{status}** — challan {c['challan_no']}, amount {rs(c['amount'])}"
                     + (f" (scholarship discount {rs(c['scholarship_discount'])})" if c.get("scholarship_discount") else ""))
        lines.append(f"Due date: {d(c['due_date'])}"
                     + (f" · paid on {d(c['paid_on'])} via {c['bank']}" if c.get("paid_on") else ""))
        if c.get("late_fine"):
            lines.append(f"Late fine so far: {rs(c['late_fine'])} (Rs 500 per week)")
        if status != "Paid":
            lines.append(f"**Total payable now: {rs(c['total_payable'])}** — generate the challan from the portal and pay at any designated bank or via 1Link.")
    if r.get("history"):
        lines.append("\nPrevious semesters: " + ", ".join(f"{h['term']} {h['status']}" for h in r["history"]))
    lines.append(f"\nSource: {r.get('source')}")
    return "\n".join(lines)


def fmt_attendance(r: dict) -> str:
    if r.get("otp_required"):
        return otp_prompt(r)
    if r.get("error"):
        return r["error"]
    if not r.get("courses"):
        return r.get("message", "No attendance recorded.")
    short = [c for c in r["courses"] if c["short"]]
    table = _table(["Course", "Attended", "Total", "%"],
                   [[c["course"], c["attended"], c["total"], f"{c['percentage']}%" + (" ⚠️" if c["short"] else "")]
                    for c in r["courses"]])
    note = (f"\n\n⚠️ Below the 75% minimum in {len(short)} course(s). Students under 75% are not allowed to sit the final exam."
            if short else "\n\nAll courses are above the 75% minimum.")
    return (f"**Attendance — {r['name']} ({r['roll_number']}) · {r['term']}**\n"
            f"Overall: **{r['overall_percentage']}%** (updated {d(r.get('updated_on'))})\n\n{table}{note}")


def fmt_profile(r: dict) -> str:
    if r.get("otp_required"):
        return otp_prompt(r)
    if r.get("error"):
        return r["error"]
    cg = f"{r['cgpa']:.2f}" if r.get("cgpa") is not None else "— (no result yet)"
    return (f"**Student record — {r['name']} ({r['roll_number']})**\n"
            f"- Father's name: {r['father_name']}\n- Programme: {r['program']} · {r['batch']} · Section {r['section']}\n"
            f"- Current semester: {r['current_semester']} · Campus: {r['campus']}\n- Status: {r['status']} · CGPA: {cg}\n"
            f"- University email: {r['email']}\n- Advisor: {r['advisor']}\n- Hostel: {r['hostel']}")


def fmt_fee_tariff(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    lines = [f"**{r['program']}** — {r['category']}: **{rs(r['amount'])}** (effective {d(r['effective_from'])}) · {r['source']}"]
    for c in r.get("all_categories", [])[1:]:
        lines.append(f"- {c['category']}: {rs(c['amount'])}")
    if r.get("note"):
        lines.append(r["note"])
    return "\n".join(lines)


def fmt_deadline(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    if r.get("passed"):
        main = f"The last date for **{r['service']}** ({r['semester']}) was **{d(r['date'])}** — it has passed."
    else:
        main = f"The last date for **{r['service']}** ({r['semester']}) is **{d(r['date'])}**{_when(r.get('days_left'))}."
    others = [x for x in r.get("all_deadlines", []) if x["date"] != r["date"]]
    if others:
        main += "\n" + "\n".join(f"- {x['semester']}: {d(x['date'])}{' (passed)' if x['passed'] else ''}" for x in others)
    return main + f"\n\nSource: {r['source']}"


def fmt_calendar(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    rows = []
    for e in r["events"][:12]:
        when = d(e["start_date"]) + (f" – {d(e['end_date'])}" if e.get("end_date") else "")
        rows.append(f"- **{e['event']}** — {when}{_when(e.get('days_from_today')) if (e.get('days_from_today') or 0) >= 0 else ''}"
                    + (f"  \n  _{e['notes']}_" if e.get("notes") else ""))
    return "\n".join(rows) + f"\n\nSource: {r['source']}"


def fmt_timetable(r: dict) -> str:
    if r.get("error"):
        return r["error"] + (f" Timetables exist for semesters {r['semesters_with_timetable']}." if r.get("semesters_with_timetable") else "")
    if r.get("needs"):
        return (f"Which semester of **{r['program']}**? This term's timetable is available for semesters "
                f"{', '.join(map(str, r['semesters_with_timetable']))}.")
    table = _table(["Day", "Time", "Course", "Room", "Teacher"],
                   [[s["day"], s["time"], s["course"], s["room"], s["teacher"]] for s in r["slots"]])
    return f"**{r['program']} — semester {r['semester_no']} timetable ({r['term']}, section {r['section']})**\n\n{table}\n\nSource: {r['source']}"


def fmt_courses(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    table = _table(["Sem", "Code", "Course", "Cr.", "Teacher"],
                   [[c["semester"], c["code"], c["title"], c["credit_hours"], c["teacher"]] for c in r["courses"][:40]])
    title = f"**{r['program']} — courses**" if r.get("program") else "**Courses**"
    return f"{title}\n\n{table}\n\nSource: {r['source']}"


def fmt_program(r: dict) -> str:
    if r.get("error"):
        return r["error"] + (("\nProgrammes: " + ", ".join(r["available"])) if r.get("available") else "")
    fees = ", ".join(f"{f['category']} {rs(f['amount'])}" for f in r.get("fees", []))
    return (f"**{r['name']}** ({r['code']}) — {r['level']}, {r['faculty']}\n"
            f"- Duration: {r['duration_years']:g} years · {r['semesters']} semesters · {r['credit_hours']} credit hours\n"
            f"- Eligibility: {r['eligibility']}\n- Entry test: {r['entry_test']}\n"
            f"- Seats: {r['seats']} · Shift: {r['shift']}\n- Offered at: {', '.join(r['offered_at'])}\n"
            f"- Fee: {fees}\n"
            + (f"- 1st-semester classes begin: {d(r['first_semester_classes_begin'])}\n" if r.get("first_semester_classes_begin") else "")
            + f"\nSource: {r['source']}")


def fmt_programs(r: dict) -> str:
    rows = [[p["code"], p["name"], p["level"], f"{p['duration_years']:g} yr", rs(p["semester_fee_pkr"]) if p.get("semester_fee_pkr") else "—"]
            for p in r["programs"]]
    return f"**Programmes offered ({r['count']})**\n\n" + _table(["Code", "Programme", "Level", "Duration", "Semester fee"], rows) + f"\n\nSource: {r['source']}"


def fmt_checklist(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    items = "\n".join(f"{i}. {c['en']} — {'attested copy' if c.get('copy') else 'original'}" for i, c in enumerate(r["checklist"], 1))
    fee = f"\n\nFee: {rs(r['fee']['amount'])} ({r['fee']['category']})" if r.get("fee") else ""
    return f"**{r['service']}** — documents needed:\n{items}\n\n**How it works:** {r['procedure']}{fee}\n\nSource: {r['source']}"


def fmt_department(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    s = (f"**{r['name_en']}** ({r.get('name_ur') or ''})\n- Phone: {r.get('phone')}\n- Email: {r.get('email')}\n"
         f"- Office hours: {r.get('office_hours')}\n- Location: {r.get('campus')}, {r.get('address')}")
    if r.get("other_matches"):
        s += "\n\nAlso matching: " + ", ".join(r["other_matches"])
    return s


def fmt_campuses(r: dict) -> str:
    return "\n".join(f"- **{c['name']}** — {c['address']} · {c['phone']} · {c['email']}" for c in r["campuses"])


def fmt_faculty(r: dict) -> str:
    if r.get("error"):
        return r["error"]
    return "\n".join(f"- **{f['name']}** — {f['designation']}, {f['department']}  \n  {f['specialization']} · {f['email']} · "
                     f"{f['office']} · office hours {f['office_hours']}" for f in r["faculty"]) + f"\n\nSource: {r['source']}"


def fmt_scholarships(r: dict) -> str:
    out = []
    for s in r["scholarships"][:6]:
        dl = f" · deadline {d(s['deadline'])}" + (" (passed)" if s["deadline_passed"] else "") if s.get("deadline") else ""
        out.append(f"- **{s['name']}** ({s['type']}) — {s['coverage']}{dl}  \n  Eligibility: {s['eligibility']}  \n  Apply: {s['how_to_apply']}")
    return "\n".join(out) + f"\n\nSource: {r['source']}"


def fmt_hostels(r: dict) -> str:
    out = []
    for h in r["hostels"]:
        out.append(f"- **{h['name']}** ({h['campus']}) — {rs(h['fee_per_semester'])}/semester, mess about {rs(h['mess_fee_per_month'])}/month, "
                   f"{h['vacant_seats']} vacant seats  \n  {h['rooms']}; {', '.join(h['facilities'])}. Warden: {h['warden']} ({h['warden_phone']})")
    return "\n".join(out) + f"\n\nRefundable security deposit: {rs(r['security_deposit'])}. Source: {r['source']}"


def fmt_transport(r: dict) -> str:
    out = []
    for t in r["routes"]:
        out.append(f"- **{t['route']} {t['name']}** ({t['campus']}) — leaves {t['morning_departure']}, returns {t['return_from_campus']}, "
                   f"{rs(t['fee_per_semester'])}/semester  \n  Stops: {' → '.join(t['stops'])}")
    return "\n".join(out) + f"\n\nSource: {r['source']}"


def fmt_kb(r: dict) -> str:
    chunks = r.get("chunks") or []
    if not chunks:
        return ""
    out = [chunks[0]["text"]]
    for c in chunks[1:2]:
        if c["score"] >= 0.7:
            out.append(c["text"])
    src = ", ".join(sorted({f"{c['source_doc_id']} {c.get('section') or ''}".strip() for c in chunks[:2]}))
    return "\n\n".join(out) + f"\n\nSource: {src}"


FORMATTERS = {
    "get_student_result": fmt_result, "get_fee_status": fmt_fee_status, "get_attendance": fmt_attendance,
    "get_student_profile": fmt_profile, "get_fee_tariff": fmt_fee_tariff, "get_deadline": fmt_deadline,
    "get_academic_calendar": fmt_calendar, "get_class_timetable": fmt_timetable, "get_courses": fmt_courses,
    "get_program_info": fmt_program, "list_programs": fmt_programs, "get_document_checklist": fmt_checklist,
    "get_department": fmt_department, "list_campuses": fmt_campuses, "get_faculty": fmt_faculty,
    "get_scholarships": fmt_scholarships, "get_hostel_info": fmt_hostels, "get_transport_routes": fmt_transport,
    "search_knowledge_base": fmt_kb,
}


def format_tool(name: str, result: dict) -> str:
    if isinstance(result, dict) and result.get("otp_required"):
        return otp_prompt(result)
    f = FORMATTERS.get(name)
    if not f:
        return result.get("message") or result.get("error") or ""
    return f(result)
