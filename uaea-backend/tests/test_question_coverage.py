"""Many real-world questions → each must be answered from the database (offline engine, no LLM).

(question, tool that must be called, text that must appear in the reply)
"""

import pytest

CASES = [
    # classes / calendar
    ("BSCS ki classes kab sy shru hongi?", "get_academic_calendar", "2 Nov 2026"),
    ("When do BBA classes start?", "get_academic_calendar", "3 Nov 2026"),
    ("MBA ki classes kab start hongi", "get_academic_calendar", "7 Nov 2026"),
    ("mid term exams kab hain", "get_academic_calendar", "Mid-term"),
    ("final exams kab se hain?", "get_academic_calendar", "Final-term"),
    ("winter vacation kab hogi", "get_academic_calendar", "Winter break"),
    ("orientation kab hai", "get_academic_calendar", "29 Oct 2026"),
    ("convocation kab hai", "get_academic_calendar", "12 Dec 2026"),
    ("date sheet kab aayegi", "search_knowledge_base", "date sheet"),
    # fees
    ("BSCS ki fees kitni hai?", "get_fee_tariff", "28,500"),
    ("BBA fee per semester", "get_fee_tariff", "27,000"),
    ("MS CS ki fees", "get_fee_tariff", "48,000"),
    ("کمپیوٹر سائنس کی فیس کتنی ہے؟", "get_fee_tariff", "28,500"),
    ("urgent transcript ki fees kitni hai", "get_fee_tariff", "3,500"),
    ("fee kitni hai", "list_programs", "BS Computer Science"),
    ("Fee challan kahan se banega?", "get_document_checklist", "portal"),
    # admission / programmes
    ("Admission ki last date kya hai?", "get_deadline", "20 Jan 2027"),
    ("BSAI admission eligibility", "get_program_info", "60%"),
    ("kaun se programs offer hotay hain", "list_programs", "MBA"),
    ("Quetta campus mein kaun se programs hain", "list_programs", "BS Information Technology"),
    ("entry test ka pattern kya hai", "search_knowledge_base", "Mathematics 40%"),
    ("merit kaise banta hai", "search_knowledge_base", "Intermediate"),
    # timetable / courses / teachers
    ("BSCS 3rd semester timetable", "get_class_timetable", "Data Structures"),
    ("BSSE 2nd semester ke courses", "get_courses", "Object Oriented Programming"),
    ("who teaches natural language processing", "get_faculty", "Nadia Aslam"),
    ("computer science department ka HOD kaun hai", "get_faculty", "Imran Haider"),
    # services & documents
    ("ڈگری کے لیے کون سے کاغذات چاہییں؟", "get_document_checklist", "Degree"),
    ("NOC ke liye kya documents chahiye?", "get_document_checklist", "NOC"),
    ("migration certificate kaise milega", "get_document_checklist", "Migration"),
    ("Transcript apply karne ka tareeqa?", "get_document_checklist", "Transcript"),
    ("rechecking ki fees aur tareeqa", "get_document_checklist", "1,500"),
    ("semester freeze kaise karun", "get_document_checklist", "Freeze"),
    # campus life
    ("girls hostel fee Islamabad", "get_hostel_info", "Fatima Jinnah Hall"),
    ("Bahria se university bus route", "get_transport_routes", "Bahria"),
    ("scholarship kab tak apply kar sakte hain", "get_scholarships", "Need-Based"),
    ("hafiz e quran ko kya concession milta hai", "get_scholarships", "Hafiz"),
    ("library timings kya hain", "search_knowledge_base", "08:00"),
    # rules
    ("minimum attendance kitni honi chahiye", "search_knowledge_base", "75%"),
    ("refund policy kya hai agar main chor doon", "search_knowledge_base", "100%"),
    ("probation kya hota hai", "search_knowledge_base", "2.00"),
    ("grading scale kya hai", "search_knowledge_base", "85"),
    ("plagiarism policy", "search_knowledge_base", "Turnitin"),
    ("LMS ka password bhool gaya", "search_knowledge_base", "IT Help Desk"),
    # contacts
    ("Rawalpindi campus ka number chahiye", "get_department", "051-4567890"),
    ("Examination department contact", "get_department", "051-9250142"),
    ("hello", None, "roll number"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("question,tool,expected", CASES, ids=[c[0][:40] for c in CASES])
async def test_question_is_answered_from_db(client, question, tool, expected):
    r = await client.post("/v1/chat/message", json={"session_id": f"cov-{hash(question)}", "text": question})
    assert r.status_code == 200
    data = r.json()
    assert data["engine"] == "offline"
    called = [tc["name"] for tc in data["tool_calls"]]
    if tool:
        assert tool in called, f"{question!r}: expected {tool}, got {called}"
    assert expected.lower() in data["reply"].lower(), f"{question!r}: {data['reply'][:400]}"
    assert data["otp"] is None
