# Phase 4: RU Q&A Answer Reliability - Research

**Researched:** 2026-03-27
**Domain:** FastAPI + Pydantic response contracts, RU-facing Q&A payloads over grounded retrieval
**Confidence:** HIGH (codebase-local); MEDIUM (confidence calibration heuristics — validate in tests)

## User Constraints

Copied from `04-CONTEXT.md` — planner MUST honor.

### Locked decisions
- **D-01 / D-02:** Typed structured payload in `details` (sections, key facts, caveats — exact keys at implementation discretion) plus short Russian `message` as primary chat line.
- **D-03 / D-04:** Discrete Russian confidence tiers and/or optional numeric in `details`; user-facing copy always states confidence in understandable Russian.
- **D-05 / D-06:** Citations traceable to `evidence[]`; consistent numbering with API; RU-first labels in user-visible text; English/raw `source_id` in structured evidence.
- **D-07 / D-08:** Insufficient historical evidence → `status: "failed"`, `details.code` e.g. `RETRIEVAL_NO_EVIDENCE` (not `ready`). `ready` only for successful structured paths.

### Claude's discretion
- Exact Pydantic model names and `details` key names; confidence mapping rules; citation layout (inline vs «Источники»); RU wording templates.

### Deferred
- None for this phase. Live API / freshness = Phase 5.

## Summary

Phase 4 extends the existing `/next_message` path in `src/api/chat.py`, which already performs alias resolution, Chroma retrieval, `format_evidence`, and returns `NextMessageResponse` with `details` containing `evidence`. The main gap is **product-shaped Russian output**: structured sections, **explicit confidence**, and **citations** tied to evidence indices, while preserving the **failed + RETRIEVAL_NO_EVIDENCE** branch.

**Primary recommendation:** Add small Pydantic models under `src/models/api_contracts.py` for the structured QnA subset of `details`, implement a dedicated builder (e.g. `src/answer/` or functions in `src/api/chat.py`) that derives confidence from retrieval `rank_score` values, formats RU `message` + optional «Источники» block, and `model_dump()` into `details` beside existing keys. Verify with pytest on JSON shape and abstention behavior.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ (project) | Runtime | Existing project |
| FastAPI | (project) | HTTP API | Already used |
| Pydantic v2 | (project) | Schemas | Phase 2 contract discipline |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| pytest | (project) | Tests | Existing `tests/` |

**No new runtime dependencies** required for QnA shaping unless later UX needs a template engine (out of scope).

## Architecture Patterns

### Recommended flow (success path)
1. `resolve_entities` → `retrieve_historical_context` → `format_evidence` (unchanged).
2. **Build structured answer** from evidence list: sections (e.g. key fact + context), citation list with `ref` 1..N aligned with `evidence` order.
3. **Derive confidence** from scores (e.g. max or weighted top-k `rank_score`) → discrete RU tier + optional float in `details`.
4. Set `message` to one-line RU summary; put rich structure under `details` keys documented in plans.

### Anti-patterns
- **Switching insufficient-evidence to `ready`:** Violates D-07/D-08 and misleads clients.
- **Citations that do not map to `evidence[]` indices:** Breaks traceability (QNA-02 / RAG-03).
- **Subjective confidence without score grounding:** Hard to test; tie tiers to explicit thresholds in code and assert in tests.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ad-hoc JSON blobs | Untyped dict-only shapes | Pydantic models + `model_dump()` | Contract tests, OpenAPI alignment |
| New retrieval store | Extra DB for citations | Evidence list order as source of truth | Already populated in Phase 3 |

## Common Pitfalls

### Pitfall 1: OpenAPI / response_model too strict
**What goes wrong:** Nested models on `NextMessageResponse.details` can conflict with existing `dict` typing.
**How to avoid:** Keep `NextMessageResponse.details: dict` if needed; use composed models only for building then dump to dict (matches Phase 2–3 pattern).

### Pitfall 2: Drifting evidence order
**What goes wrong:** Citation `[2]` points to wrong snippet after sort/filter.
**How to avoid:** Build citations from the same list instance passed to `details["evidence"]` without reordering after citation assignment.

### Pitfall 3: Breaking existing tests
**What goes wrong:** `test_rag_grounding` expects `Историческая сводка` and `details.evidence`.
**How to avoid:** Preserve or migrate assertions to new `message` prefix/shape while keeping evidence populated.

## Open Questions

1. **Exact RU strings for confidence tiers** — pick three labels (e.g. высокая / средняя / низкая) and document thresholds in code comments + tests.
2. **Streamlit** — optional display of structured `details`; only if time in execution (not blocking API contract).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (project) |
| Config file | none — use existing `tests/` |
| Quick run command | `pytest tests/test_qna_reliability.py -q` (to be added) |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| QNA-01 | Structured RU answer in `message` + typed structure in `details` | unit/API | `pytest tests/test_qna_reliability.py -q` | ❌ Wave 0 |
| QNA-02 | Confidence (RU) + citations mapping to evidence | unit/API | `pytest tests/test_qna_reliability.py -q` | ❌ Wave 0 |
| QNA-03 | No evidence → `failed` + `RETRIEVAL_NO_EVIDENCE` | unit/API | `pytest tests/test_qna_reliability.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_qna_reliability.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_qna_reliability.py` — covers QNA-01..03
- [ ] Reuse `tests/conftest.py` `client` fixture
- [ ] Framework: existing pytest — no install

## Sources

### Primary (HIGH confidence)
- `src/api/chat.py` — current `/next_message` behavior
- `src/models/api_contracts.py` — `NextMessageResponse`, `EvidenceItem`
- `.planning/phases/04-ru-q-a-answer-reliability/04-CONTEXT.md` — locked decisions

## Metadata

**Research date:** 2026-03-27  
**Valid until:** 2026-04-27

## RESEARCH COMPLETE
