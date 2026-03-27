# Phase 6: GigaChat Classic RAG - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace **template-only** Russian synthesis on the **historical-evidence success path** with **GigaChat classic RAG**: retrieval chunks feed the model prompt; the response remains **Russian**, **grounded**, and **traceable** in API `details` (citations / evidence linkage preserved per GC-01). On **GigaChat outage or hard failure**, use **deterministic template** behavior (**no silent fabrication**, GC-02). **Primary implementation** lives in **`src/answer/gigachat_rag.py`**; **`russian_qna.py`** becomes **shared helpers and/or template-fallback only** (GC-03).

This phase does **not** ship Streamlit (Phase 7) or change the async session contract. It does **not** replace Phase 5 **live** success behavior unless explicitly replanned.

</domain>

<decisions>
## Implementation Decisions

### Routing: historical vs live (scope with Phase 5)
- **D-01:** **GigaChat applies only** when the **historical evidence branch** succeeds (`evidence` non-empty after formatting), replacing today’s `build_structured_ru_answer` + templated `message` for that branch.
- **D-02:** The **live-enriched success path** (no historical evidence, live gate passed, upstream OK) stays **fully deterministic** — continue using existing `summarize_live_next_payload_ru`, `live_fresh_user_message_ru`, `build_live_structured_ru_answer`, `live_qna_confidence` — **no GigaChat** on that path for v1.1 unless a later phase explicitly changes it.

### API / `details` shape (compatibility with Phase 4 & 7)
- **D-03:** Preserve the existing **`structured_answer`** and **`confidence`** shapes in `details` on success (Pydantic types in `api_contracts`). The LLM path must **populate or map** into **`StructuredRUAnswer`** and **`QnAConfidence`** (validation, repair, or constrained decoding — planner/implementation discretion).
- **D-04:** **`message`** stays a **short Russian** primary line for chat UIs; richer content remains in **`details`** (Phase 4 pattern).

### GigaChat failure → template fallback (GC-02)
- **D-05:** On **GigaChat error, timeout, or documented outage**, fall back to **current template synthesis** from shared helpers (equivalent factual behavior to pre–Phase 6 historical success: structured + confidence from evidence rules **without inventing facts**).
- **D-06:** Expose **machine-readable** fallback metadata in `details` on that path (e.g. a dedicated key such as `synthesis` / `synthesis_source` with value indicating **`template_fallback`** and an optional **reason code**). **No requirement** for an extra user-visible Russian “fallback” sentence in `message` unless tests or Phase 7 UX need it (**Claude’s discretion**).

### Confidence with LLM (trust)
- **D-07:** **Baseline confidence tiers** for the GigaChat success path remain **evidence-derived** (same family of logic as `qna_confidence_from_evidence`: scores from retrieval/evidence). The model may add **qualitative caveats** inside **`structured_answer`** sections if useful; it **must not** force a **higher** confidence tier than the evidence pipeline allows without a documented, tested rule.

### Claude's Discretion
- GigaChat client wiring (`gigachat` vs `langchain-gigachat`), timeouts, **single vs double** invoke before fallback, and exact **`details`** key names for D-06.
- Prompt wording and whether system instructions are RU, EN, or bilingual (must not break RU user-facing output and citation rules).
- Exact validation strategy for mapping messy LLM output into `StructuredRUAnswer`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, GC alignment.
- `.planning/REQUIREMENTS.md` — **GC-01**, **GC-02**, **GC-03**.
- `.planning/PROJECT.md` — v1.1 GigaChat RAG + template fallback; local run note (Phase 7 / RUN-01).

### Prior phase contracts
- `.planning/phases/05-live-enrichment-freshness/05-CONTEXT.md` — live branch, `details.live`, `LIVE_UNAVAILABLE`, historical-first ordering.
- `.planning/phases/04-ru-q-a-answer-reliability/04-CONTEXT.md` — `structured_answer`, `confidence`, `message` vs `details`, abstention `failed` + `RETRIEVAL_NO_EVIDENCE`.
- `.planning/phases/03-historical-rag-grounding/03-CONTEXT.md` — retrieval/evidence traceability.

### Stack / provider notes
- `.planning/research/STACK.md` — GigaChat SDK and `langchain-gigachat` versions and roles.

### Implementation anchors
- `src/api/chat.py` — `/next_message` orchestration; historical vs live branching.
- `src/answer/russian_qna.py` — template builders and confidence helpers to retain or extract for fallback.
- `src/models/api_contracts.py` — `StructuredRUAnswer`, `QnAConfidence`, `EvidenceItem`, `NextMessageResponse` / `details` patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`next_message`** already resolves entities, retrieves, formats **`evidence`**, and builds success **`details`** with **`structured_answer`** and **`confidence`** on the historical path.
- **`russian_qna.py`** provides **`build_structured_ru_answer`**, **`qna_confidence_from_evidence`**, and live helpers — fallback and shared formatting should reuse or thinly wrap these.

### Established Patterns
- Contract-first **`details`** dict with **model_dump** for nested models; **`code: OK`** for successes; live vs historical provenance split from Phase 5.

### Integration Points
- New **`gigachat_rag.py`** should be called from **`chat.py`** only on **non-empty evidence** success routing, before assembling the response; fallback closes back to template helpers on failure.

</code_context>

<specifics>
## Specific Ideas

User selected **all four** discuss-phase gray areas; decisions **D-01–D-07** match the **recommended defaults** articulated in the same session (deterministic live path; preserve `details` schema; machine-readable fallback signaling; evidence-grounded confidence). Adjust in planning if product intent changes.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-gigachat-classic-rag*
*Context gathered: 2026-03-27*
