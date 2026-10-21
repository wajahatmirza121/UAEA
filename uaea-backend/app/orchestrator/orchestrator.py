"""Orchestrator — the pipeline for every incoming chat message.

    sanitize → classify → persist
      → OTP gate (deterministic: verify / resend / cancel a pending code)
      → Groq LLM with tool-calling over the real database
          (falls back to the offline engine if Groq is unavailable)
      → guardrails (strip numbers/dates not backed by a tool result)
      → persist → response

Private student data is only ever produced by tools that check OTP
verification in code; the LLM cannot bypass it.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from openai import (
    AsyncOpenAI, APIError, APIConnectionError, APITimeoutError, BadRequestError,
    NotFoundError, RateLimitError, AuthenticationError,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Conversation, Message, UnansweredQuery
from app.orchestrator.clock import today
from app.orchestrator.entities import find_otp_code
from app.orchestrator.formatters import format_tool, otp_prompt
from app.orchestrator.guardrails import check_reply
from app.orchestrator.intent_router import classify
from app.orchestrator.normalizer import normalise, detect_language, strip_injection
from app.orchestrator.offline import answer_offline
from app.orchestrator.tools import TOOL_DEFINITIONS, PRIVATE_TOOLS, ToolContext, execute_tool
from app.services import otp as otp_service

logger = logging.getLogger("orchestrator")

MAX_ROUNDS = 5
HISTORY_TURNS = 12

SYSTEM_PROMPT = """You are "UAEA Assistant", the student-services chatbot of UAEA University (Pakistan).
Students write in English, Urdu script, or Roman Urdu (e.g. "BSCS ki classes kab sy shru hongi?" = "When do BSCS classes start?").
Understand spelling mistakes and mixed language.

FACTS COME ONLY FROM TOOLS
1. Never state a fee, date, deadline, document requirement, phone number, grade or any university fact unless a tool returned it in THIS turn. Do not use your training knowledge about universities.
2. Always call a tool first. Pick the most specific one:
   - when classes start / mid-terms / finals / holidays / orientation / convocation → get_academic_calendar (pass program code like "BSCS" and an event keyword)
   - fees → get_fee_tariff; last dates → get_deadline; required documents & procedure → get_document_checklist
   - programmes, eligibility, seats → get_program_info / list_programs; timetable → get_class_timetable; courses → get_courses
   - teachers → get_faculty; offices & phone numbers → get_department; scholarships, hostels, buses → their tools
   - rules & policies (attendance %, grading, refund, probation, plagiarism, library, LMS, etc.) → search_knowledge_base (query in English)
3. If tools return nothing useful, say you don't have that information and offer to connect the student to staff (create_escalation_ticket only if they agree or insist).

PRIVATE STUDENT DATA (result, GPA/CGPA, marks, fee status/dues, attendance, profile)
4. Only via get_student_result / get_fee_status / get_attendance / get_student_profile with a roll number (format like BSCS-2023-014). If the student did not give a roll number, ask for it. Never guess a roll number and never look up a student by name.
5. These tools are protected by WhatsApp OTP. The system handles the code automatically; never ask for the code yourself, never claim someone is verified, and never reveal private data that a tool did not return.

STYLE
6. Reply in the student's language and script (Roman Urdu → Roman Urdu, اردو → اردو, English → English).
7. Be concise and friendly. Use short paragraphs, bullet points or a small Markdown table. Write amounts as "Rs 28,500" and dates like "2 Nov 2026"; mention how many days are left when useful.
8. End factual answers with the source in the form: Source: <source from the tool>.
"""


# ── public entry point ────────────────────────────────────────────────────────

def llm_enabled() -> bool:
    key = (settings.llm_api_key or "").strip()
    return bool(key) and "REPLACE" not in key.upper()


async def handle_message(db: AsyncSession, session_id: str, channel: str, text: str) -> dict[str, Any]:
    cleaned = strip_injection(text or "")[:2000]
    language = detect_language(cleaned)
    intent_result = classify(cleaned)
    intent = intent_result["intent"]
    confidence = intent_result["confidence"]

    conversation = await _get_or_create_conversation(db, session_id, channel)
    db.add(Message(id=str(uuid.uuid4()), conversation_id=conversation.id, role="user", text=cleaned, intent=intent))
    await db.flush()
    history = await _get_message_history(db, conversation.id)
    ctx = ToolContext(session_id=session_id, conversation_id=conversation.id, question=cleaned)

    # 1. OTP gate — handled in code, never by the LLM.
    gate = await _otp_gate(db, ctx, cleaned, language)
    if gate is not None:
        return await _finish(db, conversation, gate, intent="otp_verification", confidence=1.0, language=language)

    # 2. Answer: Groq with tools, else offline engine.
    out: dict[str, Any] | None = None
    if llm_enabled():
        out = await _run_llm(db, ctx, cleaned, history[:-1], language)
    if out is None:
        out = await answer_offline(db, cleaned, intent_result, language, ctx, history[:-1])
        out["engine"] = "offline"
        out["model"] = None
    else:
        # 3. Guardrails on LLM text.
        grounding = [cleaned, str(today())] + [m.get("text") or "" for m in history[-6:] if m["role"] == "user"]
        g = check_reply(out["reply"], out["tool_calls"], extra_grounding=grounding)
        if len(g.flags) > 2:
            logger.warning("Guardrail rejected LLM reply (%d flags) — using offline answer", len(g.flags))
            alt = await answer_offline(db, cleaned, intent_result, language, ctx, history[:-1])
            out.update(reply=alt["reply"], tool_calls=out["tool_calls"] + alt["tool_calls"],
                       otp=out.get("otp") or alt.get("otp"))
            out["guardrail"] = "replaced"
        elif g.was_modified:
            out["reply"] = g.cleaned_reply
            out["guardrail"] = "modified"

    if confidence < 0.4 and not out.get("tool_calls"):
        await _track_unanswered(db, cleaned, intent, confidence)
    return await _finish(db, conversation, out, intent=intent, confidence=confidence, language=language,
                         intent_label=intent_result.get("label"))


# ── OTP gate ──────────────────────────────────────────────────────────────────

_RESEND = re.compile(r"\b(resend|re-send|send again|new code|dobara bhej|dubara bhej|code nahi aaya|code nahi mila|didn'?t get)\b")
_CANCEL = re.compile(r"\b(cancel|stop|chhoro|chodo|rehne do|nahi chahiye)\b")

MSG = {
    "wrong": {"en": "❌ That code is not correct. You have {n} attempt(s) left.",
              "roman": "❌ Ye code ghalat hai. Aap ke paas {n} koshish(ein) baqi hain.",
              "ur": "❌ یہ کوڈ درست نہیں۔ آپ کے پاس {n} کوشش باقی ہیں۔"},
    "expired": {"en": "⌛ That code has expired. Type **resend** to get a new one.",
                "roman": "⌛ Code expire ho gaya hai. Naya code lene ke liye **resend** likhein.",
                "ur": "⌛ کوڈ کی میعاد ختم ہو گئی۔ نیا کوڈ لینے کے لیے **resend** لکھیں۔"},
    "locked": {"en": "🔒 Too many wrong attempts. Please ask again to receive a new code.",
               "roman": "🔒 Bohat dafa ghalat code. Dobara poochein to naya code bheja jayega.",
               "ur": "🔒 بہت زیادہ غلط کوششیں۔ دوبارہ پوچھیں تو نیا کوڈ بھیجا جائے گا۔"},
    "verified": {"en": "✅ Verified. Here are the details you asked for:",
                 "roman": "✅ Verification ho gayi. Ye rahi aap ki maloomat:",
                 "ur": "✅ تصدیق ہو گئی۔ آپ کی مطلوبہ معلومات:"},
    "cancelled": {"en": "Okay, I've cancelled the verification. Ask me anything else.",
                  "roman": "Theek hai, verification cancel kar di. Kuch aur poochna ho to batayein.",
                  "ur": "ٹھیک ہے، تصدیق منسوخ کر دی گئی۔"},
    "no_pending": {"en": "There's no verification in progress. To see a student's record, send the roll number with your question, e.g. *BSCS-2023-014 result*.",
                   "roman": "Abhi koi verification pending nahi. Roll number ke saath sawal likhein, maslan *BSCS-2023-014 result*.",
                   "ur": "ابھی کوئی تصدیق زیرِ التوا نہیں۔ رول نمبر کے ساتھ سوال لکھیں۔"},
}


def _m(key: str, lang: str, **kw) -> str:
    return MSG[key].get(lang, MSG[key]["en"]).format(**kw)


async def _otp_gate(db: AsyncSession, ctx: ToolContext, text: str, lang: str) -> dict[str, Any] | None:
    n = normalise(text)
    code = find_otp_code(text)
    pending = await otp_service.get_pending(db, ctx.session_id)
    # A bare code has no language of its own — answer in the language the
    # private question was asked in.
    if pending is not None and pending.pending_question and re.fullmatch(r"[\W\d_a-zA-Z ]{0,30}", text) and (
            code or len(n.split()) <= 3):
        lang = detect_language(pending.pending_question)

    if pending is not None and pending.status == "expired" and code:
        return _gate_reply(_m("expired", lang))

    if pending is None or pending.status != "pending":
        # A message that is nothing but a 6-digit code, with nothing to verify.
        if code and re.fullmatch(r"[\s\d-]*", text):
            last = await otp_service.latest(db, ctx.session_id)
            if last is not None and last.status in ("expired", "locked"):
                return _gate_reply(_m(last.status, lang))
            return _gate_reply(_m("no_pending", lang))
        if _RESEND.search(n):
            payload = await otp_service.resend(db, ctx.session_id)
            if payload:
                return _gate_reply(otp_prompt(payload, lang), otp=payload)
        return None

    if code:
        outcome = await otp_service.verify_code(db, ctx.session_id, code)
        if outcome.status == "ok":
            ch = outcome.challenge
            calls = (ch.pending_tool or {}).get("calls", []) or [
                {"name": "get_student_profile", "args": {"roll_number": ch.roll_number}}]
            tool_calls, parts = [], []
            for c in calls:
                r = await execute_tool(db, c["name"], c.get("args", {}), ctx.conversation_id, ctx)
                tool_calls.append({"name": c["name"], "args": c.get("args", {}), "result": r})
                parts.append(format_tool(c["name"], r))
            reply = _m("verified", lang) + "\n\n" + "\n\n---\n\n".join(parts)
            reply += ("\n\n_Access to this record stays open in this chat for "
                      f"{settings.otp_access_minutes} minutes — ask about result, attendance, fee status or profile._")
            return _gate_reply(reply, tool_calls=tool_calls, verified=ch.roll_number)
        if outcome.status == "wrong":
            return _gate_reply(_m("wrong", lang, n=outcome.attempts_left), otp=_otp_public(outcome.challenge))
        if outcome.status == "expired":
            return _gate_reply(_m("expired", lang))
        if outcome.status == "locked":
            return _gate_reply(_m("locked", lang))

    if _RESEND.search(n):
        payload = await otp_service.resend(db, ctx.session_id)
        if payload:
            return _gate_reply(otp_prompt(payload, lang) if "cooldown_seconds" not in payload else payload["message"],
                               otp=payload)
    if _CANCEL.search(n) and len(n.split()) <= 4:
        await otp_service.cancel(db, ctx.session_id)
        return _gate_reply(_m("cancelled", lang))
    # Anything else: answer normally; the code stays valid until it expires.
    return None


def _otp_public(ch) -> dict[str, Any] | None:
    if ch is None:
        return None
    return {"otp_required": True, "roll_number": ch.roll_number, "masked_phone": otp_service.mask_phone(ch.phone),
            "channel": "WhatsApp"}


def _gate_reply(reply: str, *, tool_calls: list | None = None, otp: dict | None = None,
                verified: str | None = None) -> dict[str, Any]:
    return {"reply": reply, "tool_calls": tool_calls or [], "escalated": False, "otp": otp,
            "verified_roll": verified, "engine": "otp", "model": None, "resolved": True}


# ── Groq LLM with tools ───────────────────────────────────────────────────────

def _llm_safe(result: Any) -> str:
    """Tool result as JSON for the model — never includes demo OTP codes."""
    if isinstance(result, dict) and "dev_code" in result:
        result = {k: v for k, v in result.items() if k != "dev_code"}
    s = json.dumps(result, default=str, ensure_ascii=False)
    return s[:12000]


async def _run_llm(db: AsyncSession, ctx: ToolContext, text: str, history: list[dict], language: str) -> dict | None:
    """Groq tool-calling loop. Returns None if the LLM can't be used (caller falls back)."""
    client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url,
                         timeout=settings.llm_timeout_seconds, max_retries=1)
    verified = await otp_service.verified_rolls(db, ctx.session_id)
    lang_name = {"ur": "Urdu (Urdu script)", "roman": "Roman Urdu", "en": "English"}.get(language, "English")
    system = (SYSTEM_PROMPT + f"\nToday is {today():%A, %d %B %Y} (Pakistan time)."
              + f"\nThe student is writing in {lang_name}."
              + (f"\nThis chat has already verified roll number(s): {', '.join(verified)} — private tools will return data for them."
                 if verified else ""))
    messages: list[dict] = [{"role": "system", "content": system}]
    for m in history[-HISTORY_TURNS:]:
        if m["role"] in ("user", "assistant") and m.get("text"):
            messages.append({"role": m["role"], "content": m["text"][:3000]})
    messages.append({"role": "user", "content": text})

    models = [settings.llm_model] + [m.strip() for m in settings.llm_fallback_models.split(",") if m.strip()]
    models = list(dict.fromkeys(models))
    tool_calls_out: list[dict] = []
    escalated = False

    model_idx = 0
    tool_fail_retries = 0
    for _round in range(MAX_ROUNDS + 2):
        if model_idx >= len(models):
            return None
        model = models[model_idx]
        try:
            extra = {}
            if model.startswith("openai/gpt-oss") and settings.llm_reasoning_effort:
                extra["extra_body"] = {"reasoning_effort": settings.llm_reasoning_effort}
            resp = await client.chat.completions.create(
                model=model, messages=messages, tools=TOOL_DEFINITIONS, tool_choice="auto",
                temperature=settings.llm_temperature, max_tokens=2048, **extra,
            )
        except AuthenticationError as e:
            logger.error("Groq authentication failed — check LLM_API_KEY: %s", e)
            return None
        except (NotFoundError, RateLimitError) as e:
            logger.warning("Groq model %s unavailable (%s) — trying next model", model, type(e).__name__)
            model_idx += 1
            continue
        except BadRequestError as e:
            body = str(e)
            if "decommissioned" in body or "model_not_found" in body or "does not exist" in body:
                model_idx += 1
                continue
            if "tool_use_failed" in body or "failed_generation" in body:
                tool_fail_retries += 1
                logger.warning("Groq tool_use_failed on %s (retry %d)", model, tool_fail_retries)
                if tool_fail_retries >= 2:
                    model_idx += 1
                continue
            logger.error("Groq bad request: %s", body[:500])
            return None
        except (APIConnectionError, APITimeoutError) as e:
            logger.error("Groq unreachable: %s", e)
            return None
        except APIError as e:
            logger.error("Groq API error: %s", e)
            return None

        msg = resp.choices[0].message
        if not msg.tool_calls and not (msg.content or "").strip():
            # Empty answer (e.g. reasoning used up the token budget) — try the next model.
            logger.warning("Groq model %s returned an empty reply — trying next model", model)
            model_idx += 1
            continue
        if not msg.tool_calls:
            return {"reply": (msg.content or "").strip(), "tool_calls": tool_calls_out, "escalated": escalated,
                    "otp": None, "engine": "groq", "model": model, "resolved": bool(tool_calls_out)}

        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [{"id": tc.id, "type": "function",
                                         "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
                                        for tc in msg.tool_calls]})
        otp_payload = None
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}") or {}
            except json.JSONDecodeError:
                args = {}
            logger.info("Tool call: %s(%s)", name, args)
            result = await execute_tool(db, name, args, ctx.conversation_id, ctx)
            tool_calls_out.append({"name": name, "args": args, "result": result})
            if name == "create_escalation_ticket":
                escalated = True
            if name in PRIVATE_TOOLS and isinstance(result, dict) and result.get("otp_required") and otp_payload is None:
                otp_payload = result
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": _llm_safe(result)})

        if otp_payload:
            # Stop here: the student must enter the code before anything else is shown.
            return {"reply": otp_prompt(otp_payload, language), "tool_calls": tool_calls_out,
                    "escalated": False, "otp": otp_payload, "engine": "groq", "model": model, "resolved": True}

    return {"reply": "Sorry, this is taking longer than expected. Let me connect you to a staff member.",
            "tool_calls": tool_calls_out, "escalated": True, "otp": None, "engine": "groq", "model": models[0],
            "resolved": False}


# ── persistence + response ────────────────────────────────────────────────────

async def _finish(db: AsyncSession, conversation: Conversation, out: dict, *, intent: str | None,
                  confidence: float, language: str, intent_label: str | None = None) -> dict[str, Any]:
    tool_calls = [{"name": tc["name"], "args": tc.get("args"), "result": tc.get("result")} for tc in out.get("tool_calls", [])]
    db.add(Message(id=str(uuid.uuid4()), conversation_id=conversation.id, role="assistant",
                   text=out["reply"], intent=intent, tool_calls=json.loads(json.dumps(tool_calls, default=str))))
    if out.get("escalated"):
        conversation.escalated = True
    await db.commit()

    otp = out.get("otp")
    otp_public = None
    if otp:
        otp_public = {k: otp[k] for k in ("roll_number", "student", "masked_phone", "channel", "expires_in_seconds",
                                          "resent", "rate_limited", "delivery_failed", "cooldown_seconds", "dev_code")
                      if k in otp}
    return {
        "reply": out["reply"],
        "intent": intent,
        "intent_label": intent_label,
        "tool_calls": tool_calls,
        "escalated": bool(out.get("escalated")),
        "confidence": confidence,
        "language": language,
        "sources": _extract_sources(tool_calls),
        "otp": otp_public,
        "verified_roll": out.get("verified_roll"),
        "engine": out.get("engine"),
        "model": out.get("model"),
        "resolved": out.get("resolved", True),
    }


async def _get_or_create_conversation(db: AsyncSession, session_id: str, channel: str) -> Conversation:
    stmt = (select(Conversation)
            .where(Conversation.session_id == session_id, Conversation.resolved.is_(False))
            .order_by(Conversation.started_at.desc()).limit(1))
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if conv is None:
        conv = Conversation(id=str(uuid.uuid4()), session_id=session_id, channel=channel)
        db.add(conv)
        await db.flush()
    return conv


async def _get_message_history(db: AsyncSession, conversation_id: str) -> list[dict]:
    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": m.id, "role": m.role, "text": m.text, "intent": m.intent, "tool_calls": m.tool_calls or [],
             "created_at": str(m.created_at)} for m in rows]


async def _track_unanswered(db: AsyncSession, text: str, intent: str | None, confidence: float) -> None:
    existing = (await db.execute(select(UnansweredQuery).where(UnansweredQuery.text == text))).scalar_one_or_none()
    if existing:
        existing.count += 1
    else:
        db.add(UnansweredQuery(id=str(uuid.uuid4()), text=text, intent=intent, confidence=confidence,
                               reason="Low classifier confidence"))


def _extract_sources(tool_calls: list[dict]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen = set()
    for tc in tool_calls:
        result = tc.get("result", {})
        if not isinstance(result, dict):
            continue
        cands = []
        if result.get("source"):
            cands.append({"tool": tc["name"], "source": result["source"]})
        for chunk in result.get("chunks", []) or []:
            cands.append({"tool": tc["name"], "source": chunk.get("source_doc_id", ""), "section": chunk.get("section", "")})
        for c in cands:
            key = (c["source"], c.get("section"))
            if key not in seen:
                seen.add(key)
                sources.append(c)
    return sources
