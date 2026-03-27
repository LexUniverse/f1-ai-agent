# Phase 6: GigaChat Classic RAG - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 replaces **primary answer synthesis** with **GigaChat classic RAG** on top of the **existing retrieval pipeline**: when there is **usable context** (historical **evidence** and/or **live summary** per routing), the model receives a **prompt that includes retrieved chunks** (and live facts when applicable) and returns a **Russian** answer while **preserving traceable citations** in API `details`. When **GigaChat fails or is unavailable**, `/next_message` uses **deterministic template synthesis** (legacy/`russian_qna` helpers) with **explicit fallback signaling** (machine-readable `details` **and** a **short fixed Russian** user-visible line). **`src/answer/gigachat_rag.py`** is the primary LLM module; **`russian_qna.py`** is reduced to **shared builders / template fallback only** (GC-03).

This phase does **not** deliver Streamlit (Phase 7) or change auth/async session contracts (Phase 2).

</domain>

<decisions>
## Implementation Decisions

### Routing & live path (GC-01, GC-02)
- **D-01:** **Historical-first** retrieval and Phase 5 **live gate** behavior stay as today: resolve → retrieve → format evidence → branch (non-empty evidence vs empty vs live).
- **D-02:** **GigaChat applies to both** (user choice **1B**): (a) **historical success** path when `evidence` is non-empty — prompt includes **chunks/evidence**; (b) **live-enriched success** path when historical evidence is empty but live fetch succeeds — prompt includes **`summarize_live_next_payload_ru`** (and related live context) **plus** whatever chunk grounding is allowed (may be minimal); **both** paths must still populate **`details.live`** when live data was used, per Phase 5.
- **D-03:** **Template fallback** when GigaChat errors/unavailable: use **equivalent deterministic** builders from the `russian_qna` helper surface so **facts are not silently invented** (GC-02).

### API shape & LLM mapping (GC-01, GC-03)
- **D-04:** **Preserve existing contract** (user choice **2A**): success responses keep **`structured_answer`** as **`StructuredRUAnswer`** and **`confidence`** as **`QnAConfidence`** (`src/models/api_contracts.py`). The **planner/implementation** maps or constrains GigaChat output into these types (parse/validate; repair or safe retry — **Claude’s discretion** on strategy).
- **D-05:** **`message`** remains the **short primary Russian line** for chat UIs (Phase 4). For **GigaChat** paths, **`message`** is still concise; richer content lives in **`structured_answer`**.

### Fallback transparency (GC-02)
- **D-06:** On **template fallback** after GigaChat failure (user choice **3B**): (a) set a **machine-readable** field in **`details`** (e.g. nested under `synthesis` / `model` — exact key names **Claude’s discretion**) recording **`route: "template_fallback"`** (or equivalent) and optionally **`gigachat_error_class`** for support; (b) include a **fixed short Russian phrase** in **`message`** (or tightly prescribed append) that **discloses** the answer was **not** produced by the LLM — wording is **implementation-defined once**, then **pytest-stable**.

### Confidence (QNA alignment under LLM)
- **D-07:** **Hybrid** (user choice **4C**): **`confidence.score` / `tier_ru`** remain **grounded in retrieval evidence** when evidence exists (same family as `qna_confidence_from_evidence`); **live-only** path may keep **`live_qna_confidence()`** or a **documented** variant — **Claude’s discretion** so long as tiers stay explainable. The model **must not** override numeric tier with self-reported “confidence” unless **capped** by evidence rules.
- **D-08:** **Qualitative caveats** (model uncertainty, missing chunk coverage) may appear **only** inside **`structured_answer.sections`** (or equivalent section bodies), **not** as conflicting **`QnAConfidence`** values.

### Claude's Discretion
- GigaChat **SDK** wiring, timeouts, **retry** count before fallback, prompt templates (RU/EN system mix), **JSON vs tool** extraction for structured mapping.
- Exact **`details`** key names for synthesis metadata; exact **Russian** fallback disclosure string once tests lock it.
- How much **historical chunk text** is injected on the **live** branch when evidence is empty (minimal vs expanded) within prompt budget.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, GC synthesis ownership
- `.planning/REQUIREMENTS.md` — **GC-01**, **GC-02**, **GC-03**
- `.planning/PROJECT.md` — v1.1 GigaChat + template fallback, local run boundary

### Prior phase contracts
- `.planning/phases/05-live-enrichment-freshness/05-CONTEXT.md` — live gate, `details.live`, `LIVE_UNAVAILABLE`, historical-first
- `.planning/phases/04-ru-q-a-answer-reliability/04-CONTEXT.md` — `message` vs `details`, structured answer, `RETRIEVAL_NO_EVIDENCE` semantics
- `.planning/phases/03-historical-rag-grounding/03-CONTEXT.md` — retrieval, evidence traceability

### Research / stack
- `.planning/research/STACK.md` — `gigachat`, `langchain-gigachat` versions and integration notes
- `.planning/research/SUMMARY.md` — stack rationale including GigaChat

### Implementation anchors
- `src/api/chat.py` — `/next_message` orchestration; integration point for `gigachat_rag` vs fallback
- `src/models/api_contracts.py` — `StructuredRUAnswer`, `QnAConfidence`, `EvidenceItem`, `LiveDetails`, `NextMessageResponse` shapes
- `src/answer/russian_qna.py` — template/fallback helpers (`build_structured_ru_answer`, live builders, confidence helpers)
- `src/retrieval/` — evidence formatting and retrieval (unchanged contract surface for Phase 6)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/api/chat.py`**: branches **historical evidence** vs **`RETRIEVAL_NO_EVIDENCE`** vs **live success**; builds `details` with `evidence`, `structured_answer`, `confidence`, and `live` on live path.
- **`src/answer/russian_qna.py`**: deterministic **`build_structured_ru_answer`**, **`qna_confidence_from_evidence`**, live **`build_live_structured_ru_answer`**, **`live_qna_confidence`**, **`summarize_live_next_payload_ru`** — intended to remain as **fallback/shared** after Phase 6.
- **`src/models/api_contracts.py`**: typed **`StructuredRUAnswer`** / **`QnAConfidence`**; Phase 6 must **populate these from GigaChat** or template path consistently.

### Established Patterns
- **Synchronous** handling inside **`/next_message`**; **Pydantic** `model_dump()` into **`details`** dict.
- **Phase 5**: **`details.code == "OK"`** for successes; consumers detect live via **`"live" in details`**.

### Integration Points
- New **`src/answer/gigachat_rag.py`**: **primary** call for **both** historical and (per D-02) **live success** synthesis; **`chat.py`** chooses LLM vs fallback based on GigaChat outcome.
- **Credentials**: GigaChat auth via **environment / secrets** — no keys in repo (**Claude’s discretion** for exact env names; document in plan).

</code_context>

<specifics>
## Specific Ideas

User selections from discuss-phase: **1B** (GigaChat on live path too), **2A** (strict schema mapping), **3B** (`details` flag + fixed RU disclosure on fallback), **4C** (hybrid confidence: evidence-grounded tiers, caveats in sections only).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-gigachat-classic-rag*
*Context gathered: 2026-03-27*
