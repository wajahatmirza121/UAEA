"""Per-conversation state machine for guided flows.

Tracks which guided flow is active and which slots are filled.
State is persisted via Conversation/Message history so it survives restarts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from app.orchestrator.intent_router import GUIDED_FLOW_INTENTS


# ── Flow definitions ──────────────────────────────────────────────────────────

FLOW_DEFINITIONS: dict[str, dict[str, Any]] = {
    "admission": {
        "name": "Admission & Enrolment",
        "service_id": "svc-01",
        "slots": ["programme", "campus"],
        "steps": [
            {"slot": "programme", "prompt": "Which programme are you applying for? (e.g. BS Computer Science, B.Ed, MA Urdu)"},
            {"slot": "campus", "prompt": "Which campus? (Islamabad Main, Rawalpindi, Lahore)"},
            {"action": "get_fee_tariff", "args_from": ["programme"]},
            {"action": "get_deadline", "args_from": ["service_name"],
             "service_name": "Admission & Enrolment"},
            {"action": "get_document_checklist", "args_from": ["service_name"],
             "service_name": "Admission & Enrolment"},
            {"action": "confirm", "text": "Here is everything you need for admission."},
        ],
    },
    "fee_challan": {
        "name": "Fee Challan",
        "service_id": "svc-02",
        "slots": ["programme", "enrolment_type"],
        "steps": [
            {"slot": "programme", "prompt": "Which programme are you enrolled in?"},
            {"slot": "enrolment_type", "prompt": "Is this a new enrolment or a repeat course? (new / repeat)"},
            {"action": "get_fee_tariff", "args_from": ["programme", "enrolment_type"]},
            {"action": "get_deadline", "args_from": ["service_name"],
             "service_name": "Fee Challan"},
            {"action": "confirm", "text": "Generate the challan from the portal and deposit before the due date."},
        ],
    },
    "degree": {
        "name": "Degree Application",
        "service_id": "svc-04",
        "slots": [],
        "steps": [
            {"action": "get_document_checklist", "args_from": ["service_name"],
             "service_name": "Degree Application"},
            {"action": "get_fee_tariff", "args_from": ["service_name"],
             "service_name": "Degree", "category": "Normal service"},
            {"action": "get_deadline", "args_from": ["service_name"],
             "service_name": "Degree Application"},
            {"action": "confirm", "text": "Processing time is 6 to 8 weeks. I cannot promise a specific date."},
        ],
    },
}


@dataclass
class FlowState:
    """Current state of a guided flow within a conversation."""
    intent: str | None = None
    active: bool = False
    filled_slots: dict[str, str] = field(default_factory=dict)
    completed: bool = False

    @classmethod
    def from_messages(cls, messages: list[dict]) -> FlowState:
        """Reconstruct flow state from conversation message history."""
        state = cls()
        for msg in messages:
            tc = msg.get("tool_calls") or []
            for call in tc:
                if call.get("name") == "flow_state":
                    data = call.get("result", {})
                    state.intent = data.get("intent")
                    state.filled_slots = data.get("filled_slots", {})
                    state.active = data.get("active", False)
                    state.completed = data.get("completed", False)
        return state

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "active": self.active,
            "filled_slots": self.filled_slots,
            "completed": self.completed,
        }


def next_step(state: FlowState) -> dict | None:
    """Determine the next step for an active guided flow.

    Returns a step dict (prompt/confirm/action) or None if flow is complete.
    """
    if not state.active or not state.intent:
        return None

    flow_def = FLOW_DEFINITIONS.get(state.intent)
    if not flow_def:
        return None

    for step in flow_def["steps"]:
        # If this step collects a slot that's not yet filled, prompt for it
        if "slot" in step and step["slot"] not in state.filled_slots:
            return step

        # If this step is an action that needs execution
        if "action" in step:
            # Check if all required args are available
            args_from = step.get("args_from", [])
            all_filled = all(
                a in state.filled_slots or a in step
                for a in args_from
            )
            if all_filled:
                return step

    # All steps completed
    state.completed = True
    state.active = False
    return None


def fill_slot(state: FlowState, text: str) -> str | None:
    """Try to fill the next unfilled slot from user text.

    Returns the slot name that was filled, or None.
    """
    if not state.active or not state.intent:
        return None

    flow_def = FLOW_DEFINITIONS.get(state.intent)
    if not flow_def:
        return None

    for slot_name in flow_def["slots"]:
        if slot_name not in state.filled_slots:
            state.filled_slots[slot_name] = text.strip()
            return slot_name

    return None
