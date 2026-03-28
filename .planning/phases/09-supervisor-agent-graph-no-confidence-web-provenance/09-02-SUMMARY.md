---
phase: 09-supervisor-agent-graph-no-confidence-web-provenance
plan: 02
requirements-completed: [API-05, WEB-01, SRCH-03]
completed: 2026-03-28
---

# Phase 9 Plan 02 Summary

`/next_message` builds `details` via `assemble_next_message_details`: no confidence in the JSON path; when the graph provides `tavily_queries` and `web_results`, `details.web` uses `WebSearchDetails` / `WebSearchResultItem`. Streamlit drops confidence UI and shows an optional web expander.

## key-files

- modified: `src/api/chat.py`, `src/models/api_contracts.py`, `streamlit_app.py`
- created: `tests/test_next_message_contract_phase9.py`
- modified: `tests/test_tavily_turn.py`, `tests/test_qna_reliability.py`

## Self-Check: PASSED

- `python3 -m pytest tests/test_next_message_contract_phase9.py -q` passes; full `tests/` (non-integration) passes.
