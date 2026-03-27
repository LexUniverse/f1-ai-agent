# Phase 7: Streamlit UI & Local Run — Research

**Researched:** 2026-03-27  
**Domain:** Streamlit operator UI, httpx sync client against FastAPI, local run docs  
**Confidence:** HIGH for Streamlit + httpx patterns; HIGH for API header `X-Session-Id` contract from existing tests

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (07-CONTEXT.md)

- **D-01:** Default API base `http://127.0.0.1:8000`; override via **`F1_API_BASE_URL`** in `.env` / `.env.example`.
- **D-02:** **`httpx` or `requests`** — prefer **httpx** (already in codebase / tests).
- **D-03..D-06:** Present `message`, `confidence`, citations from `details.structured_answer.sources_block_ru`, **`details.live`** panel when present, compact **`details.synthesis`** (route + `gigachat_error_class`).
- **D-07..D-09:** Poll `/message_status` every **0.5–1.0 s**; client timeout **30–60 s**; then single **`/next_message`**.
- **D-10..D-11:** Chat history in **`st.session_state`**; **«Новый чат»** clears and new `/start_chat` on next submit.
- **D-12..D-13:** RUN-01: document API launch + Streamlit; add root **`api.py`** if missing.

### Claude's Discretion

- Exact Streamlit layout, seconds within bands, optional raw JSON expander, Streamlit pin.

### Deferred

- None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Planner note |
|----|----------------|
| **UI-01** | Requires HTTP `POST /start_chat` with `access_code` + **user question** stored for session. Current `StartChatRequest` lacks `question`; **minimal addition**: optional `question: str | None` on request; `start_chat` sets `session.next_message` when provided (tests unchanged when omitted). |
| **UI-02** | Poll `GET /message_status` with header **`X-Session-Id: {uuid}`** (same as `tests/conftest.py` patterns). |
| **UI-03** | Parse `NextMessageResponse`: `message`, `details.confidence`, `details.structured_answer`, `details.live`, `details.synthesis`. |
| **RUN-01** | README section: `python api.py` or `uvicorn src.main:app --reload --host 127.0.0.1 --port 8000`; `streamlit run streamlit_app.py` (path finalized in plan). |
</phase_requirements>

## Project Constraints (from `.cursor/rules/`)

No additional rule files found at research time beyond project defaults.

## Summary

Implement a **thin Streamlit front-end** that uses **`httpx.Client`** against the existing FastAPI app. **Do not** embed FastAPI `TestClient` in the Streamlit app. Session-scoped state holds **`session_id`**, chat turns, and optional UI flags.

**Critical integration gap (UI-01):** Production Streamlit must send the operator’s question; today `Session.next_message` is only set in tests via direct mutation. **Recommended fix:** add optional **`question`** to `StartChatRequest` and assign to the new session in `start_chat` when present. This is a **contract completion**, not a new product feature — aligns REQUIREMENTS UI-01 with Phase 7 CONTEXT (interpret “no new backend capabilities” as no RAG/live/GigaChat changes).

## Standard Stack

| Library | Version | Purpose |
|---------|---------|---------|
| **streamlit** | ≥1.33 (pin in `requirements.txt`) | Operator UI |
| **httpx** | Align with project (add pin if missing from `requirements.txt`) | Sync HTTP |
| **python-dotenv** | existing | Optional: Streamlit can `load_dotenv` or rely on shell env |

## Architecture Patterns

- **Module split:** `src/ui/f1_api_client.py` (or `src/streamlit_client.py`) — pure functions / small class: `start_chat`, `get_message_status`, `fetch_next_message` taking `base_url` and `httpx.Client` or constructing client per call.
- **App entry:** root **`streamlit_app.py`** — imports client, reads `os.environ.get("F1_API_BASE_URL", "http://127.0.0.1:8000")`.
- **`api.py`:** thin shim `uvicorn.run("src.main:app", host="127.0.0.1", port=8000)` for RUN-01 parity with ROADMAP wording.

## Common Pitfalls

- Missing **`X-Session-Id`** header → 401/404 per Phase 2 contract.
- Parsing `details`; keys may be partial on `failed` — **guard** with `.get()`.
- Blocking Streamlit: keep HTTP timeouts bounded (e.g. 30 s per request) in addition to **overall** poll timeout.

## Code Examples (patterns)

Headers for authenticated routes:

```python
headers = {"X-Session-Id": session_id}
client.get(f"{base}/message_status", headers=headers)
client.post(f"{base}/next_message", headers=headers, json={})
```

## Validation Architecture

> `workflow.nyquist_validation` is **true** — section required.

### Test framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing `pytest.ini`) |
| Quick run | `pytest tests/test_streamlit_client.py -x` (after Wave 0) |
| Full suite | `pytest` |

### Phase requirements → test map

| Req ID | Behavior | Test type | Command |
|--------|----------|-----------|---------|
| **UI-01** | `start_chat` with `question` sets session text (API unit via TestClient) | API | `pytest tests/test_api_async_contracts.py` + new case |
| **UI-02** | Client helpers call correct paths/methods | unit | `httpx.MockTransport` in `tests/test_streamlit_client.py` |
| **UI-03** | (Manual or Streamlit E2E optional) | manual | Run API + Streamlit, smoke question |
| **RUN-01** | Docs mention `api.py` + streamlit | grep | `rg "streamlit run" README.md` |

### Sampling

- After API contract change: `pytest tests/test_api_async_contracts.py -x`
- After client module: `pytest tests/test_streamlit_client.py -x`
- Wave merge: `pytest`

### Wave 0 gaps

- [ ] `tests/test_streamlit_client.py` — MockTransport for `start_chat`, `message_status`, `next_message`
- [ ] Extend `tests/test_api_async_contracts.py` — `start_chat` + `question` sets `next_message` on session (read from store)

## Sources

- `07-CONTEXT.md`, `07-UI-SPEC.md`, `src/api/chat.py`, `src/models/api_contracts.py`, `tests/conftest.py`
- [Streamlit docs — session state](https://docs.streamlit.io/develop/concepts/architecture/session-state)
- [httpx — MockTransport](https://www.python-httpx.org/advanced/transports/)

## RESEARCH COMPLETE
