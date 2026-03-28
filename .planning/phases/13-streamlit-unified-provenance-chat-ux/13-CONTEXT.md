# Phase 13: Streamlit Unified Provenance & Chat UX — Context

**Gathered:** 2026-03-28  
**Status:** Ready for planning

<domain>

## Phase boundary

Deliver **Streamlit** changes for **UI-04**, **UI-05**, **UI-06** only:

1. **UI-04** — Chat history **chronological**: oldest at the **top** of the transcript, **newest** (latest user + assistant pair) **immediately above** the composer/input block; turns **appended** in time order (not prepended).
2. **UI-05** — Assistant **answer body** (`message`) always **visible**; **no** confidence UI (**API-05**).
3. **UI-06** — **One** collapsed expander for provenance with **Russian** labels; includes **RAG**, **web** (queries, results, optional fetch), and **synthesis** metadata — **no** redundant stacked «Источники» + raw `web` JSON expander + separate «Синтез» for the **same** content when `details["provenance"]` is available.

**Out of scope:** Phase **14** (README, smokes), API contract changes beyond consuming existing **`details`** shapes, new product features.

**Depends on:** Phase **12** — **`details["provenance"]`** populated on graph success/fail paths when applicable; legacy **`evidence`**, **`structured_answer`**, **`web`** remain for compatibility.

</domain>

<decisions>

## Implementation decisions

### Chat layout & ordering (UI-04)

- **D-01:** Persist `st.session_state.messages` in **strict chronological order** (oldest → newest). On each successful send, **`append`** `{"role": "user", …}` then **`append`** `{"role": "assistant", …}` (do **not** `insert(0, …)`).
- **D-02:** Render the scrollable transcript **top → bottom** = **time order**; the **composer** stays **below** the transcript so the **latest** assistant turn sits **directly above** inputs/divider.

### Assistant message & provenance (UI-05, UI-06)

- **D-03:** Always render the assistant **`message`** as the primary markdown **before** any expanders.
- **D-04:** If `details.get("provenance")` is a **non-empty** `dict` (has at least `rag` or usable `web` / `synthesis`): render **one** expander titled **«Происхождение ответа»** (`expanded=False`). Inside, use **Russian** subsection headings:
  - **«Контекст (RAG)»** — normalized query + compact evidence (from `provenance["rag"]`; mirror key facts, avoid huge dumps; prefer list/table over raw JSON wall).
  - **«Веб-поиск»** — queries, results (titles, URLs, short snippets); if `provenance["web"].get("fetch")`, show **«Загрузка страницы»** (URL, ok/error, short excerpt preview if present).
  - **«Синтез»** — route and optional `gigachat_error_class` from `provenance["synthesis"]` / aligned fields.
- **D-05:** When **D-04** applies, **do not** render the separate **«Источники»** block from `structured_answer.sources_block_ru` (duplicate of RAG sourcing). **Do not** render separate **«Веб-поиск»** + **«Синтез»** expanders that only repeat the same data.
- **D-06:** When **`provenance` is absent** or empty (legacy client/API): **fallback** — keep current behavior: show **«Источники»** from `structured_answer` if present; optional **«Веб-поиск»** via structured display (prefer not to use `st.json` for operator-facing text if a simple list is enough — **planner** may choose `st.json` only as interim for legacy).

### Live & edge cases

- **D-07:** If `details.get("live")` is a `dict`, show a **separate** expander **«Актуальные данные (live)»** (`expanded=False`). **Do not** fold `live` into **«Происхождение ответа»** in Phase 13 (different semantics; roadmap UI-06 targets RAG + web + synthesis).
- **D-08:** On **`failed`** `next_message` / error path: show **message** + **error details** as today; **no** provenance expander required.

### Claude's discretion

- Exact **layout** inside the provenance expander (tables vs `st.dataframe` vs markdown lists).
- Truncation limits for snippets and number of evidence rows shown.
- Minor copy tweaks on Russian labels if UX review suggests clearer operator language.

</decisions>

<canonical_refs>

## Canonical references

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements

- `.planning/ROADMAP.md` — Phase 13 goal & success criteria (UI-04, UI-05, UI-06)
- `.planning/REQUIREMENTS.md` — UI-04, UI-05, UI-06; API-05 (no confidence)
- `.planning/PROJECT.md` — v1.4 milestone, unified provenance UX intent

### Prior phase context & API

- `.planning/phases/12-supervisor-reliability-single-pass-web/12-CONTEXT.md` — WEB-02 / provenance intent
- `src/models/api_contracts.py` — `ProvenanceSnapshot` and related models (shape reference)
- `src/api/chat.py` — `assemble_next_message_details` (what appears in `details`)

### Streamlit & client

- `streamlit_app.py` — current UI to refactor (`_render_assistant_block`, message ordering)
- `src/ui/f1_chat_http.py` — HTTP client helpers (no change expected unless tests require)

### Tests

- `tests/test_streamlit_client.py` — contract tests if any assert on response shape; extend if needed for UI helpers factored out of `streamlit_app.py`

</canonical_refs>

<code_context>

## Existing code insights

### Reusable assets

- `_render_assistant_block` in `streamlit_app.py` — central place to swap **one** provenance expander vs legacy branches.
- Pydantic **`ProvenanceSnapshot`** — optional runtime validation in UI if parsing `details` client-side (planner decides).

### Established patterns

- `st.chat_message` for roles; `st.expander` for collapsible sections; sidebar for API base URL.

### Integration points

- `post_next_message` → `details` dict; must handle both **`provenance`**-rich and **legacy** responses during transition.

</code_context>

<specifics>

## Specific ideas

- User requested **all** discuss-phase topics in one pass (RU: «Давай все обсудим») — decisions above lock **chronological append**, **provenance-first** rendering, **deduplicated** sources, **live** separate.

</specifics>

<deferred>

## Deferred ideas

- Merging **live** into unified provenance — **deferred** (not required by UI-06 wording).
- Replacing **legacy** fallback with a hard requirement on `provenance` only — **deferred** until API version bump / Phase 14 docs.

</deferred>

---

*Phase: 13-streamlit-unified-provenance-chat-ux*  
*Context gathered: 2026-03-28*
