"""Tests for lookup API endpoints — verifies seeded data is returned correctly."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient):
    """GET /v1/lookup/departments returns seeded departments."""
    resp = await client.get("/v1/lookup/departments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    names = [d["name_en"] for d in data]
    assert "Directorate of Admissions" in names
    assert "Examinations Department" in names


@pytest.mark.asyncio
async def test_list_departments_by_region(client: AsyncClient):
    """GET /v1/lookup/departments?region=Islamabad filters correctly."""
    resp = await client.get("/v1/lookup/departments", params={"region": "Islamabad"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for dept in data:
        assert dept["region"]["region"] == "Islamabad"


@pytest.mark.asyncio
async def test_list_departments_by_query(client: AsyncClient):
    """GET /v1/lookup/departments?query=Admission finds the right dept."""
    resp = await client.get("/v1/lookup/departments", params={"query": "Admission"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert "Admission" in data[0]["name_en"]


@pytest.mark.asyncio
async def test_list_fee_tariffs(client: AsyncClient):
    """GET /v1/lookup/fee-tariff returns seeded fee tariffs."""
    resp = await client.get("/v1/lookup/fee-tariff")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    programs = [f["program"] for f in data]
    assert "BS Computer Science" in programs


@pytest.mark.asyncio
async def test_list_fee_tariffs_by_program(client: AsyncClient):
    """GET /v1/lookup/fee-tariff?program=BS Computer Science filters correctly."""
    resp = await client.get("/v1/lookup/fee-tariff", params={"program": "BS Computer Science"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for fee in data:
        assert "BS Computer Science" in fee["program"]
    # Check the specific amount is correct
    amounts = {f["category"]: f["amount"] for f in data}
    assert amounts.get("Semester (new)") == 28500


@pytest.mark.asyncio
async def test_list_deadlines(client: AsyncClient):
    """GET /v1/lookup/deadlines returns seeded deadlines."""
    resp = await client.get("/v1/lookup/deadlines")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_list_deadlines_by_service(client: AsyncClient):
    """GET /v1/lookup/deadlines?service=Admission filters correctly."""
    resp = await client.get("/v1/lookup/deadlines", params={"service": "Admission"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["date"] == "2026-09-30"


@pytest.mark.asyncio
async def test_document_checklist(client: AsyncClient):
    """GET /v1/lookup/document-checklist?service=Admission returns the right checklist."""
    resp = await client.get("/v1/lookup/document-checklist", params={"service": "Admission"})
    assert resp.status_code == 200
    data = resp.json()
    assert "checklist" in data
    assert len(data["checklist"]) >= 2
    items_en = [item["en"] for item in data["checklist"]]
    assert any("CNIC" in item for item in items_en)


@pytest.mark.asyncio
async def test_document_checklist_degree(client: AsyncClient):
    """GET /v1/lookup/document-checklist?service=Degree Application returns degree docs."""
    resp = await client.get("/v1/lookup/document-checklist", params={"service": "Degree Application"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Degree Application"
    assert len(data["checklist"]) >= 3


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health returns ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
