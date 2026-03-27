# Phase 8: LangGraph Supervisor & Tavily Tooling - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 8-LangGraph Supervisor & Tavily Tooling
**Areas discussed:** RAG sufficiency, Tavily budget & failures, web provenance Phase 8 vs 9, f1api removal, LangGraph shape & FastAPI execution

---

## Gray-area selection

User selected all areas: **1, 2, 3, 4, 5** (batch discuss).

---

## Area 1 — RAG sufficiency (AGT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| A | Rules-only gate | |
| B | Hybrid: rules + GigaChat judge on borderline | ✓ |
| C | Always LLM judge after non-empty RAG | |

**Borderline definition**

| Option | Description | Selected |
|--------|-------------|----------|
| A | Retriever score band (thresholds in code + pytest) | ✓ |
| B | Judge when evidence exists + freshness-style intent signal | |
| C | Claude discretion heuristics | |

**User's choice:** Q1 **B**, Q2 **A**
**Notes:** Judge only on borderline scores; thresholds implementation-defined with tests.

---

## Area 2 — Tavily budget & failures

| Option | Description | Selected |
|--------|-------------|----------|
| A | 1 Tavily call per turn | ✓ |
| B | Up to 2 with reformulation | |

**Failure code**

| Option | Description | Selected |
|--------|-------------|----------|
| A | `WEB_SEARCH_UNAVAILABLE` (new code; Phase 5-style failed payload) | ✓ |
| B | Reuse `LIVE_UNAVAILABLE` | |
| C | `SEARCH_UNAVAILABLE` | |

**User's choice:** Q3 **A**, Q4 **A**
**Notes:** User asked why f1api was mentioned often when removing it — explained: prior art comparison only; new code avoids conflating with removed f1api/live path.

---

## Area 3 — Web provenance (Phase 8 vs Phase 9)

| Option | Description | Selected |
|--------|-------------|----------|
| A | URLs in `sources_block_ru` only; no `details.web` in Phase 8 | ✓ |
| B | Minimal `details.web` in Phase 8 | |
| C | Full WEB-01 in Phase 8 | |

**User's choice:** Q5 **A**

---

## Area 4 — f1api removal (SRCH-02)

| Option | Description | Selected |
|--------|-------------|----------|
| A | Remove from pipeline; delete/stub client; update tests | ✓ |
| B | Pipeline-only removal; keep deprecated module | |
| C | Feature flag | |

**User's choice:** Q6 **A**

---

## Area 5 — LangGraph shape & FastAPI execution

| Option | Description | Selected |
|--------|-------------|----------|
| A | Explicit supervisor-style named nodes | ✓ |
| B | Linear chain only, no explicit supervisor | |

| Option | Description | Selected |
|--------|-------------|----------|
| A | `asyncio.to_thread` / thread pool for sync graph | ✓ |
| B | Async-native only if supported | |

**User's choice:** Q7 **A**, Q8 **A**

---

## Claude's Discretion

None explicitly chosen — planner/implementer discretion on: LangGraph state schema, judge prompt, exact score bands, RU string for `WEB_SEARCH_UNAVAILABLE`, entity resolution inside vs outside graph.

## Deferred Ideas

- `details.web` + Streamlit — Phase 9 (WEB-01)
- Second Tavily hop — deferred / backlog
- README + credential smokes — Phase 10
