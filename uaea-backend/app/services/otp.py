"""One-time-password verification for private student records.

Flow
----
1. A private tool (result, fee status, attendance, profile) is called for a
   roll number. If this chat session has not verified that roll number, the
   tool does NOT return data. Instead :func:`start_challenge` creates an
   ``OtpChallenge``, sends a 6-digit code to the student's WhatsApp number and
   remembers which lookup was asked for.
2. The student types the code in the chat. The orchestrator checks it with
   :func:`verify_code` *before* the LLM is involved — the model never sees or
   judges the code.
3. On success the session may read that roll number's records for
   ``OTP_ACCESS_MINUTES`` and the remembered lookup is answered immediately.

Codes are stored only as an HMAC; they expire after ``OTP_TTL_SECONDS`` and
lock after ``OTP_MAX_ATTEMPTS`` wrong tries.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OtpChallenge, Student
from app.services import whatsapp


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _aware(dt: datetime.datetime | None) -> datetime.datetime | None:
    """SQLite hands back naive datetimes; treat them as UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def _hash(challenge_id: str, code: str) -> str:
    msg = f"{challenge_id}:{code}".encode()
    return hmac.new(settings.otp_secret.encode(), msg, hashlib.sha256).hexdigest()


def generate_code() -> str:
    n = settings.otp_length
    return str(secrets.randbelow(10 ** n)).zfill(n)


def mask_phone(phone: str) -> str:
    """'+923333797617' → '+92 333 •••7617'."""
    d = "".join(ch for ch in phone if ch.isdigit())
    if d.startswith("0") and len(d) == 11:
        d = "92" + d[1:]
    if len(d) >= 12:
        return f"+{d[:2]} {d[2:5]} •••{d[-4:]}"
    return "•••" + d[-4:]


def mask_name(name: str) -> str:
    """'Aisha Khan' → 'A•••• K•••' (confirms the record without revealing it).

    Bullets, not asterisks, so Markdown rendering can't eat them.
    """
    return " ".join(p[0] + "•" * (len(p) - 1) for p in name.split())


@dataclass
class VerifyOutcome:
    status: str                     # ok | wrong | expired | locked | none
    challenge: OtpChallenge | None = None
    attempts_left: int = 0


# ── queries ───────────────────────────────────────────────────────────────────

async def is_verified(db: AsyncSession, session_id: str, roll_number: str) -> bool:
    if not session_id:
        return False
    stmt = (
        select(OtpChallenge)
        .where(OtpChallenge.session_id == session_id,
               OtpChallenge.roll_number == roll_number,
               OtpChallenge.status == "verified")
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    ch = (await db.execute(stmt)).scalar_one_or_none()
    return bool(ch and _aware(ch.verified_until) and _aware(ch.verified_until) > _now())


async def verified_rolls(db: AsyncSession, session_id: str) -> list[str]:
    stmt = select(OtpChallenge).where(OtpChallenge.session_id == session_id, OtpChallenge.status == "verified")
    now = _now()
    return sorted({c.roll_number for c in (await db.execute(stmt)).scalars().all()
                   if _aware(c.verified_until) and _aware(c.verified_until) > now})


async def get_pending(db: AsyncSession, session_id: str) -> OtpChallenge | None:
    """Latest pending challenge for this session (expired ones are marked expired)."""
    stmt = (
        select(OtpChallenge)
        .where(OtpChallenge.session_id == session_id, OtpChallenge.status == "pending")
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    ch = (await db.execute(stmt)).scalar_one_or_none()
    if ch and _aware(ch.expires_at) <= _now():
        ch.status = "expired"
        await db.flush()
        # Keep returning it so the caller can tell the student it expired.
    return ch


async def latest(db: AsyncSession, session_id: str) -> OtpChallenge | None:
    stmt = (select(OtpChallenge).where(OtpChallenge.session_id == session_id)
            .order_by(OtpChallenge.created_at.desc()).limit(1))
    return (await db.execute(stmt)).scalar_one_or_none()


# ── actions ───────────────────────────────────────────────────────────────────

def _public_payload(ch: OtpChallenge, student: Student | None, *, resent: bool = False,
                    code: str | None = None, delivery_error: str | None = None) -> dict[str, Any]:
    left = max(0, int((_aware(ch.expires_at) - _now()).total_seconds()))
    payload: dict[str, Any] = {
        "otp_required": True,
        "roll_number": ch.roll_number,
        "student": mask_name(student.name) if student else None,
        "masked_phone": mask_phone(ch.phone),
        "channel": "WhatsApp",
        "expires_in_seconds": left,
        "resent": resent,
        "message": (
            f"This is private student information. A {settings.otp_length}-digit verification code has been "
            f"sent on WhatsApp to the number registered for {ch.roll_number} ({mask_phone(ch.phone)}). "
            f"Ask the student to type the code in this chat."
        ),
    }
    if delivery_error:
        payload["delivery_failed"] = True
        payload["message"] = (
            "The verification code could not be delivered on WhatsApp right now. "
            "Ask the student to try again in a minute (type 'resend')."
        )
    if code and settings.otp_dev_echo and settings.app_env != "production":
        payload["dev_code"] = code
    return payload


async def start_challenge(
    db: AsyncSession,
    session_id: str,
    student: Student,
    pending_call: dict[str, Any] | None,
    question: str | None = None,
) -> dict[str, Any]:
    """Create (or reuse) a challenge for (session, roll) and send the code."""
    now = _now()
    # Reuse a live pending challenge for the same roll number instead of spamming codes.
    stmt = (
        select(OtpChallenge)
        .where(OtpChallenge.session_id == session_id, OtpChallenge.roll_number == student.roll_number,
               OtpChallenge.status == "pending")
        .order_by(OtpChallenge.created_at.desc()).limit(1)
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing and _aware(existing.expires_at) > now:
        calls = list((existing.pending_tool or {}).get("calls", []))
        if pending_call and pending_call not in calls:
            calls.append(pending_call)
            existing.pending_tool = {"calls": calls}
        await db.flush()
        return _public_payload(existing, student)

    # Cancel any other pending challenge in this session (one at a time).
    others = (await db.execute(select(OtpChallenge).where(
        OtpChallenge.session_id == session_id, OtpChallenge.status == "pending"))).scalars().all()
    for o in others:
        o.status = "cancelled"

    # Hourly cap per roll number.
    hour_ago = now - datetime.timedelta(hours=1)
    sent_last_hour = (await db.execute(
        select(func.count()).select_from(OtpChallenge).where(
            OtpChallenge.roll_number == student.roll_number, OtpChallenge.created_at >= hour_ago)
    )).scalar_one()
    if sent_last_hour >= settings.otp_max_per_hour:
        return {"otp_required": True, "rate_limited": True, "roll_number": student.roll_number,
                "message": "Too many verification codes were requested for this roll number. Please try again in an hour."}

    code = generate_code()
    ch = OtpChallenge(
        id=str(uuid.uuid4()), session_id=session_id, roll_number=student.roll_number,
        phone=student.phone, code_hash="", status="pending", attempts=0,
        pending_tool={"calls": [pending_call] if pending_call else []},
        pending_question=question, created_at=now,
        expires_at=now + datetime.timedelta(seconds=settings.otp_ttl_seconds),
    )
    ch.code_hash = _hash(ch.id, code)
    db.add(ch)
    await db.flush()

    delivery = await whatsapp.send_otp(student.phone, code, student.name.split()[0])
    ch.delivery = delivery.channel if delivery.ok else f"failed:{delivery.channel}"
    ch.delivery_ref = delivery.ref or (delivery.error or "")[:120]
    await db.flush()
    return _public_payload(ch, student, code=code, delivery_error=None if delivery.ok else delivery.error)


async def resend(db: AsyncSession, session_id: str) -> dict[str, Any] | None:
    """Send a fresh code for the session's latest pending/expired challenge."""
    stmt = (
        select(OtpChallenge)
        .where(OtpChallenge.session_id == session_id, OtpChallenge.status.in_(["pending", "expired"]))
        .order_by(OtpChallenge.created_at.desc()).limit(1)
    )
    ch = (await db.execute(stmt)).scalar_one_or_none()
    if not ch:
        return None
    wait = settings.otp_resend_cooldown_seconds - (_now() - _aware(ch.created_at)).total_seconds()
    if ch.status == "pending" and wait > 0:
        payload = _public_payload(ch, None)
        payload["message"] = f"Please wait {int(wait) + 1} seconds before asking for a new code."
        payload["cooldown_seconds"] = int(wait) + 1
        return payload
    student = (await db.execute(select(Student).where(Student.roll_number == ch.roll_number))).scalar_one_or_none()
    if not student:
        return None
    pending_call = None
    calls = (ch.pending_tool or {}).get("calls", [])
    ch.status = "cancelled"
    await db.flush()
    payload = await start_challenge(db, session_id, student, calls[0] if calls else pending_call, ch.pending_question)
    # carry over any additional queued lookups
    new = await get_pending(db, session_id)
    if new and len(calls) > 1:
        new.pending_tool = {"calls": calls}
        await db.flush()
    payload["resent"] = True
    return payload


async def cancel(db: AsyncSession, session_id: str) -> bool:
    rows = (await db.execute(select(OtpChallenge).where(
        OtpChallenge.session_id == session_id, OtpChallenge.status == "pending"))).scalars().all()
    for r in rows:
        r.status = "cancelled"
    await db.flush()
    return bool(rows)


async def verify_code(db: AsyncSession, session_id: str, code: str) -> VerifyOutcome:
    ch = await get_pending(db, session_id)
    if ch is None:
        return VerifyOutcome("none")
    if ch.status == "expired":
        return VerifyOutcome("expired", ch)
    if ch.attempts >= settings.otp_max_attempts:
        ch.status = "locked"
        await db.flush()
        return VerifyOutcome("locked", ch)

    if hmac.compare_digest(ch.code_hash, _hash(ch.id, code.strip())):
        ch.status = "verified"
        ch.verified_until = _now() + datetime.timedelta(minutes=settings.otp_access_minutes)
        await db.flush()
        return VerifyOutcome("ok", ch)

    ch.attempts += 1
    left = settings.otp_max_attempts - ch.attempts
    if left <= 0:
        ch.status = "locked"
        await db.flush()
        return VerifyOutcome("locked", ch)
    await db.flush()
    return VerifyOutcome("wrong", ch, attempts_left=left)
