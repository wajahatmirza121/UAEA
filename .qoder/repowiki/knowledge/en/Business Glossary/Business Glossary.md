---
kind: business_term
name: Business Glossary
category: business_term
scope:
    - '**'
---

### UAEAT
- Definition：Urdu AI Educational Assistant — the university student-services chatbot built for this project, providing guided flows for admission, fee challan, degree application, and RAG-backed answers for other services.
- Aliases：UAEA、UAEAT assistant

### guided flow
- Definition：A slot-filling dialogue state machine that drives students through multi-step university processes (Admission & Enrolment, Fee Challan, Degree Application). Each flow has defined slots to collect and action steps to execute once all slots are filled.
- Aliases：flow、guided_flow

### tool call
- Definition：A structured function invocation that Claude executes during a conversation turn to fetch deterministic data (fee tariff, deadline, document checklist, department lookup, RAG search, escalation ticket creation). Answers returned to students must be backed by tool-call results, never by the LLM's own generation.
- Aliases：tool_use、function call

### guardrail
- Definition：Post-generation step that scans the LLM's draft reply for numbers, dates, and document requirements and strips or rewrites any claim that cannot be traced to a tool-call result from that turn, replacing it with a 'connect to human' fallback.
- Aliases：hallucination guardrail、reply guardrail

### RAG
- Definition：Retrieval-Augmented Generation pipeline that ingests PDFs/text into semantically-chunked `KnowledgeChunk` records with embeddings, then performs top-k cosine similarity search over pgvector plus a basic section-header rerank to return cited sources to the LLM.
- Aliases：knowledge base、RAG pipeline

### StudentSystemAdapter
- Definition：Abstract interface defining how the orchestrator talks to external student information systems (fee status, results, assignments, service requests, request tracking). Currently implemented by `MockAdapter` returning canned data; designed to be swapped for real integrations later.
- Aliases：adapter、student system adapter

### UnansweredQuery
- Definition：Queue entry created when the intent classifier confidence drops below 0.4 and the query does not match a known guided flow. Used by the admin `/v1/admin/queue/unanswered` endpoint to surface low-confidence items for review.
- Aliases：unanswered queue、low-confidence queue

### escalation ticket
- Definition：Record created when a conversation is escalated (either explicitly via `/v1/chat/escalate` or automatically when the LLM exhausts tool-call rounds without resolving the request). Tracks reason, status, and assigned staff member.
- Aliases：ticket、escalation
