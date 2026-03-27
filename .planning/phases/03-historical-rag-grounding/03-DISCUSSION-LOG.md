# Phase 3: Historical RAG Grounding - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 03-historical-rag-grounding
**Areas discussed:** Retrieval pipeline shape, RU/EN entity alias strategy, Traceability output contract, Historical indexing boundary

---

## Retrieval Pipeline Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Inline in `/next_message` | Retrieval and grounding execute synchronously in request flow. | ✓ |
| Background queue | Decouple retrieval via async job and polling lifecycle. | |
| Separate retrieval service | Internal boundary for retrieval-specific orchestration. | |

**User's choice:** Inline in `/next_message`.
**Notes:** Prioritized low-complexity integration compatible with current API/session architecture.

---

## RU/EN Entity Alias Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical dictionary + normalization | RU/EN aliases map to canonical entities with dictionary-first matching. | ✓ |
| Fuzzy-primary matching | Fuzzy matching as default to maximize recall. | |
| Dictionary-first + fuzzy fallback | Deterministic primary strategy with fuzzy fallback. | |

**User's choice:** Canonical dictionary + normalization.
**Notes:** Favor predictable and testable behavior in initial retrieval grounding.

---

## Traceability Output Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Top-k evidence bundle | Include source IDs, snippets, entity tags, rank score. | ✓ |
| IDs + titles only | Lightweight references with limited explanation value. | |
| Full raw chunks | Maximum transparency with higher payload noise/size. | |

**User's choice:** Top-k evidence bundle.
**Notes:** Balances auditability with response clarity and contract stability.

---

## Historical Indexing Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Historical-only indexing | Phase 3 uses indexed historical `f1db` only; no live calls. | ✓ |
| Optional live fallback | Permit live API calls in Phase 3 when needed. | |
| Historical + near-live deltas | Add periodic near-live ingestion in this phase. | |

**User's choice:** Historical-only indexing.
**Notes:** Keeps Phase 3 boundary clean and defers live freshness policy to Phase 5.

---

## Claude's Discretion

- Exact retrieval `top_k` default.
- Evidence score threshold defaults.
- Internal retriever/alias/evidence module decomposition.

## Deferred Ideas

None.
