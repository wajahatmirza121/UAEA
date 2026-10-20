"""StudentSystemAdapter — abstract interface.

All orchestrator/tool code depends on this interface, never on concrete adapters.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class StudentSystemAdapter(ABC):

    @abstractmethod
    async def get_fee_status(self, roll_number: str) -> dict[str, Any]:
        """Return fee payment status for a student."""

    @abstractmethod
    async def get_result(self, roll_number: str, semester: str) -> dict[str, Any]:
        """Return examination result for a student/semester."""

    @abstractmethod
    async def get_assignment_status(self, roll_number: str, course: str) -> dict[str, Any]:
        """Return assignment submission status."""

    @abstractmethod
    async def submit_service_request(self, request_type: str, payload: dict) -> dict[str, Any]:
        """Submit a generic service request. Returns a receipt."""

    @abstractmethod
    async def track_request(self, request_id: str) -> dict[str, Any]:
        """Track the status of a previously submitted request."""
