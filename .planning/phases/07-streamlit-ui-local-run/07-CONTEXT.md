# Phase 7: Streamlit UI & Local Run - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Operators run **FastAPI + Streamlit locally**, use the existing async contract end-to-end: **access code + question** → **`/start_chat`** (store `session_id`) → **poll `/message_status`** until terminal state → **`/next_message`**, and the UI surfaces **`message`**, **confidence**, **citations** (sources), and **`details.live`** when present (**UI-01..UI-03**). **RUN-01** documents local launch (**API + Streamlit**, no Docker) — including a documented API entry (e.g. `python api.py` or equivalent) consistent with the milestone.

Out of scope: new backend capabilities, Docker, multi-user product auth beyond the existing allowlist code flow, LangGraph orchestration UI.

</domain>

<decisions>
## Implementation Decisions

### API client configuration
- **D-01:** Streamlit calls the FastAPI base URL **`http://127.0.0.1:8000` by default**. Override via **environment variable** (recommended name **`F1_API_BASE_URL`**, documented in `.env.example`) so local dev matches the existing **`.env`** pattern used for GigaChat and other secrets.
- **D-02:** Use **plain `httpx` or `requests`** from Streamlit for sync HTTP to `/start_chat`, `/message_status`, `/next_message` — no requirement to share FastAPI test client; keep the UI as a thin HTTP client.

### Presentation of structured fields (UI-03 + Phase 6 transparency)
- **D-03:** Always show **`message`** as the primary assistant line; show **`confidence`** (`tier_ru` and/or `score`) in a dedicated compact block.
- **D-04:** Show **citations** from **`details.structured_answer.sources_block_ru`** (or equivalent formatted list); if missing on failure paths, omit gracefully and show API **`message`** only.
- **D-05:** When **`details.live`** exists, show **`as_of`**, **`provider`**, and related fields in a small **“Live”** panel (expandable or always visible — planner/implementation discretion).
- **D-06:** Show **`details.synthesis`** in a **compact** way (e.g. badge or `st.expander`): **`route`** (`gigachat_rag` vs `template_fallback`) and **`gigachat_error_class`** when present so operators see LLM vs template path without raw JSON dump by default.

### Polling lifecycle (UI-02)
- **D-07:** Poll **`/message_status`** every **0.5–1.0 s** until status is **`ready` or `failed`** (or a single terminal policy per Phase 2 contract).
- **D-08:** **Client-side timeout** approximately **30–60 s** with a clear Russian message if exceeded; display current **`message_status`** text alongside a spinner while waiting.
- **D-09:** After terminal status, call **`/next_message`** once per the existing async lifecycle (same as tests/conftest expectations).

### Session and chat history in Streamlit
- **D-10:** **Accumulate** user questions and assistant replies in **`st.session_state`** for the current browser session so the operator can scroll the thread.
- **D-11:** **New chat**: starting a new flow runs **`/start_chat`** again and stores a **new `session_id`**; provide an explicit control (e.g. **«Новый чат»**) that clears local history and requires a new start; planner decides exact UX.

### Local run documentation (RUN-01)
- **D-12:** Document **two processes**: (1) API — **`python api.py`** *or* **`uvicorn src.main:app --reload --host 127.0.0.1 --port 8000`** (whichever the repo implements); (2) Streamlit — **`streamlit run …`** with module path under repo root. **Docker not required** for v1.1.
- **D-13:** If **`api.py`** does not exist at plan time, **add a thin root `api.py`** (or update docs only) so RUN-01 matches PROJECT/ROADMAP wording; Claude’s discretion on minimal shim vs README-only.

### Claude's Discretion
- Exact Streamlit layout (sidebar vs main), default polling interval within 0.5–1.0 s, timeout exact value in band 30–60 s, styling/theming.
- Whether to show **raw JSON** of `details` in a secondary expander for power users.
- **`streamlit` version pin** in `requirements.txt` alongside existing deps.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, UI-01..03, RUN-01
- `.planning/REQUIREMENTS.md` — **UI-01**, **UI-02**, **UI-03**, **RUN-01**
- `.planning/PROJECT.md` — v1.1 local run, Streamlit visibility into structured fields

### API & answer shape
- `.planning/phases/02-async-backend-contracts/02-CONTEXT.md` — session lifecycle, error envelope, polling semantics
- `.planning/phases/04-ru-q-a-answer-reliability/04-CONTEXT.md` — `message` vs `structured_answer`, confidence, abstention
- `.planning/phases/06-gigachat-classic-rag/06-CONTEXT.md` — `details.synthesis`, template fallback disclosure, `details.live` preservation

### Code (integration targets)
- `src/main.py` — FastAPI app and router mount
- `src/api/chat.py` — `/start_chat`, `/message_status`, `/next_message`
- `src/models/api_contracts.py` — response models / `NextMessageResponse` shape
- `.env.example` — pattern for `F1_API_BASE_URL` and local secrets

### Research (optional depth)
- `.planning/research/STACK.md` — Streamlit version notes
- `.planning/research/ARCHITECTURE.md` — UI layer expectations

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **FastAPI app** in `src/main.py` with `chat_router` — Streamlit only needs HTTP client against running server.
- **Typed contracts** in `src/models/api_contracts.py` — mirror field names in UI (`message`, `details`, etc.).
- **Tests** (`tests/conftest.py`, `tests/test_qna_reliability.py`, etc.) demonstrate header **`X-Session-Id`** and JSON bodies for the three endpoints.

### Established Patterns
- **Auth**: `access_code` in `/start_chat` body; allowlist via **`AUTH_ALLOWLIST_CODES`** (tests set this; Streamlit operator must use a valid code).
- **Errors**: HTTP 4xx/5xx return **error envelope** — UI should surface `error.message` / `error.code` in Russian-friendly way.

### Integration Points
- New entry suggested: **`streamlit_app.py`** or **`ui/app.py`** at repo root or under `src/` — planner chooses; **`requirements.txt`** gains **`streamlit`** pin.
- Optional **root `api.py`** uvicorn entry for RUN-01 alignment.

</code_context>

<specifics>
## Specific Ideas

User accepted **all recommended defaults** in discuss-phase (2026-03-27): env-configurable API base URL with localhost default, full structured visibility including compact synthesis route, 0.5–1 s polling with 30–60 s timeout, session-scoped chat history with explicit new chat.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-streamlit-ui-local-run*
*Context gathered: 2026-03-27*
