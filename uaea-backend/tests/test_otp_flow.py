"""WhatsApp OTP verification for private student records (end-to-end via the chat API)."""

import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.config import settings
from app.db.models import OtpChallenge
from app.services import whatsapp


@pytest.fixture
def outbox(monkeypatch):
    """Capture WhatsApp messages instead of sending them."""
    sent: list[dict] = []

    async def fake_send(phone, code, student_name=None):
        sent.append({"phone": phone, "code": code, "name": student_name})
        return whatsapp.Delivery(True, "whatsapp:test", ref=f"msg-{len(sent)}")

    monkeypatch.setattr(whatsapp, "send_otp", fake_send)
    return sent


async def say(client: AsyncClient, session: str, text: str) -> dict:
    r = await client.post("/v1/chat/message", json={"session_id": session, "channel": "web", "text": text})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_general_information_needs_no_otp(client, outbox):
    data = await say(client, "pub-1", "BSCS ki classes kab sy shru hongi?")
    assert data["otp"] is None
    assert outbox == []
    assert "2 Nov 2026" in data["reply"]
    assert any(tc["name"] == "get_academic_calendar" for tc in data["tool_calls"])


@pytest.mark.asyncio
async def test_private_result_requires_whatsapp_otp(client, outbox):
    data = await say(client, "otp-1", "Roll number BSCS-2023-014 ka result batao")
    assert data["otp"]["roll_number"] == "BSCS-2023-014"
    assert data["otp"]["masked_phone"] == "+92 333 •••7617"
    # Code went to the demo WhatsApp number, and nothing private leaked.
    assert len(outbox) == 1
    assert outbox[0]["phone"] == settings.demo_student_phone == "+923333797617"
    assert "GPA" not in data["reply"] and "Aisha" not in data["reply"]
    assert outbox[0]["code"] not in data["reply"]
    assert "dev_code" not in data["otp"]


@pytest.mark.asyncio
async def test_wrong_then_correct_code_shows_result(client, outbox):
    await say(client, "otp-2", "BSCS-2023-014 result")
    code = outbox[-1]["code"]
    wrong = "000000" if code != "000000" else "111111"

    bad = await say(client, "otp-2", wrong)
    assert "not correct" in bad["reply"] or "ghalat" in bad["reply"]
    assert "GPA" not in bad["reply"]

    good = await say(client, "otp-2", f"code is {code}")
    assert good["verified_roll"] == "BSCS-2023-014"
    assert "Aisha Khan" in good["reply"]
    assert "GPA" in good["reply"] and "CGPA" in good["reply"]
    assert good["engine"] == "otp"


@pytest.mark.asyncio
async def test_verified_session_can_ask_more_without_new_code(client, outbox):
    await say(client, "otp-3", "BSCS-2023-014 ki attendance")
    await say(client, "otp-3", outbox[-1]["code"])
    n_sent = len(outbox)

    fee = await say(client, "otp-3", "BSCS-2023-014 fee status")
    assert len(outbox) == n_sent            # no new code
    assert fee["otp"] is None
    assert "Fee status" in fee["reply"]


@pytest.mark.asyncio
async def test_other_session_cannot_reuse_verification(client, outbox):
    await say(client, "otp-4a", "BSCS-2023-014 result")
    await say(client, "otp-4a", outbox[-1]["code"])
    other = await say(client, "otp-4b", "BSCS-2023-014 result")
    assert other["otp"] is not None
    assert "GPA" not in other["reply"]


@pytest.mark.asyncio
async def test_expired_code_is_rejected(client, outbox, seeded_db):
    await say(client, "otp-5", "BSCS-2024-007 result")
    code = outbox[-1]["code"]
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    await seeded_db.execute(update(OtpChallenge).where(OtpChallenge.session_id == "otp-5").values(expires_at=past))
    await seeded_db.commit()
    data = await say(client, "otp-5", code)
    assert "expired" in data["reply"].lower()
    assert "GPA" not in data["reply"]


@pytest.mark.asyncio
async def test_lockout_after_max_attempts(client, outbox):
    await say(client, "otp-6", "BBA-2023-021 result")
    code = outbox[-1]["code"]
    wrong = "123456" if code != "123456" else "654321"
    for _ in range(settings.otp_max_attempts):
        last = await say(client, "otp-6", wrong)
    assert "Too many" in last["reply"] or "Bohat" in last["reply"]
    after = await say(client, "otp-6", code)        # even the right code no longer works
    assert "GPA" not in after["reply"]


@pytest.mark.asyncio
async def test_resend_invalidates_old_code(client, outbox, seeded_db, monkeypatch):
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)
    await say(client, "otp-7", "BSAI-2024-002 result")
    old = outbox[-1]["code"]
    r = await say(client, "otp-7", "resend")
    assert r["otp"] is not None and len(outbox) == 2
    new = outbox[-1]["code"]
    if old != new:
        bad = await say(client, "otp-7", old)
        assert "GPA" not in bad["reply"]
    good = await say(client, "otp-7", new)
    assert "Zainab Ahmed" in good["reply"]


@pytest.mark.asyncio
async def test_codes_are_stored_hashed(client, outbox, seeded_db):
    await say(client, "otp-8", "MSCS-2025-002 result")
    code = outbox[-1]["code"]
    ch = (await seeded_db.execute(select(OtpChallenge).where(OtpChallenge.session_id == "otp-8"))).scalar_one()
    assert ch.code_hash != code and code not in ch.code_hash
    assert len(ch.code_hash) == 64


@pytest.mark.asyncio
async def test_unknown_roll_number(client, outbox):
    data = await say(client, "otp-9", "BSCS-2099-123 result")
    assert outbox == []
    assert "No student found" in data["reply"]


@pytest.mark.asyncio
async def test_private_question_without_roll_asks_for_it(client, outbox):
    data = await say(client, "otp-10", "meri attendance kitni hai")
    assert outbox == []
    assert "BSCS-2023-014" in data["reply"]  # shows the expected format


@pytest.mark.asyncio
async def test_bare_code_without_pending(client, outbox):
    data = await say(client, "otp-11", "482913")
    assert "no verification" in data["reply"].lower() or "pending nahi" in data["reply"].lower()


@pytest.mark.asyncio
async def test_dev_echo_shows_code_only_when_enabled(client, outbox, monkeypatch):
    monkeypatch.setattr(settings, "otp_dev_echo", True)
    data = await say(client, "otp-12", "BSIT-2025-003 result")
    assert data["otp"]["dev_code"] == outbox[-1]["code"]


@pytest.mark.asyncio
async def test_hourly_limit(client, outbox, monkeypatch):
    monkeypatch.setattr(settings, "otp_max_per_hour", 2)
    for i in range(2):
        await say(client, f"otp-13-{i}", "BSPSY-2024-009 result")
    data = await say(client, "otp-13-x", "BSPSY-2024-009 result")
    assert len(outbox) == 2
    assert "Too many" in data["reply"]
