---
phase: 07-streamlit-ui-local-run
plan: 01
subsystem: ui
tags: [streamlit, httpx, fastapi]

requires: []
provides:
  - Optional start_chat question on session
  - src/ui/f1_chat_http sync HTTP helpers
  - streamlit_app operator UI with polling and structured answer fields
affects: [07-streamlit-ui-local-run]

tech-stack:
  added: [streamlit, httpx]
  patterns: [thin HTTP client module separate from Streamlit]

key-files:
  created:
    - src/ui/__init__.py
    - src/ui/f1_chat_http.py
    - streamlit_app.py
    - tests/test_streamlit_client.py
  modified:
    - src/models/api_contracts.py
    - src/api/chat.py
    - tests/test_api_async_contracts.py
    - requirements.txt

key-decisions:
  - "Strip optional question and set session.next_message only when non-empty after strip."

patterns-established:
  - "Streamlit bootstraps sys.path from repo root for src imports."

requirements-completed: [UI-01, UI-02, UI-03]

duration: 25min
completed: 2026-03-27
---

# Phase 7: Streamlit UI — Plan 01 Summary

**`/start_chat` accepts an operator question, a reusable httpx client wraps the async lifecycle, and Streamlit surfaces message, confidence, citations, live, and synthesis with Russian copy.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 7 paths (4 modified, 3 created)

## Accomplishments

- Extended `StartChatRequest` and `start_chat` so the first user question can be sent at session creation.
- Added `src/ui/f1_chat_http.py` with `start_chat_http`, `get_message_status`, and `post_next_message` (X-Session-Id, 30s timeout).
- Delivered `streamlit_app.py` with 0.75s polling, 60s timeout, history, «Новый чат», and structured-field display per UI-SPEC.

## Task Commits

1. **Task 1:** `9a96f18` — StartChatRequest + wiring + API test
2. **Task 2:** `21169e7` — httpx client module
3. **Task 3:** `72bba14` — Streamlit app, client tests, dependencies

## Files Created/Modified

- `src/models/api_contracts.py` — optional `question` on start chat
- `src/api/chat.py` — sets `next_message` from stripped question
- `src/ui/f1_chat_http.py` — sync API client helpers
- `streamlit_app.py` — operator UI
- `tests/test_api_async_contracts.py` — optional question test
- `tests/test_streamlit_client.py` — MockTransport coverage
- `requirements.txt` — streamlit + httpx pins

## Decisions Made

None beyond the plan — strip-only nonempty question to preserve default `next_message` for empty/whitespace input.

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

None

## Next Phase Readiness

- Plan 07-02 can add `api.py`, README local run, and `.env.example` for `F1_API_BASE_URL`.

---
*Phase: 07-streamlit-ui-local-run*
*Completed: 2026-03-27*

## Self-Check: PASSED
