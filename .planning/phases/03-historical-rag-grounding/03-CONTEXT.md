# Phase 3: Historical RAG Grounding - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Historical Formula 1 questions are answered from traceable retrieval over indexed `f1db` data in ChromaDB, with RU/EN entity alias matching. This phase establishes historical retrieval grounding only; live API enrichment remains out of scope until Phase 5.

</domain>

<decisions>
## Implementation Decisions

### Retrieval Pipeline Shape
- **D-01:** Retrieval executes inline in `/next_message` during Phase 3 (no queue/service split yet).
- **D-02:** Retrieval output is a required intermediate artifact before final answer synthesis.

### RU/EN Entity Alias Strategy
- **D-03:** Use a canonical RU/EN alias dictionary with normalized matching (dictionary-first).
- **D-04:** Phase 3 does not use fuzzy-first entity matching to avoid low-trust false positives.

### Traceability Output Contract
- **D-05:** Return top-k evidence items that include source ID, short snippet, entity tags, and rank score.
- **D-06:** Evidence records must be explicitly tied to final answer synthesis to satisfy traceability requirements.

### Historical Indexing Boundary
- **D-07:** Phase 3 indexes historical `f1db` snapshot data only.
- **D-08:** Phase 3 does not call live APIs; live enrichment and freshness logic are deferred to Phase 5.

### Claude's Discretion
- Exact top-k default and score threshold values.
- Chunk sizing/token window strategy for retrieval snippets.
- Internal module boundaries for retriever, alias resolver, and evidence formatter.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and acceptance anchors
- `.planning/ROADMAP.md` — Phase 3 goal, dependencies, and success criteria.
- `.planning/REQUIREMENTS.md` — `RAG-01`, `RAG-02`, `RAG-03` requirement definitions.
- `.planning/PROJECT.md` — trust-first constraints and RU-first product context.

### Prior phase compatibility
- `.planning/phases/01-access-control/01-CONTEXT.md` — session/auth constraints that retrieval flow must preserve.
- `.planning/phases/02-async-backend-contracts/02-CONTEXT.md` — typed contract and deterministic API behavior constraints.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/api/chat.py`: existing `/next_message` control point where inline retrieval should be inserted.
- `src/models/api_contracts.py`: typed response contract patterns to extend for evidence traceability fields.
- `src/sessions/store.py`: session status/state holder for retrieval processing outcomes.
- `src/main.py`: shared error-envelope normalization pattern to keep retrieval failures deterministic.

### Established Patterns
- API behavior is contract-first and deterministic (Phase 2 baseline).
- Unified machine-readable error envelope is already established.
- Minimal in-memory implementation style is preferred for current milestone scope.

### Integration Points
- Retrieval orchestration should attach to `/next_message` in `src/api/chat.py`.
- Evidence payload schema should be represented in `src/models/api_contracts.py`.
- Retrieval failure/status transitions should align with session lifecycle semantics in `src/sessions/store.py`.

</code_context>

<specifics>
## Specific Ideas

- Keep the first implementation straightforward and auditable: dictionary-first aliasing and explicit retrieval evidence payloads.
- Preserve clean phase boundaries by deferring live/freshness concerns to Phase 5.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-historical-rag-grounding*
*Context gathered: 2026-03-27*
