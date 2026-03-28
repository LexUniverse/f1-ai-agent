# Phase 13: Streamlit Unified Provenance & Chat UX — Discussion Log

> **Audit trail only.** Decisions are captured in `13-CONTEXT.md`.

**Date:** 2026-03-28  
**Phase:** 13-streamlit-unified-provenance-chat-ux  
**Areas discussed:** Chat order (UI-04), Unified provenance (UI-06), Duplicate sources, Live & failures  

**User prompt:** «Давай все обсудим» — discuss **all** proposed gray areas in one pass.

---

## 1. Chat order (UI-04)

| Option | Description | Selected |
|--------|-------------|----------|
| A | Chronological list (`append`), oldest top — newest just above composer (matches REQUIREMENTS) | ✓ |
| B | Keep current `insert(0, …)` newest-first in scroll | |

**User's choice:** Full discussion scope accepted; **Option A** locked per roadmap/UI-04.  
**Notes:** Aligns `streamlit_app.py` with «oldest top, newest above composer».

---

## 2. Single provenance expander (UI-06)

| Option | Description | Selected |
|--------|-------------|----------|
| A | Read `details["provenance"]` first; Russian title «Происхождение ответа»; subsections RAG / web / synthesis (+ fetch when present) | ✓ |
| B | Keep multiple expanders only | |

**User's choice:** **Option A** with subsection labels: «Контекст (RAG)», «Веб-поиск», «Загрузка страницы» (if fetch), «Синтез».  
**Notes:** Fallback to legacy layout if `provenance` missing.

---

## 3. Duplicate «Источники»

| Option | Description | Selected |
|--------|-------------|----------|
| A | Hide `sources_block_ru` block when unified provenance is shown | ✓ |
| B | Always show inline sources for scanability | |

**User's choice:** **Option A** — avoids duplicate RAG sourcing vs UI-06.

---

## 4. Live & failures

| Option | Description | Selected |
|--------|-------------|----------|
| A | Separate expander «Актуальные данные (live)» when `details.live` present | ✓ |
| B | Merge live into «Происхождение ответа» | |

**User's choice:** **Option A** for Phase 13 scope. Failed turns: no provenance expander.

---

## Claude's discretion

- Provenance interior widgets (tables vs markdown), truncation limits — see CONTEXT § Claude's Discretion.

## Deferred ideas

- Unified expander including live — deferred to future milestone if product wants one operator surface.
