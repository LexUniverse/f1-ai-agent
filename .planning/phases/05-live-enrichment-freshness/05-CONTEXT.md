# Phase 5: Live Enrichment & Freshness - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Augment **`/next_message`** with **conditional calls to f1api.dev** so users get **current** Formula 1 data when **historical RAG alone is insufficient** and the question **requires live freshness**. Surface **`as_of`** (and related freshness metadata) on **live-dependent** successes. When the live API is **unavailable**, return a **clear degraded-mode** outcome with an explicit machine-readable code and **Russian user-visible copy**—without fabricating live facts.

This phase does **not** introduce LangGraph, Streamlit changes, or new roadmap capabilities beyond LIVE-01..03. It **preserves** Phase 4 behavior for **historical success** and the **`RETRIEVAL_NO_EVIDENCE`** path when **live is not applicable**.

</domain>

<decisions>
## Implementation Decisions

### Live-call trigger & routing (LIVE-01)
- **D-01:** **Always run historical retrieval first** (current `resolve_entities` → `retrieve_historical_context` → `format_evidence` order). No live calls before that completes.
- **D-02:** Consider a **live enrichment attempt** only when **both** hold: (a) the question **requires current/live data** per a **deterministic gate**, and (b) **either** `evidence` is **empty** after formatting **or** the gate marks the query as **live-primary** (e.g. standings, schedule, “who leads now”). For v1, prioritize the **empty-evidence** branch so behavior stays easy to test; **optional second branch** (live-primary with weak RAG) is **Claude’s discretion** if tests stay stable.
- **D-03:** **Live gate (intent):** Use a **normalized_query** (and/or original user text) check with an **explicit allowlist** of patterns/keywords (RU/EN) for “current”, “now”, “latest standings”, “next race”, “calendar”, etc. **Planner** maintains the list as code + tests; avoid LLM-based routing in this phase.
- **D-04:** If historical path already yields **non-empty evidence** and the question is **not** live-primary per D-03, **do not** call the live API—return the existing Phase 4 success payload.

### `details` / API contract (LIVE-01, LIVE-03)
- **D-05:** When live data contributes to a **successful** answer, include a **`details["live"]`** object (Pydantic-serialized to dict) alongside existing keys. **Minimum fields:** `as_of` (string, UTC ISO-8601 with `Z`), `provider` (literal `"f1api.dev"`). **Optional:** `resource` or `endpoint_key` for traceability/debug (Claude’s discretion).
- **D-06:** Keep **historical provenance** in `details["evidence"]` (f1db-backed). **Do not** mix live rows into `evidence` as fake `EvidenceItem`s unless the planner adds a **clear, tested** mapping; **default for v1:** `evidence` remains historical-only; live facts live under **`live`** (and/or a dedicated `live_facts` shape) so provenance stays auditable.
- **D-07:** **`message` (RU)** must remain a **short user-facing line**. When live is used, it **must visibly reflect freshness** (e.g. include an **`Актуально на …`** or equivalent substring tying to the same instant as `details.live.as_of`—exact wording Claude’s discretion).
- **D-08:** Success `details["code"]` remains **`"OK"`** for both purely historical and live-enriched successes; consumers use **`"live" in details`** to detect live usage (avoid proliferating success codes unless tests demand a distinct `OK_LIVE`).

### Degraded mode & outages (LIVE-02)
- **D-09:** On **timeout, transport error, HTTP 5xx, or open circuit** when a **live call was required** (gate passed), return **`status: "failed"`** with **`details["code"] == "LIVE_UNAVAILABLE"`**. **Do not** use `RETRIEVAL_NO_EVIDENCE` for API outages.
- **D-10:** **`details`** on that branch: include **`code`**, **`evidence": []`**, and **omit** `structured_answer` / `confidence` (same hygiene as abstention path). Optional: `details["live"]` with `{"error": "..."}` for debug—Claude’s discretion if tests lock it.
- **D-11:** **`message`** must be a **fixed Russian string** (single canonical template) that states that **live data is temporarily unavailable** and that the assistant **cannot answer the current-data part**—**no fabricated results**. Exact sentence Claude’s discretion; must be **pytest-stable**.

### Client resilience & `as_of` semantics (LIVE-03)
- **D-12:** Implement **`f1api.dev`** behind a **dedicated client module** (e.g. `src/integrations/` or `src/live/`) with **configurable timeout** (default **≤ 10s**), **bounded retries** on safe GETs (count/backoff: Claude’s discretion), and a **circuit breaker** after repeated failures.
- **D-13:** **`as_of`**: Prefer a **timestamp from the API payload** when the client can extract it; otherwise use **UTC ISO-8601** time of the **successful response completion** at the server. Always normalize to **UTC** with **`Z`** in JSON.
- **D-14:** **Caching (optional v1):** Short TTL cache for identical live requests is **Claude’s discretion**; if added, **`as_of` must still reflect** the **data freshness rule** (either API timestamp or cache + stale metadata—planner documents choice in PLAN).

### Claude's Discretion
- Exact **keyword/pattern list** for D-03 and any **low-score + live** heuristic.
- **Pydantic** names for nested `live` shapes beyond the minimum in D-05.
- **Circuit breaker** thresholds, **retry** counts, **cache TTL**.
- **Exact Russian strings** for D-07 and D-11 (must stay **test-locked** once chosen).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, LIVE-01..03
- `.planning/REQUIREMENTS.md` — LIVE-01, LIVE-02, LIVE-03 definitions
- `.planning/PROJECT.md` — RAG-first policy, f1api.dev mention, degraded-mode principle

### Prior phase contracts
- `.planning/phases/04-ru-q-a-answer-reliability/04-CONTEXT.md` — `details` vs `message`; abstention uses `failed` + `RETRIEVAL_NO_EVIDENCE`
- `.planning/phases/03-historical-rag-grounding/03-CONTEXT.md` — historical-only retrieval scope

### Research & architecture
- `.planning/research/PITFALLS.md` — retrieve → sufficiency → live; degraded mode; freshness pitfalls
- `.planning/research/ARCHITECTURE.md` — live API adapter boundary, supervisor pattern (defer graph to later; **this phase: FastAPI path only**)

### Implementation anchors
- `src/api/chat.py` — `next_message` integration point
- `src/models/api_contracts.py` — extend contracts for `live` sub-shapes as needed
- `src/retrieval/retriever.py` — historical retrieval (unchanged contract)

### External API
- `https://f1api.dev/docs` — endpoint surface, auth, rate limits (verify current docs during research)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets
- **`next_message`** already orchestrates **resolve → retrieve → format_evidence** and branches **ready vs `RETRIEVAL_NO_EVIDENCE`**.
- **Phase 4** builders in `src/answer/russian_qna.py` and **`structured_answer` / `confidence`** in **`details`** for historical success.

### Established patterns
- **Synchronous** request/response inside **`/next_message`** (no background workers).
- **Typed** Pydantic response models; **`details`** remains a **`dict`** with **`model_dump()`** for nested models.

### Integration points
- **Live client** should be injected or imported as a **thin adapter** from `chat.py` (or called via a small service function) to keep **HTTP/retry/circuit** logic out of the route body.
- **Session store** `set_status` continues to mirror **`failed` vs `ready`** outcomes; align **`failure_code`** with new **`LIVE_UNAVAILABLE`** when applicable.

</code_context>

<specifics>
## Specific Ideas

No additional product references beyond **f1api.dev** as the live provider and **UTC `as_of`** visibility on live-dependent answers. Open to standard HTTP client patterns (`httpx` or `urllib`—planner matches existing stack).

</specifics>

<deferred>
## Deferred Ideas

- **LangGraph / multi-agent** routing (named in PROJECT.md) — not part of Phase 5 delivery.
- **Merging historical + live** in one synthesized narrative with conflict resolution — only if explicitly planned; v1 may ship **live-only fallback when RAG is empty** first.
- **Docker / production deploy** — v2 / out of scope per REQUIREMENTS.

### Reviewed Todos (not folded)
- None (todo match-phase returned no items).

**None otherwise — discussion stayed within Phase 5 scope.**

</deferred>

---

*Phase: 05-live-enrichment-freshness*
*Context gathered: 2026-03-27*
