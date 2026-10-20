# UAEA Backend

**Urdu AI Educational Assistant** — the university student-services chatbot backend.
FastAPI + PostgreSQL (or SQLite for local runs) + **Groq** for understanding the
question and calling tools + **WhatsApp OTP** before any student's private record
is shown.

```
Student: "BSCS ki classes kab sy shru hongi?"        → answered for everyone
Student: "Roll no BSCS-2023-014 ka result dikhao"     → 6-digit code sent on WhatsApp
Student: "482913"                                     → verified → result table shown
```

---

## Quick start — local, no Docker (SQLite)

```bash
cd uaea-backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env            # macOS/Linux: cp .env.example .env
#  → put your Groq key in LLM_API_KEY  (free key: https://console.groq.com/keys)
#  → set DATABASE_URL=sqlite+aiosqlite:///./uaea.db

python -m app.db.seed --create-tables   # creates tables + loads the demo university
uvicorn app.main:app --reload --port 8000
```

Then in the project root: `npm run dev` and open http://localhost:5173/chat.

## Quick start — Docker (PostgreSQL + pgvector)

```bash
cd uaea-backend
cp .env.example .env        # set LLM_API_KEY
docker-compose up --build   # migrations + seed run automatically
```

Backend at http://localhost:8000, health check at `/health`, API docs at `/docs`.

---

## Groq (the LLM)

| Setting | Default | Notes |
|---|---|---|
| `LLM_API_KEY` | — | Your Groq key (`gsk_…`). Without a key the chat still works using the offline engine. |
| `LLM_MODEL` | `openai/gpt-oss-120b` | **`llama-3.3-70b-versatile` was shut down by Groq on 16 Aug 2026** — older `.env` files must be updated. |
| `LLM_FALLBACK_MODELS` | `qwen/qwen3.8-27b,openai/gpt-oss-20b` | Tried in order if a model is retired, rate-limited or returns nothing. |
| `LLM_REASONING_EFFORT` | `low` | gpt-oss models only; keeps replies fast. |

How a message is handled (`app/orchestrator/orchestrator.py`):

1. **Sanitise + classify** — prompt-injection stripping, language detection (English / Urdu / Roman Urdu), keyword intent label.
2. **OTP gate** — if this chat is waiting for a code, the code is checked *in code*, before the LLM. `resend` / `cancel` also handled here.
3. **Groq with 20 tools** — the model decides which database lookups to make (`app/orchestrator/tools.py`) and writes the answer from their results.
4. **Guardrails** — any amount or date in the reply that no tool returned is struck out; if the reply has several, the grounded offline answer is used instead.
5. **Fallback** — if Groq is unreachable, out of quota, or the key is missing, the **offline engine** (`app/orchestrator/offline.py`) answers from the same tools with templates.

The LLM is never the source of truth: fees, dates, grades, phone numbers all come from tool calls.

### Tools

| Public (anyone) | Private (WhatsApp OTP first) |
|---|---|
| `get_academic_calendar` — classes begin, mid/finals, holidays, orientation, convocation | `get_student_result` — GPA, CGPA, course grades |
| `get_fee_tariff`, `get_deadline`, `get_document_checklist` | `get_fee_status` — challan, dues, late fine |
| `list_programs`, `get_program_info` — eligibility, seats, duration | `get_attendance` — per course, 75 % warning |
| `get_class_timetable`, `get_courses`, `get_faculty` | `get_student_profile` — programme, semester, advisor, hostel |
| `get_scholarships`, `get_hostel_info`, `get_transport_routes` | |
| `get_department`, `list_campuses`, `search_knowledge_base` (54 policy chunks), `create_escalation_ticket` | |

---

## WhatsApp OTP for private records

Every student in the demo database has the WhatsApp number **+92 333 3797617**
(`DEMO_STUDENT_PHONE`). When anyone asks for a student's result, fee status,
attendance or profile:

1. The tool refuses to return data and instead creates an `otp_challenges` row and sends a 6-digit code to that student's WhatsApp.
2. The chat shows *"code sent to +92 333 •••7617"* with a code box.
3. The code is typed in the chat → checked by `app/services/otp.py` → the original question is answered.
4. That chat can see that roll number's records for `OTP_ACCESS_MINUTES` (15) without another code.

Security: codes are stored only as an HMAC, expire after 5 minutes, lock after 5 wrong tries, at most 6 codes per roll number per hour, 30 s resend cooldown, and are never sent to the LLM. General information (fees, calendar, timetables…) never needs a code.

### Delivering the code (`WHATSAPP_PROVIDER`)

| Provider | What you need | Good for |
|---|---|---|
| `console` (default) | nothing — the code is printed in the backend terminal: `[OTP console] WhatsApp to +923333797617: … code … is 482913` | development |
| `twilio` | Twilio account SID + auth token. With the **sandbox**, first send the join code (e.g. `join <two-words>`) from +92 333 3797617 to **+1 415 523 8886** on WhatsApp. | demos — works in minutes |
| `meta` | WhatsApp Cloud API token + phone-number ID and an approved **authentication** template (`META_WA_TEMPLATE`). | production |

Twilio sandbox `.env`:

```env
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

For a classroom demo without any WhatsApp account you can set `OTP_DEV_ECHO=true` — the code is then also shown in the chat. Never enable this in production.

---

## The demo database

`python -m app.db.seed` loads a deterministic dataset (same data on every machine):

| Table | Rows | | Table | Rows |
|---|---|---|---|---|
| programs | 19 | | students | 167 |
| campuses | 8 | | result_records | 540 |
| departments / offices | 32 | | fee_records | 707 |
| fee_tariffs | 59 | | attendance_records | 696 |
| services (with checklists) | 17 | | courses | 579 |
| deadlines | 14 | | timetable slots | 584 |
| academic calendar events | 37 | | faculty | 41 |
| scholarships | 9 | | hostels / bus routes | 8 / 8 |
| knowledge-base chunks | 54 | | | |

Demo roll numbers (all use WhatsApp +92 333 3797617):

| Roll number | Name | Notes |
|---|---|---|
| BSCS-2023-014 | Aisha Khan | 7th semester, CGPA 3.64, fees paid |
| BSSE-2024-011 | Ayesha Siddiqui | 25 % scholarship |
| BSCS-2024-007 | Ali Raza | hostel resident |
| BBA-2023-021 | Fatima Noor | Lahore campus |
| BSIT-2025-003 | Hamza Iqbal | fee **overdue** with late fine |
| BSAI-2024-002 | Zainab Ahmed | CGPA 3.78, 50 % scholarship |
| BSCS-2023-031 | Bilal Hussain | **probation**, short attendance, fee overdue |
| MSCS-2025-002 | Usman Tariq | MS student |
| BSPSY-2024-009 | Maryam Javed | |
| BSMATH-2025-012 | Hassan Ali | Multan campus |
| BED15-2025-040 | Sara Khan | Karachi campus |
| BSCS-2026-001 | Ahmed Raza | new 1st-semester student (no result yet) |
| MBA-2025-015 | Hira Malik | |
| BSENG-2024-018 | Noor Fatima | Peshawar campus |

Roll numbers are flexible in chat: `bscs 2023 14`, `BSCS-2023-014`, `bscs-2023-014` all work.

The data is fictional. "Today" is the real date in Pakistan; set `TODAY_OVERRIDE=2026-10-20` to reproduce the test-suite's view.

### Things students can ask (all answered from the database)

- *BSCS ki classes kab sy shru hongi?* · *mid term exams kab hain?* · *winter vacation kab hogi?*
- *BSCS ki fees kitni hai?* · *urgent transcript ki fees?* · *کمپیوٹر سائنس کی فیس کتنی ہے؟*
- *Admission ki last date?* · *BSAI eligibility* · *Quetta campus mein kaun se programs hain?*
- *BSCS 3rd semester timetable* · *BSSE 2nd semester ke courses* · *who teaches NLP?*
- *girls hostel fee Islamabad* · *Bahria se bus route* · *hafiz e quran concession*
- *minimum attendance kitni honi chahiye?* · *refund policy* · *LMS password bhool gaya*
- *NOC ke liye kya documents chahiye?* · *Rawalpindi campus ka number*
- *BSCS-2023-014 result* · *attendance bhi dikhao* · *BSIT-2025-003 fee status* → OTP first

---

## API

| Method | Path | |
|---|---|---|
| POST | `/v1/chat/message` | `{session_id, text}` → `{reply, intent, tool_calls, sources, otp, verified_roll, engine, model, …}` |
| GET | `/v1/chat/session/{id}` | conversation history |
| POST | `/v1/chat/escalate` | create a staff ticket |
| GET | `/v1/lookup/departments`, `/fee-tariff`, `/deadlines`, `/document-checklist` | original lookups |
| GET | `/v1/lookup/campuses`, `/programs`, `/programs/{code}`, `/calendar`, `/timetable`, `/courses`, `/faculty`, `/scholarships`, `/hostels`, `/transport` | public catalogue |
| * | `/v1/admin/…` | needs `X-API-Key` |

`otp` in the chat response is set when a code was sent: `{roll_number, masked_phone, expires_in_seconds, …}`.
Private records are never available through `/v1/lookup`.

```bash
curl -X POST http://localhost:8000/v1/chat/message -H "Content-Type: application/json" \
  -d '{"session_id":"demo-1","text":"BSCS ki classes kab sy shru hongi?"}'
```

---

## Tests

```bash
pytest -q          # 118 tests, in-memory SQLite, no API keys or network needed
```

Covers the original suite plus: the full OTP flow (wrong / expired / locked / resend / hourly cap / session isolation / hashing), the Groq tool-calling loop with a fake Groq client (fallback models, empty replies, outages, hallucinated numbers, malformed tool arguments), and 46 real student questions answered from the database.

---

## Layout

```
app/
  main.py, config.py, schemas.py
  api/            chat.py · lookup.py · admin.py
  db/             models.py (25 tables) · seed_data.py (reference data) · seed.py (generator) · session.py
  orchestrator/   orchestrator.py · tools.py · offline.py · formatters.py · entities.py
                  intent_router.py · normalizer.py · guardrails.py · clock.py
  services/       otp.py · whatsapp.py
  rag/            retrieve.py (pgvector, or BM25 keyword search) · ingest.py
alembic/versions/ 0001_initial.py · 0002_expanded_db_otp.py
tests/
```

Knowledge-base search uses pgvector when `EMBEDDING_API_KEY` is set (PostgreSQL only); otherwise BM25 keyword search, which needs nothing beyond the Groq key.
