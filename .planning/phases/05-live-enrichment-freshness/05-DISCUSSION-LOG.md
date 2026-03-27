# Phase 5: Live Enrichment & Freshness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `05-CONTEXT.md`.

**Date:** 2026-03-27
**Phase:** 05-live-enrichment-freshness
**Areas discussed:** Live-call trigger & routing; API contract & `as_of`; Degraded mode; Client resilience

---

## Area selection

**Prompt:** Which of the four proposed areas to discuss?

| Option | Description | Selected |
|--------|-------------|----------|
| 1 | Live-call trigger & routing | ✓ |
| 2 | `details` / API contract for live + `as_of` | ✓ |
| 3 | Degraded-mode UX & codes | ✓ |
| 4 | Client resilience & freshness semantics | ✓ |

**User's choice:** `all` (all four areas)

**Notes:** User elected full coverage; decisions finalized using session recommendations aligned with Phases 3–4 contracts, ROADMAP success criteria, and `.planning/research` guidance.

---

## 1. Live-call trigger & routing

| Approach | Description | Selected |
|----------|-------------|----------|
| A | Historical first; live only after RAG, behind deterministic gate | ✓ |
| B | Parallel RAG + live always | |
| C | LLM decides when to call live | |

**User's choice:** A — deterministic gate + empty-evidence priority for v1; keyword/pattern list for “current data” intent; no live if strong historical success unless live-primary (optional branch).

**Notes:** Keeps tests predictable and matches RAG-first product rule.

---

## 2. `details` / API contract & `as_of`

| Approach | Description | Selected |
|----------|-------------|----------|
| A | Nested `details["live"]` with `as_of`, `provider`; keep historical `evidence` f1db-only | ✓ |
| B | Fold live into `evidence` as synthetic items | |
| C | Separate HTTP resource / new endpoint | |

**User's choice:** A — `code` stays `OK` for success; presence of `live` signals enrichment; `message` includes freshness cue in Russian.

---

## 3. Degraded mode (LIVE-02)

| Approach | Description | Selected |
|----------|-------------|----------|
| A | `failed` + `LIVE_UNAVAILABLE` + fixed RU `message`; no `structured_answer` | ✓ |
| B | `ready` with degraded flag and partial answer | |
| C | Reuse `RETRIEVAL_NO_EVIDENCE` | |

**User's choice:** A — distinct code from RAG abstention; stable copy for tests.

---

## 4. Client resilience & `as_of` semantics

| Approach | Description | Selected |
|----------|-------------|----------|
| A | Dedicated client module; timeout ≤10s; retries + circuit breaker; `as_of` UTC from API or server clock | ✓ |
| B | Inline `requests` in route without breaker | |

**User's choice:** A — optional short TTL cache left to planner discretion.

---

## Claude's Discretion

- Exact RU strings (freshness line + outage line) once chosen in implementation.
- Keyword list, breaker thresholds, retry counts, optional cache.

## Deferred Ideas

- LangGraph orchestration, Docker packaging, advanced historical+live merge — noted as out of scope for Phase 5.
