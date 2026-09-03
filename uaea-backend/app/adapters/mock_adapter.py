"""MockAdapter — canned responses for Phase 1.

Returns realistic data so guided flows can be tested end-to-end
without any dependency on University IT systems.
"""

from __future__ import annotations
from typing import Any
from app.adapters.base import StudentSystemAdapter


class MockAdapter(StudentSystemAdapter):

    async def get_fee_status(self, roll_number: str) -> dict[str, Any]:
        return {
            "roll_number": roll_number,
            "status": "paid",
            "amount": 28500,
            "semester": "Autumn 2026",
            "paid_on": "2026-09-15",
            "challan_number": "CH-2026-44821",
        }

    async def get_result(self, roll_number: str, semester: str) -> dict[str, Any]:
        return {
            "roll_number": roll_number,
            "semester": semester,
            "gpa": 3.42,
            "status": "passed",
            "gazette_notified": True,
        }

    async def get_assignment_status(self, roll_number: str, course: str) -> dict[str, Any]:
        return {
            "roll_number": roll_number,
            "course": course,
            "submitted": 3,
            "total": 4,
            "pending": "Assignment 4 — due 2026-11-09",
        }

    async def submit_service_request(self, request_type: str, payload: dict) -> dict[str, Any]:
        return {
            "request_id": f"SR-2026-{hash(str(payload)) % 10000:04d}",
            "type": request_type,
            "status": "submitted",
            "message": "Your request has been submitted and will be processed within 5 working days.",
        }

    async def track_request(self, request_id: str) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "status": "in_progress",
            "last_update": "2026-09-01",
            "note": "Under review by the relevant department.",
        }


# Singleton for dependency injection
mock_adapter = MockAdapter()
