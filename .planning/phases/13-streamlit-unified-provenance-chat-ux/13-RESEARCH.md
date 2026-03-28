# Phase 13 — Technical research: Streamlit unified provenance & chat UX

**Phase:** 13 — Streamlit Unified Provenance & Chat UX  
**Question:** What do we need to know to plan UI-04 / UI-05 / UI-06 well?

---

## Current implementation (`streamlit_app.py`)

- **Ordering bug (UI-04):** Successful send uses `st.session_state.messages.insert(0, …)` twice (user, then assistant), so **newest pair is at index 0** and the `for msg in messages` loop shows **newest at top** — opposite of required **chronological append** (oldest top, newest above composer).
- **Provenance (UI-06):** `_render_assistant_block` always shows **«Источники»** from `structured_answer.sources_block_ru`, then **«Веб-поиск»** `st.json(web)`, then **«Live»** `st.json(live)`, then **«Синтез»** — duplicates hierarchy when API already sends **`details["provenance"]`** (Phase 12).
- **Live label:** English **"Live"** expander; CONTEXT **D-07** requires **«Актуальные данные (live)»**.

---

## API shape (consumer reference)

- **`details["provenance"]`** — built in `src/graph/f1_turn_graph.py` via `_build_provenance_snapshot`: `{ "rag": { normalized_query, evidence[] }, "synthesis": {...}, "web"?: { queries, results, fetch? } }`.
- Validated in `src/api/chat.py` with `ProvenanceSnapshot.model_dump()` when parse succeeds.
- **Legacy:** `structured_answer`, `details["web"]`, `details["synthesis"]` still present for older responses — Streamlit must **branch**: unified path vs legacy per **13-CONTEXT D-04–D-06**.

---

## Streamlit constraints

- **`st.chat_message` + loop:** Order of iteration = visual order; **append-only** `messages` list matches oldest→newest with composer below container.
- **Testing:** No heavy Streamlit e2e in repo today. **Low-friction approach:** extract **pure** helpers (e.g. `provenance_nonempty(details) -> bool`, optional markdown/table builders) under `src/ui/` and **`pytest`** them; keep `st.*` only in `streamlit_app.py`. Matches **13-CONTEXT** canonical ref to extend `tests/test_streamlit_client.py` or add sibling tests.

---

## Risk: empty `provenance` dict

- Graph may attach `provenance` with empty `rag.evidence` but keys present — **D-04** says “non-empty dict (has at least `rag` or usable web/synthesis)”. Plan should define **predicate** aligned with CONTEXT (e.g. truthy `provenance` dict AND (`evidence` non-empty OR `web` block OR non-empty `synthesis`)).

---

## Validation Architecture

| Dimension | Approach |
|-----------|----------|
| **1–7** | Requirements UI-04–06 traced in PLAN tasks; acceptance via grep + pytest |
| **8 (Nyquist)** | Wave 0: existing `pytest`; add **`tests/test_provenance_display.py`** (or similar) for pure helpers; manual spot-check Streamlit optional for `/gsd-verify-work` |
| **Feedback loop** | After each task: `python3 -m pytest tests/test_provenance_display.py tests/test_streamlit_client.py -q` |

**Test commands:** `python3 -m pytest tests/test_provenance_display.py tests/test_streamlit_client.py -q` (quick); full offline: `python3 -m pytest tests/ -q --ignore-glob='*integration*'`.

---

## RESEARCH COMPLETE

Ready for planning: ordering fix, provenance-first rendering with Russian labels, legacy fallback, live expander rename, automated tests for pure logic.
