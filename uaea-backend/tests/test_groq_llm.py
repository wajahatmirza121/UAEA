"""Groq tool-calling path, using a fake OpenAI-compatible client (no network)."""

import json
from types import SimpleNamespace as NS

import httpx
import pytest
from openai import APIConnectionError, NotFoundError

from app.config import settings
from app.orchestrator import orchestrator
from app.services import whatsapp


def tool_call(name, args, i=1):
    return NS(id=f"call_{i}", type="function", function=NS(name=name, arguments=json.dumps(args)))


def reply(content=None, calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=calls or None))])


class FakeGroq:
    """Plays back a script; records every request it receives."""
    script: list = []
    requests: list = []

    def __init__(self, *a, **kw):
        self.chat = NS(completions=NS(create=self._create))

    async def _create(self, **kw):
        FakeGroq.requests.append(kw)
        step = FakeGroq.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step(kw) if callable(step) else step


@pytest.fixture
def groq(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "gsk_test_key")
    monkeypatch.setattr(orchestrator, "AsyncOpenAI", FakeGroq)
    FakeGroq.script, FakeGroq.requests = [], []
    return FakeGroq


@pytest.fixture
def outbox(monkeypatch):
    sent = []

    async def fake_send(phone, code, student_name=None):
        sent.append(code)
        return whatsapp.Delivery(True, "whatsapp:test")

    monkeypatch.setattr(whatsapp, "send_otp", fake_send)
    return sent


async def say(client, session, text):
    r = await client.post("/v1/chat/message", json={"session_id": session, "text": text})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_groq_answers_from_tool_results(client, groq):
    def final(kw):
        tool_msg = [m for m in kw["messages"] if m["role"] == "tool"][0]
        data = json.loads(tool_msg["content"])
        bscs = [e for e in data["events"] if e["program"] == "BSCS"][0]
        assert bscs["start_date"] == "2026-11-02"
        return reply("BSCS 1st semester ki classes 2 November 2026 se shuru hongi. Source: Academic Calendar 2026-27")

    groq.script = [reply(calls=[tool_call("get_academic_calendar", {"program": "BSCS", "event": "classes begin"})]), final]
    data = await say(client, "g-1", "BSCS ki classes kab sy shru hongi")
    assert data["engine"] == "groq"
    assert "2 November 2026" in data["reply"] and "[unconfirmed]" not in data["reply"]
    assert data["tool_calls"][0]["name"] == "get_academic_calendar"
    # System prompt carries the date and the student's language
    system = groq.requests[0]["messages"][0]["content"]
    assert "2026" in system and "Roman Urdu" in system
    assert len(groq.requests[0]["tools"]) >= 20


@pytest.mark.asyncio
async def test_groq_private_tool_triggers_otp_and_hides_data(client, groq, outbox):
    groq.script = [reply(calls=[tool_call("get_student_result", {"roll_number": "BSCS-2023-014"})])]
    data = await say(client, "g-2", "aisha ka result BSCS-2023-014")
    assert data["otp"]["masked_phone"] == "+92 333 •••7617"
    assert len(outbox) == 1
    assert "GPA" not in data["reply"]
    assert len(groq.requests) == 1           # loop stopped; nothing private went back to the model

    # The code is checked in code, without calling Groq
    verified = await say(client, "g-2", outbox[0])
    assert verified["verified_roll"] == "BSCS-2023-014" and "CGPA" in verified["reply"]
    assert len(groq.requests) == 1


@pytest.mark.asyncio
async def test_after_verification_groq_receives_private_data(client, groq, outbox):
    groq.script = [reply(calls=[tool_call("get_student_result", {"roll_number": "BSCS-2023-014"})])]
    await say(client, "g-3", "BSCS-2023-014 result")
    await say(client, "g-3", outbox[0])

    groq.script = [reply(calls=[tool_call("get_attendance", {"roll_number": "BSCS-2023-014"})]),
                   reply("Aap ki overall attendance theek hai.")]
    data = await say(client, "g-3", "aur attendance?")
    assert data["otp"] is None
    tool_msgs = [m for m in groq.requests[-1]["messages"] if m["role"] == "tool"]
    assert '"verified": true' in tool_msgs[0]["content"]
    assert "BSCS-2023-014" in groq.requests[-2]["messages"][0]["content"]  # verified roll told to the model


@pytest.mark.asyncio
async def test_groq_unreachable_falls_back_to_offline(client, groq):
    groq.script = [APIConnectionError(request=httpx.Request("POST", "https://api.groq.com"))]
    data = await say(client, "g-4", "BSCS ki fees kitni hai")
    assert data["engine"] == "offline"
    assert "28,500" in data["reply"]


@pytest.mark.asyncio
async def test_decommissioned_model_moves_to_fallback(client, groq):
    gone = NotFoundError("model not found", response=httpx.Response(404, request=httpx.Request("POST", "https://x")), body=None)
    groq.script = [gone, reply("Hello! How can I help?")]
    data = await say(client, "g-5", "hello")
    assert data["engine"] == "groq"
    assert groq.requests[0]["model"] == settings.llm_model
    assert groq.requests[1]["model"] != settings.llm_model


@pytest.mark.asyncio
async def test_hallucinated_numbers_are_replaced_by_grounded_answer(client, groq):
    groq.script = [reply(calls=[tool_call("get_fee_tariff", {"program": "BSCS"})]),
                   reply("Fee is Rs 99,000, plus Rs 7,777 lab fee and Rs 1,234 sports fee, due 05-12-2026.")]
    data = await say(client, "g-6", "BSCS fee?")
    assert "99,000" not in data["reply"] and "7,777" not in data["reply"]
    assert "28,500" in data["reply"]


@pytest.mark.asyncio
async def test_malformed_tool_arguments_do_not_crash(client, groq):
    bad = NS(id="c1", type="function", function=NS(name="get_fee_tariff", arguments="{not json"))
    groq.script = [reply(calls=[bad]), reply("Which programme do you mean?")]
    data = await say(client, "g-7", "fee?")
    assert data["reply"] == "Which programme do you mean?"


@pytest.mark.asyncio
async def test_empty_reply_tries_next_model_and_gpt_oss_gets_low_reasoning(client, groq, monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "openai/gpt-oss-120b")
    groq.script = [reply(content=""), reply("Assalam o alaikum!")]
    data = await say(client, "g-8", "salam")
    assert data["reply"] == "Assalam o alaikum!"
    assert groq.requests[0]["extra_body"] == {"reasoning_effort": "low"}
    assert groq.requests[1]["model"] != "openai/gpt-oss-120b"
