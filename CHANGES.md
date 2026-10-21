# What changed (Oct 2026)

## 1. Groq now understands the chat and answers from the real database
- The student chat (`src/pages/student/Chat`) now calls the backend (`POST /v1/chat/message`) instead of the in-browser mock engine. The mock engine is only a fallback when the backend is down.
- `uaea-backend/app/orchestrator/` rewritten: Groq tool-calling over **20 database tools**, model fallbacks, offline engine when Groq is unavailable, stricter guardrails.
- **Groq retired `llama-3.3-70b-versatile` on 16 Aug 2026.** Default is now `openai/gpt-oss-120b` (fallbacks `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`). Your `.env` was updated; the Groq key is unchanged.

## 2. Much larger database
- 13 new tables (migration `0002_expanded_db_otp`): programmes, academic calendar, courses, timetable, faculty, scholarships, hostels, bus routes, students, results, fee records, attendance, OTP challenges.
- ~3,600 rows: 19 programmes, 8 campuses, 32 offices, 167 students with results / fees / attendance, 54 policy documents. Data lives in `app/db/seed_data.py` and `app/db/seed.py`.

## 3. WhatsApp OTP before private information
- Every student record uses WhatsApp **+92 333 3797617**.
- Result, fee status, attendance and profile need a 6-digit code sent to that number; general information (fees, class dates, timetables…) never does.
- Code check happens in code before the LLM; hashed codes, 5-min expiry, 5 attempts, resend cooldown, hourly cap, 15-min access window per chat.
- Delivery: `console` (log), Twilio WhatsApp, or Meta WhatsApp Cloud API — see `uaea-backend/README.md`.

## 4. More questions answered
- Intent classifier extended from 8 to 24 intents (calendar, timetable, courses, faculty, hostel, transport, scholarships, attendance, policies…), with whole-word matching for short keywords.
- Roman Urdu / Urdu / English, roll numbers typed loosely (`bscs 2023 14`), semesters (`teesra semester`), terms (`fall 23`).

## Fixes found while re-checking
- `alembic.ini` lacked `prepend_sys_path = .` → `alembic upgrade head` (and the Docker start command) failed with "No module named app".
- pgvector query used `:embedding::vector`, which SQLAlchemy doesn't treat as a parameter → switched to `CAST(:embedding AS vector)`; keyword (BM25) search added when embeddings aren't configured.
- `seed.py` re-seeded the database whenever it was imported.
- Guardrail mis-read amounts written as `Rs. 28,500` and didn't recognise dates like `2 November 2026`.
- Classifier substring matching ("hi" inside "chahiye", "pass" inside "password").
- Student header overflowed sideways on phones.
- `requirements.txt` pins that don't install on Python 3.13 (asyncpg, psycopg2-binary, numpy).

## Tests
`cd uaea-backend && pytest -q` → 118 passed (50 original + 68 new).
