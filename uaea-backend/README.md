# UAEA Backend

**Urdu AI Educational Assistant** — a university student-services chatbot backend.
Built with FastAPI, PostgreSQL + pgvector, Groq for LLM tool-calling, and
OpenAI embeddings.

---

## Quick Start (Docker)

```bash
cd uaea-backend

# 1. Copy env and fill in real keys
cp .env.example .env
# Edit .env: set LLM_API_KEY (get free key at https://console.groq.com) and EMBEDDING_API_KEY

# 2. Build and start everything
docker-compose up --build

# Backend is at http://localhost:8000
# Health check: http://localhost:8000/health
```

Docker automatically runs migrations, seeds demo data, and starts the server.

## Local Development (without Docker)

```bash
# 1. Install dependencies
cd uaea-backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 2. Start PostgreSQL with pgvector (requires Docker for the DB)
docker run -d --name uaea-pg \
  -e POSTGRES_USER=uaea -e POSTGRES_PASSWORD=uaea -e POSTGRES_DB=uaea \
  -p 5432:5432 pgvector/pgvector:pg16

# 3. Copy .env and configure
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Seed demo data
python -m app.db.seed

# 6. Start the server
uvicorn app.main:app --reload --port 8000

# 7. (Optional) Ingest sample documents into RAG
python scripts/ingest_sample_docs.py
```

## Run Tests

```bash
# Tests use an in-memory SQLite DB — no Postgres or API keys needed
pytest -v

# Run a specific test file
pytest tests/test_guardrails.py -v

# Run with coverage
pytest --tb=short -q
```

**Note:** Chat flow tests that involve the orchestrator's LLM call will use
guided-flow slot-filling logic (no real Anthropic API call) for admission,
fee challan, and degree flows. The guardrails, lookup, and RAG tool tests
run fully offline.

---

## API Endpoints

### Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/message` | Send message, get assistant reply |
| GET | `/v1/chat/session/{session_id}` | Full conversation history |
| POST | `/v1/chat/escalate` | Create escalation ticket |

### Lookup (public, same logic as LLM tools)

| Method | Path | Params |
|--------|------|--------|
| GET | `/v1/lookup/departments` | `region`, `query` |
| GET | `/v1/lookup/fee-tariff` | `program`, `category` |
| GET | `/v1/lookup/deadlines` | `service` |
| GET | `/v1/lookup/document-checklist` | `service` (required) |

### Admin (requires `X-API-Key` header)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/admin/content/faq` | Create/update FAQ chunk |
| POST | `/v1/admin/content/fee-tariff` | Create/update fee tariff |
| GET | `/v1/admin/analytics/intents` | Intent frequency counts |
| GET | `/v1/admin/queue/unanswered` | Low-confidence query queue |

---

## Example curl Requests

```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-001","channel":"web","text":"I want to apply for admission"}'

# Get conversation history
curl http://localhost:8000/v1/chat/session/demo-001

# List all departments
curl http://localhost:8000/v1/lookup/departments

# Filter departments by region
curl "http://localhost:8000/v1/lookup/departments?region=Islamabad"

# Get fee tariffs for BS CS
curl "http://localhost:8000/v1/lookup/fee-tariff?program=BS+Computer+Science"

# Get deadlines for Admission
curl "http://localhost:8000/v1/lookup/deadlines?service=Admission"

# Get document checklist for Degree Application
curl "http://localhost:8000/v1/lookup/document-checklist?service=Degree+Application"

# Escalate a conversation
curl -X POST http://localhost:8000/v1/chat/escalate \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-001","reason":"Cannot resolve fee issue"}'

# Admin: create a FAQ (requires API key)
curl -X POST http://localhost:8000/v1/admin/content/faq \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-admin-api-key" \
  -d '{"source_doc_id":"manual-update","text":"Late fee surcharge is Rs 500/week","section":"§3 Fees"}'

# Admin: get intent analytics
curl http://localhost:8000/v1/admin/analytics/intents \
  -H "X-API-Key: your-admin-api-key"

# Admin: get unanswered queue
curl http://localhost:8000/v1/admin/queue/unanswered \
  -H "X-API-Key: your-admin-api-key"
```

---

## Architecture

```
uaea-backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, rate limiting
│   ├── config.py               # pydantic-settings from .env
│   ├── schemas.py              # Pydantic request/response models
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models (12 tables, pgvector)
│   │   ├── session.py          # Async engine + session factory
│   │   └── seed.py             # Realistic demo data seeder
│   ├── api/
│   │   ├── chat.py             # POST /v1/chat/*
│   │   ├── lookup.py           # GET  /v1/lookup/*
│   │   └── admin.py            # /v1/admin/* (RBAC-protected)
│   ├── orchestrator/
│   │   ├── normalizer.py       # Roman Urdu / Urdu script normalization
│   │   ├── intent_router.py    # Keyword-based intent classifier
│   │   ├── state_machine.py    # Guided flow state tracking
│   │   ├── tools.py            # Anthropic tool schemas + implementations
│   │   ├── guardrails.py       # Hallucination check / strip step
│   │   └── orchestrator.py     # Main pipeline: normalize → classify → LLM → guard
│   ├── rag/
│   │   ├── ingest.py           # Chunk + embed + store (pgvector)
│   │   └── retrieve.py         # Top-k cosine search + rerank
│   └── adapters/
│       ├── base.py             # StudentSystemAdapter ABC
│       └── mock_adapter.py     # Canned responses for Phase 1
├── alembic/                    # Database migrations
├── tests/                      # pytest suite
├── scripts/
│   └── ingest_sample_docs.py   # CLI: ingest .txt/.pdf into RAG
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── README.md
```

### Conversation Pipeline

Every message goes through these stages:

1. **Normalizer** — strip prompt injection, detect language, fold Roman Urdu variants
2. **Intent Router** — keyword classifier → admission / fee_challan / degree / result / transcript / department_lookup / small_talk / knowledge_question
3. **State Machine** — for guided flows (admission, fee_challan, degree): prompt for slots, track progress across messages
4. **LLM + Tool Calling** — Anthropic Claude with 6 registered tools that query the DB
5. **Guardrails** — scan the LLM's draft for numbers/dates/document-requirements not backed by this turn's tool results; strip ungrounded claims
6. **Persist** — save conversation + messages to DB

### Core Rule: LLM Is Never a Source of Truth

Every fee, deadline, or document-checklist fact comes from a **tool call** to
structured data (PostgreSQL tables), never from the LLM's training data. The
guardrail step enforces this: any number or date in the reply that can't be
traced to a tool call result is stripped or replaced with an escalation note.

---

## Mocked vs Real

| Component | Status |
|-----------|--------|
| **StudentSystemAdapter** | Mocked (MockAdapter) — returns canned data. Real CMS/OAS adapter replaces it with zero code changes elsewhere. |
| **LLM (Groq)** | Real API calls via OpenAI-compatible endpoint. Free fast inference. |
| **Embeddings (OpenAI)** | Real API calls. Returns zero vectors when API key is placeholder (dev/test mode). |
| **Database** | Real PostgreSQL with pgvector. Tests use in-memory SQLite. |
| **RAG pipeline** | Fully functional with real chunking, embedding, and pgvector similarity search. |
| **Auth** | RBAC stub (API key check). Full OTP auth is Phase 2. |
| **Rate limiting** | Real slowapi middleware, per-IP. Per-session placeholder. |

---

## Guided Flows

### Fully Working (state-machine driven, slot-filling, tool calls)

1. **Admission & Enrolment** — asks for programme + campus, then fetches fee tariff, deadline, and document checklist via tools
2. **Fee Challan** — asks for programme + enrolment type, fetches fee tariff and deadline
3. **Degree Application** — no slots needed, fetches checklist, fee, and deadline directly

### RAG-Only Stubs (answered via knowledge base search)

- Result Enquiry
- Transcript / PRC
- Scholarship information
- Assignment queries
- General university information

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Default |
|----------|----------|---------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://uaea:uaea@localhost:5432/uaea` |
| `LLM_API_KEY` | For LLM | `gsk-REPLACE-ME` |
| `EMBEDDING_API_KEY` | For RAG | `sk-REPLACE-ME` |
| `CORS_ORIGINS` | Yes | `http://localhost:5173,http://localhost:3000` |
| `ADMIN_API_KEY` | Yes | `uaea-admin-dev-key-change-in-production` |

---

## Frontend Integration

The frontend API client is at `src/lib/api.js` (in the parent project).
It reads `VITE_API_URL` from the Vite env and exposes typed functions for
every backend endpoint.

```bash
# In the frontend project root (.env.local):
VITE_API_URL=http://localhost:8000
```

No frontend modifications were needed — the frontend currently runs entirely
on mock data (`src/mocks/`) with no API calls. The new `api.js` client is
ready to be wired in when the frontend is updated to consume the backend.
