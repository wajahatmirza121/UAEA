"""WhatsApp delivery for OTP codes.

Providers (set ``WHATSAPP_PROVIDER`` in .env):

* ``console`` — default. Prints the code to the backend log. Nothing is sent.
  Use with ``OTP_DEV_ECHO=true`` to also show the code inside the chat (demo only).
* ``twilio``  — Twilio WhatsApp API. Works instantly with the Twilio *sandbox*:
  the receiving phone (+92 333 3797617) must first send the sandbox join code
  (e.g. "join <two-words>") to +1 415 523 8886 on WhatsApp.
* ``meta``    — WhatsApp Cloud API (Meta). Production route. Business-initiated
  messages need an approved AUTHENTICATION template (``META_WA_TEMPLATE``);
  plain text only works within 24 h of the user messaging your business number.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger("whatsapp")


@dataclass
class Delivery:
    ok: bool
    channel: str            # "console" | "whatsapp:twilio" | "whatsapp:meta"
    ref: str | None = None  # provider message id
    error: str | None = None


def otp_message(code: str, student_name: str | None = None) -> str:
    who = f" for {student_name}" if student_name else ""
    minutes = max(1, settings.otp_ttl_seconds // 60)
    return (
        f"UAEA University: your verification code{who} is {code}. "
        f"It expires in {minutes} minutes. Do not share this code with anyone. "
        f"Agar aap ne yeh request nahi ki to is message ko nazar-andaz karein."
    )


def _digits(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def _e164(phone: str) -> str:
    """'+92 333 3797617' / '03333797617' → '+923333797617'."""
    d = _digits(phone)
    if d.startswith("0") and len(d) == 11:      # local Pakistani format
        d = "92" + d[1:]
    return "+" + d


async def _send_twilio(phone: str, body: str) -> Delivery:
    sid, token = settings.twilio_account_sid, settings.twilio_auth_token
    if not sid or not token:
        return Delivery(False, "whatsapp:twilio", error="TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {"From": settings.twilio_whatsapp_from, "To": f"whatsapp:{_e164(phone)}", "Body": body}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, data=data, auth=(sid, token))
    if r.status_code >= 300:
        return Delivery(False, "whatsapp:twilio", error=f"Twilio {r.status_code}: {r.text[:300]}")
    return Delivery(True, "whatsapp:twilio", ref=r.json().get("sid"))


async def _send_meta(phone: str, code: str, body: str) -> Delivery:
    token, pnid = settings.meta_wa_token, settings.meta_wa_phone_number_id
    if not token or not pnid:
        return Delivery(False, "whatsapp:meta", error="META_WA_TOKEN / META_WA_PHONE_NUMBER_ID not set")
    url = f"https://graph.facebook.com/{settings.meta_wa_api_version}/{pnid}/messages"
    to = _digits(_e164(phone))
    if settings.meta_wa_template:
        # Authentication template: code in the body + "copy code" URL button.
        payload = {
            "messaging_product": "whatsapp", "to": to, "type": "template",
            "template": {
                "name": settings.meta_wa_template,
                "language": {"code": settings.meta_wa_template_lang},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": code}]},
                    {"type": "button", "sub_type": "url", "index": "0",
                     "parameters": [{"type": "text", "text": code}]},
                ],
            },
        }
    else:
        payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
    if r.status_code >= 300:
        return Delivery(False, "whatsapp:meta", error=f"Meta {r.status_code}: {r.text[:300]}")
    msgs = r.json().get("messages") or [{}]
    return Delivery(True, "whatsapp:meta", ref=msgs[0].get("id"))


async def send_otp(phone: str, code: str, student_name: str | None = None) -> Delivery:
    """Send an OTP over the configured provider. Never raises."""
    provider = (settings.whatsapp_provider or "console").lower().strip()
    body = otp_message(code, student_name)
    try:
        if provider == "twilio":
            result = await _send_twilio(phone, body)
        elif provider == "meta":
            result = await _send_meta(phone, code, body)
        else:
            logger.warning("[OTP console] WhatsApp to %s: %s", _e164(phone), body)
            result = Delivery(True, "console")
    except httpx.HTTPError as e:
        result = Delivery(False, f"whatsapp:{provider}", error=f"network error: {e}")

    if not result.ok:
        logger.error("OTP delivery failed via %s: %s", result.channel, result.error)
    return result
