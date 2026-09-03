---
kind: external_dependency
name: LLM Provider — Anthropic Claude with Tool Calling
slug: anthropic-claude
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### Role
Primary LLM for the UAEA conversational orchestrator. All student-facing replies are generated via Claude, which is invoked with tool definitions so it can call structured DB lookups (fee tariff, deadline, document checklist, department) and RAG search before answering.

### Integration points
- `AsyncAnthropic` client instantiated in `orchestrator._run_llm_with_tools` using `settings.anthropic_api_key` from `.env`.
- Model pinned to `claude-sonnet-4-20250514`; system prompt enforces that fees/deadlines/document requirements must come from tool-call results only.
- Tool-use loop runs up to `MAX_ROUNDS=6`, feeding each tool result back into the message history until a pure-text reply or escalation is produced.

### Stable usage notes
- If the API key is missing or invalid, the orchestrator returns a graceful fallback message rather than raising.
- Admin RBAC on `/v1/admin/*` routes uses a separate `admin_api_key` env var, not the Anthropic key.