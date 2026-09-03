"""Roman Urdu / Urdu script normalizer.

Detects language and folds common Roman Urdu spelling variants before
intent matching. Keeps a small synonym/variant map, extensible.
"""

import re

# Spelling folds for Roman Urdu, applied before scoring
VARIANTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(fees|fis|phees|faees|feez)\b"), "fee"),
    (re.compile(r"\b(admision|admisn|admishan|admissn|dakhla|dakhila|dakhle)\b"), "admission"),
    (re.compile(r"\b(tareekh|tarikh|tarik|tareek)\b"), "date"),
    (re.compile(r"\b(kitna|kitne|kitni)\b"), "kitni"),
    (re.compile(r"\b(chalan|challaan|chalaan)\b"), "challan"),
    (re.compile(r"\b(rizalt|rizult|natija|nateeja)\b"), "result"),
    (re.compile(r"\b(transkript|transcrip|transcipt)\b"), "transcript"),
    (re.compile(r"\b(degri|digree|digri)\b"), "degree"),
    (re.compile(r"\b(asignment|assigment|asaainment)\b"), "assignment"),
    (re.compile(r"\b(sertificate|certifcate|certificat)\b"), "certificate"),
    (re.compile(r"\b(skolarship|wazifa|wazaif)\b"), "scholarship"),
    (re.compile(r"\b(migreshan|migresion)\b"), "migration"),
    (re.compile(r"\b(kaise|kesay|kese|kaisay)\b"), "kaise"),
    (re.compile(r"\b(kahan|kahaan|kidhar)\b"), "kahan"),
    (re.compile(r"\b(chahiye|chahye|chahiyay|chahie)\b"), "chahiye"),
]


def normalise(text: str) -> str:
    """Lower-case, strip punctuation, fold Roman Urdu variants."""
    t = (text or "").lower().strip()
    t = re.sub(r"[?!.،؟,]", " ", t)
    t = re.sub(r"\s+", " ", t)
    for pattern, replacement in VARIANTS:
        t = pattern.sub(replacement, t)
    return t


def detect_language(text: str) -> str:
    """Detect Urdu script vs Roman Urdu vs English."""
    if re.search(r"[\u0600-\u06FF]", text):
        return "ur"
    roman_markers = re.compile(
        r"\b(kya|kitni|kaise|kahan|hai|hain|ka|ki|ke|mujhe|mera|meri|"
        r"chahiye|nahi|kab|kar|karna|se|ko|par|bhi)\b"
    )
    if roman_markers.search(normalise(text)):
        return "roman"
    return "en"


def strip_injection(text: str) -> str:
    """Remove common prompt-injection patterns from user input."""
    # Strip instruction-like patterns
    patterns = [
        r"(ignore|disregard|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
        r"you are now\s+",
        r"new instructions?:\s*",
        r"system prompt:\s*",
        r"act as (a|an)\s+",
    ]
    cleaned = text
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()
