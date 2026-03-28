# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines **RAG over historical F1 data** with **web search (Tavily via LangChain)** when needed, orchestrated by a **LangGraph + LangChain** turn: a **supervisor** (GigaChat) **accepts or rejects candidate answers** from a **worker agent** that first answers **from RAG only**, then may run **one bounded web pass** (result ranking, **title-first** reasoning, **optional fetch of a single chosen page**) — no separate numeric “confidence” gate for acceptance. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.4 — Supervisor tuning, single-pass deep web, unified provenance UI

**Goal:** Fix **over-frequent AGT-05** (supervisor false negatives): ensure **only GigaChat** decides accept/reject — **audit** prompts, JSON failures, and any **legacy numeric thresholds** that are not product `confidence` but still bias behavior. Replace **two Tavily iterations** with **one search per turn** after RAG rejection: **rank** SERP-style results, **decide from titles/snippets** whether an answer is possible; if not, **fetch one chosen URL** and extract text for synthesis — then supervisor accepts or **one** terminal failure path. **Streamlit:** **one** collapsed block for **all** provenance (RAG context + web + synthesis metadata), **no duplicate** “Источники” sections, **clear Russian** labels. Ship **README / `.env` catalog** and **opt-in smokes** (carried from prior roadmap).

**Target features:**

- **Supervisor reliability:** Reproducible logging of reject reasons; conservative JSON-parse fallback reviewed; no hidden **0.xx** gates on accept path.
- **Web pass:** Single Tavily call → **URL selection** → **title/snippet sufficiency** branch → optional **single-page** read (bounded size/timeout) → single revised candidate → supervisor.
- **API:** Extend **`details`** (or documented shape) so UI can render **one** provenance payload (RAG evidence summary + web queries/results + optional fetch metadata).
- **Streamlit:** Chronological chat (**UI-04**); message first; **UI-06** unified expander (replaces duplicated expanders).
- **Docs:** **DOC-01**, **TST-01**.

**Key context:** Operators see **constant** “Не удалось найти достаточно надёжного ответа…” — likely **supervisor always false** (API/parse/strict prompt) rather than `tier_ru_from_max_score(0.55)` (used only in **template fallback copy**, not supervisor). v1.4 validates that hypothesis in code and simplifies the web loop.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability); *Phase 4 also shipped explicit confidence — **superseded by v1.3 (confidence removed)**.*
- ✓ Live enrichment after historical retrieval uses a deterministic gate, surfaces `LiveDetails` / `as_of` in responses, and returns a fixed Russian degraded message when f1api.dev is unavailable — validated in Phase 05 (live-enrichment-freshness)
- ✓ GigaChat classic RAG on historical paths with hybrid citations and explicit template fallback + disclosure when the LLM fails — validated in Phase 06 (gigachat-classic-rag); *confidence on that path superseded by v1.3.*
- ✓ Streamlit operator UI (`/start_chat`, status polling, `/next_message`) with citations and synthesis metadata; documented local **API + Streamlit** run — validated in Phase 07 (streamlit-ui-local-run); *UI confidence superseded by v1.3.*
- ✓ **LangGraph** turn with **RAG** + **Tavily (LangChain)** and **GigaChat**; **f1api.dev** removed from answer path — validated in Phase 08 (langgraph-supervisor-tavily-tooling); *linear orchestration superseded by v1.3 supervisor–agent loop.*
- ✓ **Supervisor–Agent 1** LangGraph (RAG-first, ≤2 Tavily rounds, AGT-05 terminal copy), **no `confidence`** in synthesis types or graph outputs, **`details.web`** when search used — validated in Phase 09 (supervisor-agent-graph-no-confidence-web-provenance).

### Active (v1.4)

- **AGT-06, AGT-07, SRCH-04, WEB-02, UI-06, DOC-01, TST-01** — see `.planning/REQUIREMENTS.md` (v1.4 section).

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.
- **Confidence as a product field** — removed in v1.3; not deferred for recalibration.

## Context

Backend is FastAPI with async endpoints and Pydantic models. Frontend is Streamlit. Historical data: f1db in ChromaDB. Web: **Tavily** (typically one shot per turn after supervisor rejects RAG) plus **optional HTTP fetch** of a single page for deeper context; **GigaChat** drives supervisor and worker prompts. Acceptance is **LLM-judged only** (no product confidence field).

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests (supervisor loops may tighten budgets per plan).
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment:** Local run — API + Streamlit; Docker not a milestone goal unless scoped later.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, web-second response policy (v1.2) | Stabilize quality | v1.3 keeps RAG-first **via Agent 1**; web only after **supervisor** rejection. |
| Explicit degraded-mode when web search fails | Prevent silent failures | Preserve; align copy with new terminal failure path where relevant. |
| v1.3: Supervisor judges answers | Linear sufficiency gate insufficient for answer quality | Supervisor accepts/rejects **full candidate answers** vs user question. |
| v1.3: Max two search iterations | Cost/latency + avoid infinite loops | Delivered in Phase 9; **v1.4 replaces** with **one** Tavily + optional single-page fetch. |
| v1.3: Remove confidence entirely | Misleading constant / no calibration | Drop from schemas, details, Streamlit, tests. |
| v1.4: Single web pass + fetch | Richer answers without double Tavily | Rank URLs → titles → optional one fetch → synthesize once. |
| v1.4: Supervisor false-negative audit | Operators hit AGT-05 too often | Trace rejects; fix parse fallback / prompts; confirm no numeric accept gate. |
| v1.4: Unified Streamlit provenance | Duplicate source blocks confuse operators | One expander: RAG + web + synthesis labels. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 — Milestone **v1.4** started: supervisor tuning, single-pass web, unified UI; roadmap phases 12–14.*
