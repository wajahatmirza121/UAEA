"""Tests for guardrails — verify ungrounded claims are stripped."""

import pytest
from app.orchestrator.guardrails import check_reply, extract_grounded_values, GuardrailResult


def test_grounded_number_passes():
    """A fee amount backed by a tool call should pass through unchanged."""
    tool_calls = [
        {"name": "get_fee_tariff", "args": {"program": "BS CS"}, "result": {
            "program": "BS Computer Science",
            "amount": 28500,
            "currency": "PKR",
            "source": "Fee Circular A-26",
        }},
    ]
    reply = "The semester fee is Rs 28500 for BS Computer Science."
    result = check_reply(reply, tool_calls)
    assert result.cleaned_reply == reply
    assert not result.was_modified


def test_ungrounded_number_stripped():
    """A fee amount with no backing tool call should be flagged and stripped."""
    tool_calls = []
    reply = "The fee is Rs 50000 per semester."
    result = check_reply(reply, tool_calls)
    assert result.was_modified
    assert "50000" not in result.cleaned_reply
    assert len(result.flags) >= 1
    assert result.flags[0].kind == "ungrounded_number"


def test_ungrounded_date_stripped():
    """A date with no backing tool call should be flagged and stripped."""
    tool_calls = []
    reply = "The deadline is 30-09-2026 for admission."
    result = check_reply(reply, tool_calls)
    assert result.was_modified
    assert "30-09-2026" not in result.cleaned_reply
    assert any(f.kind == "ungrounded_date" for f in result.flags)


def test_grounded_date_passes():
    """A date backed by a tool call should pass through."""
    tool_calls = [
        {"name": "get_deadline", "args": {"service": "Admission"}, "result": {
            "service": "Admission & Enrolment",
            "date": "2026-09-30",
            "source": "Admission Notice",
        }},
    ]
    reply = "The admission deadline is 2026-09-30."
    result = check_reply(reply, tool_calls)
    assert not result.was_modified


def test_multiple_ungrounded_replaces_all():
    """Multiple ungrounded claims (>2) should replace the entire reply."""
    tool_calls = []
    reply = "The fee is Rs 50000 and the deadline is 15-01-2027. You also need Rs 3000 for processing."
    result = check_reply(reply, tool_calls)
    assert result.was_modified
    assert "connect you to a human" in result.cleaned_reply.lower() or "unconfirmed" in result.cleaned_reply.lower()


def test_extract_grounded_values_nested():
    """Grounded value extraction should handle nested structures."""
    tool_calls = [
        {"name": "search_knowledge_base", "result": {
            "chunks": [
                {"text": "fee is Rs 28500", "amount": 28500},
                {"text": "deadline 2026-09-30", "date": "2026-09-30"},
            ],
        }},
    ]
    values = extract_grounded_values(tool_calls)
    assert "28500" in values
    assert "2026-09-30" in values


def test_no_flags_on_clean_reply():
    """A reply with no numbers or dates should pass cleanly."""
    result = check_reply("I can help you with that. What programme are you interested in?", [])
    assert not result.was_modified
    assert len(result.flags) == 0
