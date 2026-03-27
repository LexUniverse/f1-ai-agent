---
phase: 05-live-enrichment-freshness
plan: "02"
subsystem: api
tags: [fastapi, live-data, ru-copy]

requires:
  - phase: "05-01"
    provides: F1ApiClient, gate, LiveDetails, messages contract
provides:
  - "/next_message live branch after empty RAG + gate"
  - LIVE_UNAVAILABLE degraded payload without structured_answer
  - RU freshness line shared with details.live.as_of
affects: []

tech-stack:
  added: []
  patterns: [app.state injected F1 client; no from_env fallback in routes]

key-files:
  created:
    - src/live/messages_ru.py
    - tests/test_live_enrichment.py
  modified:
    - src/main.py
    - src/api/chat.py
    - src/answer/russian_qna.py
    - tests/conftest.py

key-decisions:
  - "Live success uses fixed QnAConfidence tier средняя / score 0.55 per plan."
  - "Early return on LiveUpstreamError after set_status LIVE_UNAVAILABLE."

patterns-established:
  - "summarize_live_next_payload_ru for unknown JSON falls back to json.dumps prefix."

requirements-completed: ["LIVE-01", "LIVE-02", "LIVE-03"]

duration: 15min
completed: 2026-03-27
---

# Phase 05: Live Enrichment — Plan 05-02

**End-to-end live path:** `/next_message` calls the F1 API only when retrieval is empty and the gate fires, surfaces `details.live` and Russian freshness text on success, and returns a locked degraded message on outage.

## Performance

- **Tasks:** 3
- **Files:** 6 touched

## Accomplishments

- Injected `F1ApiClient.from_env()` on `app.state`; chat route uses `request.app.state.f1_api_client` only.
- Preserved Phase 4 abstention when evidence is empty and the gate is false.
- Added FastAPI integration tests for enrichment, abstention, outage, and no-call when evidence exists.

## Verification

- `python3 -m pytest tests/ -q` — pass (48 tests)

## Self-Check: PASSED
