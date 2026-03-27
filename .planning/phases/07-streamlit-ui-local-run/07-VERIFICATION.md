---
status: passed
phase: 07-streamlit-ui-local-run
completed: 2026-03-27
---

# Phase 7 Verification — Streamlit UI & Local Run

## Goal (from ROADMAP)

Operators run **API + Streamlit locally** and use the async chat contract end-to-end with full visibility into structured fields.

## Requirements traceability

| ID     | Verified |
|--------|----------|
| UI-01  | Yes — `StartChatRequest.question`; `start_chat` sets `session.next_message` when strip non-empty; tests in `test_api_async_contracts.py` |
| UI-02  | Yes — `streamlit_app.py` uses `start_chat_http`, polls `get_message_status`, then `post_next_message` with `X-Session-Id`; `tests/test_streamlit_client.py` mocks sequence |
| UI-03  | Yes — `streamlit_app.py` renders `message`, `details.confidence`, `structured_answer.sources_block_ru`, expanders for `details.live` and `details.synthesis` |
| RUN-01 | Yes — root `api.py` with `uvicorn.run("src.main:app", ...)`; README `## Local run (v1.1)` with `python api.py`, `uvicorn src.main:app`, `streamlit run streamlit_app.py`; Docker not required; `.env.example` has `F1_API_BASE_URL` comment |

## Must-haves (spot-check)

- Artifacts exist: `src/ui/f1_chat_http.py`, `streamlit_app.py`, `api.py`, `README.md`, `.env.example` (updated).
- `streamlit_app.py` imports `f1_chat_http`; `F1_API_BASE_URL` and `Отправить вопрос` present.

## Automated checks

```bash
python3 -m pytest tests/ -q
```

Result: **57 passed** (2026-03-27).

## human_verification

None required — Streamlit manual smoke optional; contract covered by tests + code inspection.

## Gaps

None.
