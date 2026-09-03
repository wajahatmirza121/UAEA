"""Guardrails — hallucination check / strip step.

After the LLM drafts a reply, this module scans it for numbers, dates,
and document requirements, then cross-checks each against the tool_call
results from the current turn. Untraceable claims are stripped or replaced.
"""

from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("guardrails")


@dataclass
class GuardrailFlag:
    kind: str          # ungrounded_number, ungrounded_date, ungrounded_requirement
    matched_text: str
    position: int


@dataclass
class GuardrailResult:
    cleaned_reply: str
    flags: list[GuardrailFlag] = field(default_factory=list)
    was_modified: bool = False


# Patterns that indicate factual claims requiring grounding
NUMBER_PATTERN = re.compile(
    r"\b(Rs\.?\s?\d[\d,]*)|"         # Rs 28,500
    r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:PKR|rupees?|روپے)\b|"  # 28500 PKR
    r"\b(\d{4,})\b"                   # bare 4+ digit numbers (likely fees/amounts)
)

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b|"  # 30-09-2026
    r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{2,4})\b|"
    r"\b(\d{4}-\d{2}-\d{2})\b"       # ISO dates
)

# Common phrases that indicate document requirements
REQUIREMENT_PATTERNS = [
    re.compile(r"(you (?:will )?need|must (?:provide|submit|attach)|required documents?|bring|carry)\s+.+", re.IGNORECASE),
]

ESCALATION_NOTE = "I don't have a confirmed answer for that detail — let me connect you to a human who can help."


def extract_grounded_values(tool_calls: list[dict]) -> set[str]:
    """Extract all string values from tool call results that can be used as grounding."""
    values: set[str] = set()

    for call in tool_calls:
        result = call.get("result", {})
        _extract_values(result, values)

    return values


def _extract_values(obj, values: set[str]):
    """Recursively extract string and numeric values from a result dict."""
    if isinstance(obj, dict):
        for v in obj.values():
            _extract_values(v, values)
    elif isinstance(obj, list):
        for item in obj:
            _extract_values(item, values)
    elif obj is not None:
        values.add(str(obj).strip().lower())


def check_reply(reply: str, tool_calls: list[dict]) -> GuardrailResult:
    """Scan an LLM reply for ungrounded claims and strip them.

    Returns a GuardrailResult with the cleaned reply and any flags raised.
    """
    grounded = extract_grounded_values(tool_calls)
    flags: list[GuardrailFlag] = []
    cleaned = reply

    # Check numbers
    for match in NUMBER_PATTERN.finditer(reply):
        num_text = match.group(0).replace(",", "").replace("Rs", "").replace("rs", "").replace(" ", "").strip()
        # Check if this number appears in any grounded value
        is_grounded = any(num_text in v for v in grounded)
        if not is_grounded:
            flags.append(GuardrailFlag("ungrounded_number", match.group(0), match.start()))

    # Check dates
    for match in DATE_PATTERN.finditer(reply):
        date_text = match.group(0)
        # Normalise the date for comparison
        normalised = date_text.replace("/", "-").lower()
        is_grounded = any(normalised in v or date_text.lower() in v for v in grounded)
        if not is_grounded:
            flags.append(GuardrailFlag("ungrounded_date", match.group(0), match.start()))

    # If we found ungrounded claims, replace them
    if flags:
        # Sort flags by position in reverse so replacements don't shift indices
        for flag in sorted(flags, key=lambda f: f.position, reverse=True):
            start = flag.position
            end = start + len(flag.matched_text)
            cleaned = cleaned[:start] + "[unconfirmed]" + cleaned[end:]

        # If too many ungrounded claims, replace entire reply
        if len(flags) > 2:
            cleaned = ESCALATION_NOTE

        for flag in flags:
            logger.warning(f"Guardrail: {flag.kind} — '{flag.matched_text}'")

    return GuardrailResult(
        cleaned_reply=cleaned,
        flags=flags,
        was_modified=len(flags) > 0,
    )
