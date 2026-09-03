# UAEA Console

Front end for **UAEA — Urdu AI Educational Assistant**: the student-facing site
and the staff governance console, on one shared data layer. Phase 1, running
entirely on mocks.

_"Your University. Your Language. Your AI Assistant."_

---

## Running it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production bundle into dist/
npm run preview  # serve the built bundle
```

Node 18 or newer. No environment variables, no backend, no database — the whole
console runs on fixtures.

---

## The idea behind the design

This is not an analytics dashboard. It is a **governance** console.

The architecture doc puts the central risk plainly: the danger is not that the
model writes an awkward sentence, it is that it states a fee, a deadline or a
document checklist that is wrong. So the LLM is a conversational interface, never
a source of truth — every number comes from a governed table or a cited chunk.

That makes `last_verified_at` the most important field in the system, and it is
the visual spine of this interface. The **freshness ladder** — four rungs that
drain as a record ages away from its last human check — appears identically in
table rows, dashboard lists and history drawers.

**Jade means a human vouched for this, and nothing else.** It is never used for
decoration, so green on this screen always carries the same promise.

The palette is charcoal-free by default: a cool paper white with a brass accent,
because this console governs stamped, dated, official paper. Dark theme ships too
and is one toggle away in the top bar.

---

## Two faces, one catalogue

| Route | Who it is for |
|-------|---------------|
| `/`   | **Students.** Landing page, chat, service directory, department contacts |
| `/admin` | **Staff.** The governance console that keeps the answers correct |

An editor changing a fee in the console changes what the assistant tells
students on the very next message — same store, no sync step.

---

## Student pages

| Route | What it does |
|-------|--------------|
| `/` | Landing: ask box, live Autumn 2026 deadlines, how the trust model works, services by department |
| `/chat` | The assistant. Classifies → routes → looks up → cites, in Urdu, Roman Urdu or English |
| `/services` | Every service, filterable by owning department, searchable |
| `/services/:id` | Full requirements: documents with original-vs-copy flags, fee, deadline, who handles it |
| `/directory` | Campus and department contacts, phone numbers as `tel:` links |

### How query routing works

Ask something and you will see a routing card appear *before* the answer:

> Looks like **Fee challan** · Finance · handled by Directorate of Finance — 96% match

That is deliberate. A student who can see their fee question went to Finance
knows immediately when it has gone somewhere wrong, instead of finding out three
replies later.

The classifier lives in `src/lib/classify.js` — deterministic keyword scoring
over both scripts, with a normaliser that folds Roman Urdu spelling variants
(`fees`/`fis`/`phees` → `fee`) and Urdu **stems** rather than whole words, so
داخلہ and داخلے both match. Below `CONFIDENCE_FLOOR` it refuses to answer and
hands over the right office with its number and opening hours.

The answer engine is `src/lib/assistant.js`. It only ever states what a tool
call returned, and it reads intent from the phrasing: *"rechecking ki fees"*
gets the amount, *"NOC ke liye kya documents"* gets the checklist first.

Both are stand-ins for §4.3.2 and §4.3.4. Replacing them with an API call is a
two-file change.

---

## Staff console pages

| Route             | What it does |
|-------------------|--------------|
| `/admin`          | Success metrics (§13), volume, intent mix, catalogue freshness, guardrail interventions |
| `/admin/content`        | Services, fee tariff, deadlines, departments — the deterministic backbone (§4.4, §6) |
| `/admin/documents`      | RAG source documents, ingestion states, retrieval tester (§5.3) |
| `/admin/flows`          | Guided-flow state machines with a live validator and step-through simulator (§4.3.3) |
| `/admin/queue`          | Unanswered and low-confidence queries, the content growth loop (§4.6) |
| `/admin/conversations`  | Transcripts with the grounding tool calls left visible (§4.3) |
| `/admin/escalations`    | Human handoff tickets |
| `/admin/integrations`   | Adapter registry — mock vs real, per-method coverage (§4.5, §15) |
| `/admin/audit`          | Append-only record of who changed what, and when (§9) |
| `/admin/guardrails`     | Answer rules, handover threshold, model selection (§5.4) |

---

## Things worth knowing

**Role switching.** Click your name at the bottom of the sidebar. Switching to
*Analytics viewer* genuinely removes write controls across every page, not just
the buttons. The `PERMS` map in `src/lib/rbac.js` is deliberately shaped the way
the API middleware should be — hiding a delete button is a courtesy, not a
security control, and Phase 2 must enforce the same map server-side.

**Change impact.** Editing a record shows a plain-language diff plus how many
students asked about it in the last 90 days, before you can save. Someone
changing a fee from Rs 28,500 to Rs 31,000 should see the number of conversations
that will quote it.

**Flow validation.** A draft flow cannot be published while it ends on an `ask`
step, has no hand-off, or consumes a slot before collecting it. Try opening the
Transcript flow — it is deliberately broken so the checks are visible.

**⌘K** opens the command palette from anywhere. Actions your role cannot perform
are filtered out of it.

---

## Layout

```
src/
├── main.jsx                    entry point
├── App.jsx                     routes
├── styles/                     tokens → base → layout → components
├── lib/                        format, freshness, rbac, csv, constants,
│                               classify (intent router), assistant (answers)
├── hooks/                      useDebounced, useCountUp, useEscape, useHotkey
├── context/                    AppContext (state + mutate), ToastContext
├── mocks/                      one file per entity, barrelled through index.js
├── components/
│   ├── ui/                     Button, Modal, Drawer, Ladder, Badge, …
│   ├── charts/                 hand-rolled SVG, themed through CSS classes
│   ├── layout/                 AppShell, Sidebar, Topbar, CommandPalette
│   ├── data/                   DataTable, TableToolbar, Pagination
│   ├── content/                RecordModal, ChecklistEditor, history, columns
│   └── student/                shell, header, footer, ask bar, cards
└── pages/
    ├── student/                Landing, Chat, Services, Directory
    └── …                       staff console pages
```

Charts paint through CSS classes rather than hex attributes, which is why they
re-theme for free when you flip to dark.

---

## Phase 2: wiring the backend

Every write in the console goes through **one function** in
`src/context/AppContext.jsx`:

```js
mutate(table, id, patch, meta)
//  id === null      → create   POST   /v1/admin/content/{table}
//  patch === null   → delete   DELETE /v1/admin/content/{table}/{id}
//  otherwise        → update   PATCH  /v1/admin/content/{table}/{id}
//  meta = { action, record, changes }  feeds the audit trail
```

Nothing else in the tree touches data directly. Grep for `↯ API SEAM` to find
every point where a fetch call replaces a `setTimeout`:

```bash
grep -rn "API SEAM" src/
```

Suggested order:

1. **Permissions middleware and the audit table first.** Both exist in the UI
   already; building them into the API from the first endpoint is much cheaper
   than retrofitting.
2. Schema and ORM models from `src/mocks/*` — the shapes there are the tables.
3. Swap `mutate()` for real requests, one table at a time.
4. Auth, input sanitisation, error handling.

---

## Not built yet

Honest list, so nothing is a surprise later:

- **WhatsApp.** The web channel is here; the Business API side (§4.1) is not.
- **Real NLU.** The classifier is keyword scoring, not a trained model. It
  handles the cases in `src/lib/classify.js` well and will miss phrasings that
  are not in the rules — which is exactly why it escalates rather than guesses.
- **Login.** No OTP or roll-number auth, so nothing personal is ever shown.
- **Intent management.** You can see intent distribution but not edit the intent
  list or its training examples.
- **Per-step drop-off analytics** inside a flow. Flow-level drop-off is shown;
  step-level is not.
- **Voice, OTP auth, deadline reminders, the transactional layer.** All Phase 2
  and 3, and correctly absent — informational accuracy has to be proven first.
