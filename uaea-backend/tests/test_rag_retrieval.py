"""Tests for RAG retrieval — verifies chunk search works with seeded data."""

import pytest
from unittest.mock import AsyncMock, patch

from app.orchestrator.tools import (
    tool_get_department, tool_get_fee_tariff,
    tool_get_deadline, tool_get_document_checklist,
)


@pytest.mark.asyncio
async def test_tool_get_department(seeded_db):
    """tool_get_department returns the right department for a name query."""
    result = await tool_get_department(seeded_db, "Admission")
    assert "error" not in result
    assert result["name_en"] == "Directorate of Admissions"
    assert result["category"] == "Admissions"


@pytest.mark.asyncio
async def test_tool_get_department_by_region(seeded_db):
    """tool_get_department can find departments by region."""
    result = await tool_get_department(seeded_db, "Islamabad")
    assert "error" not in result
    assert "Islamabad" in result.get("campus", "")


@pytest.mark.asyncio
async def test_tool_get_department_not_found(seeded_db):
    """tool_get_department returns error for unknown department."""
    result = await tool_get_department(seeded_db, "NonexistentDepartment12345")
    assert "error" in result


@pytest.mark.asyncio
async def test_tool_get_fee_tariff(seeded_db):
    """tool_get_fee_tariff returns the correct fee for a program."""
    result = await tool_get_fee_tariff(seeded_db, "BS Computer Science")
    assert "error" not in result
    assert result["amount"] == 28500
    assert result["currency"] == "PKR"


@pytest.mark.asyncio
async def test_tool_get_fee_tariff_with_category(seeded_db):
    """tool_get_fee_tariff filters by category."""
    result = await tool_get_fee_tariff(seeded_db, "BS Computer Science", "repeat")
    assert "error" not in result
    assert result["amount"] == 2150


@pytest.mark.asyncio
async def test_tool_get_fee_tariff_not_found(seeded_db):
    """tool_get_fee_tariff returns error for unknown program."""
    result = await tool_get_fee_tariff(seeded_db, "NonexistentProgram12345")
    assert "error" in result


@pytest.mark.asyncio
async def test_tool_get_deadline(seeded_db):
    """tool_get_deadline returns the right deadline for a service."""
    result = await tool_get_deadline(seeded_db, "Admission")
    assert "error" not in result
    assert result["date"] == "2026-09-30"


@pytest.mark.asyncio
async def test_tool_get_deadline_not_found(seeded_db):
    """tool_get_deadline returns error for unknown service."""
    result = await tool_get_deadline(seeded_db, "NonexistentService12345")
    assert "error" in result


@pytest.mark.asyncio
async def test_tool_get_document_checklist(seeded_db):
    """tool_get_document_checklist returns the right checklist."""
    result = await tool_get_document_checklist(seeded_db, "Admission")
    assert "error" not in result
    assert result["service"] == "Admission & Enrolment"
    assert len(result["checklist"]) >= 2
    items_en = [item["en"] for item in result["checklist"]]
    assert any("CNIC" in item for item in items_en)


@pytest.mark.asyncio
async def test_tool_get_document_checklist_degree(seeded_db):
    """tool_get_document_checklist works for Degree Application."""
    result = await tool_get_document_checklist(seeded_db, "Degree Application")
    assert "error" not in result
    assert len(result["checklist"]) >= 3


@pytest.mark.asyncio
async def test_tool_get_document_checklist_not_found(seeded_db):
    """tool_get_document_checklist returns error for unknown service."""
    result = await tool_get_document_checklist(seeded_db, "NonexistentService12345")
    assert "error" in result


@pytest.mark.asyncio
async def test_normalizer_folds_variants():
    """Roman Urdu spelling variants are folded correctly."""
    from app.orchestrator.normalizer import normalise

    assert "fee" in normalise("fis kitni hai")
    assert "admission" in normalise("admishan ka process")
    assert "challan" in normalise("challaan kahan banega")
    assert "result" in normalise("rizalt kab aayega")
    assert "degree" in normalise("degri ki darkhwast")


@pytest.mark.asyncio
async def test_language_detection():
    """Language detection correctly identifies Urdu, Roman Urdu, and English."""
    from app.orchestrator.normalizer import detect_language

    assert detect_language("کیا فیس کتنی ہے") == "ur"
    assert detect_language("fee kitni hai") == "roman"
    assert detect_language("What is the fee?") == "en"


@pytest.mark.asyncio
async def test_intent_classification():
    """Intent router classifies messages correctly."""
    from app.orchestrator.intent_router import classify

    assert classify("I want to apply for admission")["intent"] == "admission"
    assert classify("fee challan kahan banega")["intent"] == "fee_challan"
    assert classify("result kab aayega")["intent"] == "result"
    assert classify("degree ki darkhwast karna hai")["intent"] == "degree"
    assert classify("transcript chahiye")["intent"] == "transcript"
    assert classify("hello, how are you")["intent"] == "small_talk"
    assert classify("contact number kya hai")["intent"] == "department_lookup"
