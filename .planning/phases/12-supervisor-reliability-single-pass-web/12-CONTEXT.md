# Phase 12: Supervisor Reliability & Single-Pass Web — Context

**Gathered:** 2026-03-28  
**Status:** Ready for planning (post-discuss; user may refine numbered open points below)

<domain>

## Phase boundary

This phase delivers **only**:

1. **AGT-06** — Supervisor **false-negative** audit: acceptance is **LLM-only**; find/remove any **numeric gates** on the accept path; clarify behavior on **JSON/network** failures (today `gigachat_supervisor_accept_answer` returns **`False` on any exception**, which can force AGT-05 without a real “reject”).
2. **AGT-07** — **At most one `run_tavily_search_once` per turn** after the RAG-only candidate is rejected. **No second Tavily loop.** “Second chance” is **in-graph**: rank results → answer from **titles/snippets** if enough → else **HTTP GET one chosen URL** (bounded) → one revised candidate → supervisor again → if still rejected, **AGT-05** (`UNABLE_TO_ANSWER_SUPERVISOR_RU`).
3. **SRCH-04** — Worker **selects** best URL(s); **title/snippet-first** answer path before fetch.
4. **WEB-02** — **`details`** (or equivalent) expose a **single structured provenance surface** for later UI (Phase 13): RAG evidence + web query/results + optional **fetch** metadata (chosen URL, success/failure), without duplicating the same URLs in unrelated keys.

**Out of scope here:** Streamlit layout (**Phase 13**), README/smokes (**Phase 14**).

**Supersedes (within this repo):** Phase 9 **D-02** (“cap at 2 Tavily”) — replaced by **one Tavily + optional single-page read** per turn.

</domain>

<decisions>

## Implementation decisions

### Supervisor reliability (AGT-06)

- **D-01:** **No numeric confidence threshold** on supervisor accept/reject. The only gate is **`gigachat_supervisor_accept_answer`** → parsed `accept` boolean. **Audit** `src/graph/f1_turn_graph.py`, `src/answer/gigachat_rag.py`, `src/api/chat.py` for any other logic that skips acceptance (document `tier_ru_from_max_score` / `0.55` — they affect **fallback user-facing template strings**, not supervisor).
- **D-02 (recommended — confirm):** On **first** supervisor JSON parse failure, **one repair attempt** (second GigaChat message: “return only `{\"accept\": true|false}`”) before treating as reject. If still invalid → log (level + truncated payload) → **`False`** (conservative). *Alternative deferred:* always `False` on parse error (current behavior) — simpler but causes false AGT-05.
- **D-03:** Add **debug-friendly** optional logging of supervisor **accept** outcome (no full user PII in production logs by default; env flag e.g. `F1_LOG_SUPERVISOR_DECISIONS=1`).

### Single-pass web (AGT-07, SRCH-04)

- **D-04:** **`web_search_rounds` semantics:** increment **once per successful Tavily invocation** (keep compatibility with `details.web`); **never** exceed **1** Tavily call per turn after RAG rejection. Remove / bypass the **second** Tavily branch in the graph.
- **D-05:** After Tavily, new substeps (nodes or sequential helpers): **(a)** LLM or structured step to **pick** `best_url` and whether **titles/snippets suffice**; **(b)** if not, **GET** `best_url` with `httpx` (existing stack), timeout **≤15s**, max body **~500KB**, **User-Agent** identifying the app; **plain text / simple HTML strip** (stdlib `html.parser` or minimal deps — **planner chooses**); **no** headless browser in v1.4 unless research proves necessary.
- **D-06:** **One** `gigachat_synthesize_from_web_results`-style call **after** enriched context (Tavily snippets **and/or** fetched page excerpt) before returning to supervisor; supervisor sees **one** web-backed candidate per Tavily round.
- **D-07:** If Tavily fails (**WEB_SEARCH_UNAVAILABLE**), behavior unchanged: fail the turn as today (no fetch).

### API / WEB-02

- **D-08 (recommended):** Introduce a **single** top-level or nested key in graph `out_details` / chat `details`, e.g. **`provenance`** or extend documented shape: `{ "rag": { evidence summary… }, "web": { queries, results[], fetch?: { url, ok, excerpt? } }, "synthesis": { route, … } }`. **Backward compatibility:** keep `structured_answer` + `evidence` as needed for tests; **migrate** Streamlit in Phase 13 to read the unified blob.
- **D-09:** **`details.web`** (WEB-01) remains valid for “web search contributed”; may **alias** or **embed** inside **WEB-02** shape — planner to avoid two competing lists of the same URLs.

### Claude's discretion

- Exact **node split** in LangGraph (separate nodes vs one `agent1_web` function with steps).
- HTML-to-text library choice if stdlib insufficient.
- Prompt wording for **URL selection** and **title-sufficiency** JSON schema.

</decisions>

<specifics>

## Specific ideas (from product / v1.4 charter)

- Operator symptom: **constant AGT-05** — hypothesis: **supervisor always `False`** (API errors, strict prompt, parse failures) rather than hidden **0.55** gate.
- Desired web flow: query → relevant links → **pick best** → **titles** enough? answer → else **open one site** and extract → **single** iteration (no second Tavily).

</specifics>

<canonical_refs>

## Canonical references

- `.planning/ROADMAP.md` — Phase 12 goal & success criteria
- `.planning/REQUIREMENTS.md` — AGT-06, AGT-07, SRCH-04, WEB-02
- `.planning/PROJECT.md` — v1.4 milestone notes
- `.planning/phases/09-supervisor-agent-graph-no-confidence-web-provenance/09-CONTEXT.md` — prior supervisor/Tavily decisions (**D-02 superseded**)
- `src/graph/f1_turn_graph.py` — graph to refactor
- `src/answer/gigachat_rag.py` — `gigachat_supervisor_accept_answer`, synthesis prompts
- `src/graph/tavily_tool.py` — Tavily single shot
- `src/api/chat.py` — `assemble_next_message_details`

</canonical_refs>

<code_context>

## Existing code insights

### Reusable assets

- **`run_tavily_search_once`** — keep as the **only** Tavily entry; cap call count in graph.
- **`gigachat_supervisor_accept_answer`** — extend/retry policy here or thin wrapper in graph.
- **`assemble_next_message_details`** — extend for **WEB-02** unified provenance.

### Integration points

- **`F1TurnState`** — new fields likely: `fetch_url`, `fetch_excerpt`, `web_phase: literal` / flags for planner clarity.

### Pitfalls (from code read)

- ```252:253:src/answer/gigachat_rag.py
    except Exception:
        return False
```
  Any GigaChat/JSON error → **reject** → pushes toward **AGT-05** after web loop; high impact for “always failing” reports.

</code_context>

<open_points>

## Open points — reply with choices (optional)

1. **Supervisor parse errors:** **A)** one repair attempt then `False` *(recommended in D-02)* **B)** keep always `False` on error *(current)*.
2. **Page fetch:** **A)** httpx + stdlib HTML strip only **B)** add lightweight dep (e.g. `readability-lxml` / `trafilatura`) if planner bench shows garbage text.
3. **`details` shape:** **A)** new `provenance` object + keep flat fields for one release **B)** breaking cleanup in one phase *(only if you accept test churn)*.

If you send nothing, planning will follow **A / recommended** above.

</open_points>

---

*Phase: 12-supervisor-reliability-single-pass-web*
