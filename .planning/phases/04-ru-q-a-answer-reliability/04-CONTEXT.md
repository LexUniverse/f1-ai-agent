# Phase 4: RU Q&A Answer Reliability - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver **structured Russian answers** with **explicit confidence** and **source citations**, while **preserving current abstention semantics** for insufficient historical evidence: `status: "failed"` with a machine-readable code such as `RETRIEVAL_NO_EVIDENCE` (no switch to `ready` for that case). This phase sits on top of Phase 3 inline retrieval and evidence payloads; **live API enrichment and freshness remain Phase 5**.

</domain>

<decisions>
## Implementation Decisions

### Structured answer shape (QNA-01)
- **D-01:** Expose a **typed structured payload in `details`** (e.g. sections, key facts, caveats — exact keys are planner/implementation discretion) alongside a **short Russian `message`** as the primary user-facing line in chat UIs.
- **D-02:** `message` should remain a concise RU summary; richer structure lives in `details` for contract tests and clients.

### Confidence (QNA-02)
- **D-03:** **Claude’s discretion** for the concrete confidence representation: use **discrete Russian tiers** and/or an **optional numeric** field in `details`, with a documented mapping derived from retrieval/evidence strength and synthesis policy.
- **D-04:** User-facing copy must **always** state confidence in an understandable Russian form (tier or equivalent).

### Citations (QNA-02)
- **D-05:** **Claude’s discretion** to choose **inline numbered references** in prose vs a **trailing «Источники»** block (or a combination), provided every substantive claim is **traceable to `evidence[]`** and numbering/order stays consistent with the API.
- **D-06 (3b — not explicitly chosen):** Default **RU-first** labels in user-visible text; retain **English/raw `source_id` and snippets** in structured evidence for bilingual grounding, unless a later UX pass specifies otherwise.

### Abstention / insufficient evidence (QNA-03)
- **D-07:** **Keep existing behavior** for insufficient historical evidence: respond with **`status: "failed"`** and an appropriate **`details.code`** (e.g. `RETRIEVAL_NO_EVIDENCE`), not a `ready` abstention response.
- **D-08:** Reserve **`status: "ready"`** for successful answer paths where structured RU content, confidence, and citations are present; use **`failed`** for true errors and for **zero/insufficient evidence** per D-07.

### Claude's Discretion
- Exact Pydantic models and `details` key names for structured sections.
- Confidence mapping rules (tiers, optional numeric) and calibration notes.
- Citation layout (inline vs block) within D-05 constraints.
- Wording templates for Russian summaries and error messages where not already fixed by prior phases.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, dependencies (Phase 3).
- `.planning/REQUIREMENTS.md` — `QNA-01`, `QNA-02`, `QNA-03` definitions.
- `.planning/PROJECT.md` — RU-first UX, trust/accuracy, latency constraints.

### Prior phase context (compatibility)
- `.planning/phases/03-historical-rag-grounding/03-CONTEXT.md` — inline retrieval, evidence contract, traceability, no live API.
- `.planning/phases/02-async-backend-contracts/02-CONTEXT.md` — `NextMessageResponse` and deterministic API/error envelope patterns.
- `.planning/phases/01-access-control/01-CONTEXT.md` — session auth gate before chat processing.

### Implementation anchors
- `src/api/chat.py` — `/next_message` orchestration and current evidence attachment.
- `src/models/api_contracts.py` — `NextMessageResponse`, `EvidenceItem`, retrieval-related models.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/api/chat.py`: `/next_message` already resolves entities, retrieves context, formats evidence, sets session status, and returns `NextMessageResponse` with `details` including `evidence`.
- `src/models/api_contracts.py`: `EvidenceItem`, `NextMessageResponse` — extend or nest structured answer/confidence fields in `details` while preserving Phase 2 contract discipline.
- `src/retrieval/evidence.py`, `src/retrieval/retriever.py`, `src/retrieval/alias_resolver.py`: existing grounding pipeline to drive confidence/citation logic.

### Established Patterns
- Contract-first Pydantic models; machine-readable `details.code` on failures.
- Evidence list with `used_in_answer` and traceability from Phase 3.

### Integration Points
- Extend structured output in `next_message` success path; keep failure path consistent with D-07/D-08.
- Frontend (Streamlit) can show `message` first and optionally render structured `details` when present.

</code_context>

<specifics>
## Specific Ideas

- User chose **typed `details` + short RU `message`** (1A), **planner/implementation discretion on confidence and citation layout** (2C, 3C), and **retain `failed` + `RETRIEVAL_NO_EVIDENCE` for insufficient evidence** (4B).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-ru-q-a-answer-reliability*
*Context gathered: 2026-03-27*
