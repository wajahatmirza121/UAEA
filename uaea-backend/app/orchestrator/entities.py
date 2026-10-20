"""Entity extraction: roll numbers, OTP codes, programmes, semesters, terms.

Used by the tools (to resolve fuzzy arguments the LLM passes) and by the
offline engine (which has no LLM to do the understanding).
"""

from __future__ import annotations

import re

from app.orchestrator.normalizer import normalise

# Programme codes known to the roll-number format (kept in sync with seed_data)
PROGRAM_CODES = ["BSCS", "BSSE", "BSIT", "BSAI", "BBA", "BSMATH", "BSENG", "BSPSY", "BSECO", "BSPHY",
                 "BSCHEM", "BSEDU", "BED15", "MAURDU", "MSCMATH", "MBA", "MSCS", "MPHILEDU", "PHDCS"]

_ROLL_RE = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(sorted(PROGRAM_CODES, key=len, reverse=True)) + r")"
    r"\s*[-_/ ]?\s*(20\d\d)\s*[-_/ ]\s*(\d{1,3})(?!\d)",
    re.IGNORECASE,
)
_OTP_RE = re.compile(r"(?<![\d-])(\d{3})[\s-]?(\d{3})(?![\d-])")

_ORDINALS = {
    "first": 1, "1st": 1, "pehla": 1, "pehle": 1, "pehli": 1, "pahla": 1,
    "second": 2, "2nd": 2, "doosra": 2, "dusra": 2, "doosre": 2, "dusre": 2,
    "third": 3, "3rd": 3, "teesra": 3, "tisra": 3, "teesre": 3,
    "fourth": 4, "4th": 4, "chotha": 4, "chautha": 4, "chothe": 4,
    "fifth": 5, "5th": 5, "panchwan": 5, "panchwen": 5, "paanchwan": 5,
    "sixth": 6, "6th": 6, "chatha": 6, "chhata": 6, "chate": 6,
    "seventh": 7, "7th": 7, "satwan": 7, "satwen": 7,
    "eighth": 8, "8th": 8, "aathwan": 8, "athwan": 8, "aathwen": 8,
}
_SEM_RE = re.compile(r"\b(?:semester|sem|smester|samester)\s*(?:no\.?\s*)?(\d)\b|\b(\d)\s*(?:st|nd|rd|th)?\s*(?:semester|sem|smester|samester)\b")
_TERM_RE = re.compile(r"\b(fall|autumn|spring|summer)\s*[-']?\s*(20\d\d|\d\d)\b", re.IGNORECASE)

# Aliases used to spot a programme in free text. Longest first wins.
PROGRAM_ALIASES: dict[str, list[str]] = {
    "BSCS": ["bs computer science", "bscs", "bs cs", "bs-cs", "computer science", "کمپیوٹر سائنس"],
    "BSSE": ["bs software engineering", "software engineering", "bsse", "bs se", "سافٹ ویئر"],
    "BSIT": ["bs information technology", "information technology", "bsit", "bs it"],
    "BSAI": ["bs artificial intelligence", "artificial intelligence", "bsai", "bs ai"],
    "BBA": ["bba hons", "business administration", "bba"],
    "BSMATH": ["bs mathematics", "bs maths", "bs math", "bsmath"],
    "BSENG": ["bs english", "bseng", "english literature"],
    "BSPSY": ["bs psychology", "psychology", "bspsy", "nafsiyat"],
    "BSECO": ["bs economics", "economics", "bseco"],
    "BSPHY": ["bs physics", "physics", "bsphy"],
    "BSCHEM": ["bs chemistry", "chemistry", "bschem"],
    "BSEDU": ["bs education", "bsedu", "bs edu", "b.ed 4 year", "bed 4 year"],
    "BED15": ["b.ed 1.5", "bed 1.5", "b.ed", "b ed", "bed 1.5 year"],
    "MAURDU": ["ma urdu", "maurdu"],
    "MSCMATH": ["msc mathematics", "msc maths", "msc math", "mscmath"],
    "MBA": ["mba"],
    "MSCS": ["ms computer science", "ms cs", "mscs"],
    "MPHILEDU": ["mphil education", "m.phil education", "mphil edu"],
    "PHDCS": ["phd computer science", "phd cs", "phdcs"],
}
# Two-letter shorthands only count when written in capitals ("CS", "IT", "AI", "SE"),
# so English words like "it" don't turn into BS IT.
_SHORT_CAPS = {"CS": "BSCS", "SE": "BSSE", "IT": "BSIT", "AI": "BSAI"}


def find_roll_numbers(text: str) -> list[str]:
    out = []
    for m in _ROLL_RE.finditer(text or ""):
        roll = f"{m.group(1).upper()}-{m.group(2)}-{int(m.group(3)):03d}"
        if roll not in out:
            out.append(roll)
    return out


def normalise_roll(value: str) -> str | None:
    rolls = find_roll_numbers(value or "")
    return rolls[0] if rolls else None


def find_otp_code(text: str) -> str | None:
    """A bare 6-digit code (optionally '123 456' or '123-456'), not part of a roll number."""
    stripped = _ROLL_RE.sub(" ", text or "")
    m = _OTP_RE.search(stripped)
    return (m.group(1) + m.group(2)) if m else None


def find_program(text: str) -> str | None:
    if not text:
        return None
    t = " " + normalise(text) + " "
    raw = text
    best: tuple[int, str] | None = None
    for code, aliases in PROGRAM_ALIASES.items():
        for a in aliases:
            a_n = normalise(a)
            if re.search(r"(?<![a-z0-9])" + re.escape(a_n) + r"(?![a-z0-9])", t) or (a in raw and not a.isascii()):
                if best is None or len(a_n) > best[0]:
                    best = (len(a_n), code)
    if best:
        return best[1]
    for short, code in _SHORT_CAPS.items():
        if re.search(r"(?<![A-Za-z])" + short + r"(?![A-Za-z])", raw):
            return code
    # programme code typed directly, e.g. "MSCS"
    for code in PROGRAM_CODES:
        if re.search(r"(?<![a-z0-9])" + code.lower() + r"(?![a-z0-9])", t):
            return code
    return None


def find_semester_no(text: str) -> int | None:
    t = normalise(text or "")
    m = _SEM_RE.search(t)
    if m:
        return int(m.group(1) or m.group(2))
    for word, n in _ORDINALS.items():
        if re.search(r"\b" + re.escape(word) + r"\b\s*(?:semester|sem|smester|samester)", t):
            return n
    return None


def find_term(text: str) -> str | None:
    m = _TERM_RE.search(text or "")
    if not m:
        return None
    season = m.group(1).lower()
    season = {"autumn": "Fall"}.get(season, season.capitalize())
    year = m.group(2)
    if len(year) == 2:
        year = "20" + year
    return f"{season} {year}"


def find_campus(text: str) -> str | None:
    t = normalise(text or "")
    for name, cid in [("islamabad", "camp-01"), ("rawalpindi", "camp-02"), ("pindi", "camp-02"),
                      ("lahore", "camp-03"), ("karachi", "camp-04"), ("peshawar", "camp-05"),
                      ("multan", "camp-06"), ("faisalabad", "camp-07"), ("quetta", "camp-08")]:
        if name in t:
            return cid
    for ur, cid in [("اسلام آباد", "camp-01"), ("راولپنڈی", "camp-02"), ("لاہور", "camp-03"),
                    ("کراچی", "camp-04"), ("پشاور", "camp-05"), ("ملتان", "camp-06"),
                    ("فیصل آباد", "camp-07"), ("کوئٹہ", "camp-08")]:
        if ur in (text or ""):
            return cid
    return None


def find_gender(text: str) -> str | None:
    t = normalise(text or "")
    if re.search(r"\b(girls?|female|larki|larkiyon|ladies|women)\b", t) or "لڑکیوں" in (text or ""):
        return "Female"
    if re.search(r"\b(boys?|male|larke|larkon|men)\b", t) or "لڑکوں" in (text or ""):
        return "Male"
    return None
