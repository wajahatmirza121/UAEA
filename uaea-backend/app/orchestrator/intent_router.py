"""Intent router — deterministic keyword classifier.

Classifies messages into: admission, fee_challan, result, degree, transcript,
department_lookup, small_talk, escalation. Rules-based, not ML.
"""

import re
from app.orchestrator.normalizer import normalise

CONFIDENCE_FLOOR = 0.5
STRONG = 3
WEAK = 1

RULES = [
    {
        "intent": "fee_challan", "label": "Fee challan", "service_id": "svc-02",
        "strong": ["challan", "fee challan", "چالان"],
        "weak": ["bank", "jama", "deposit", "payment", "pay", "kahan", "banega", "form",
                 "بینک", "جمع", "ادائیگی"],
    },
    {
        "intent": "fee_tariff", "label": "Fee amount", "service_id": "svc-01",
        "strong": ["fee", "tariff", "فیس"],
        "weak": ["kitni", "semester", "amount", "rupay", "paisa", "cost", "charges",
                 "رقم", "سمسٹر"],
    },
    {
        "intent": "admission", "label": "Admission", "service_id": "svc-01",
        "strong": ["admission", "enrol", "enroll", "داخل", "اندراج"],
        "weak": ["apply", "form", "last date", "date", "eligible", "eligibility",
                 "درخواست", "اہلیت", "تاریخ"],
    },
    {
        "intent": "result", "label": "Result", "service_id": "svc-03",
        "strong": ["result", "نتیج", "نتائج", "gazette"],
        "weak": ["marks", "grade", "gpa", "announce", "نمبر", "اعلان"],
    },
    {
        "intent": "degree", "label": "Degree application", "service_id": "svc-04",
        "strong": ["degree", "ڈگری"],
        "weak": ["apply", "issue", "convocation", "graduate", "درخواست", "اجرا"],
    },
    {
        "intent": "transcript", "label": "Transcript", "service_id": "svc-05",
        "strong": ["transcript", "prc", "ٹرانسکرپٹ"],
        "weak": ["urgent", "normal", "copy", "record", "ارجنٹ"],
    },
    {
        "intent": "department_lookup", "label": "Contact a department", "service_id": None,
        "strong": ["contact", "phone", "number", "campus", "office", "رابط", "کیمپس"],
        "weak": ["islamabad", "rawalpindi", "lahore", "karachi", "timing", "hours",
                 "address", "اوقات", "نمبر"],
    },
    {
        "intent": "small_talk", "label": "Small talk", "service_id": None,
        "strong": ["hello", "hi", "salam", "assalam", "شکریہ", "thanks", "bye"],
        "weak": ["how are you", "kaise ho", "السلام", "good morning"],
    },
]

# Guided flows that have full state machine support
GUIDED_FLOW_INTENTS = {"admission", "fee_challan", "degree"}


def classify(text: str) -> dict:
    """Classify user text into an intent with confidence score."""
    t = normalise(text)
    if not t:
        return {"intent": None, "label": "empty", "confidence": 0.0,
                "service_id": None, "matched": []}

    scored = []
    for rule in RULES:
        score = 0
        matched = []
        for k in rule["strong"]:
            if k in t:
                score += STRONG
                matched.append(k)
        for k in rule["weak"]:
            if k in t:
                score += WEAK
                matched.append(k)
        strong_hits = sum(1 for k in rule["strong"] if k in t)
        scored.append({**rule, "score": score, "strong_hits": strong_hits, "matched": matched})

    scored.sort(key=lambda r: (-r["score"], -r["strong_hits"]))
    top = scored[0]

    if not top or top["score"] == 0:
        return {"intent": "knowledge_question", "label": "Knowledge question",
                "confidence": 0.3, "service_id": None, "matched": []}

    confidence = min(0.96, top["score"] / 6)

    return {
        "intent": top["intent"],
        "label": top["label"],
        "confidence": confidence,
        "service_id": top["service_id"],
        "matched": list(set(top["matched"])),
    }
