---
status: passed
phase: 12-supervisor-reliability-single-pass-web
updated: 2026-03-28
---

# Phase 12 Verification

## Must-haves

| Criterion | Evidence |
|-----------|----------|
| AGT-06 supervisor repair + audit note | `gigachat_supervisor_accept_answer` repair path; module comment on scores; `test_gigachat_supervisor_repair_round_accepts_after_bad_json` |
| AGT-07 one Tavily; finalize_fail after one web pass | `web_search_rounds` increment only in `tavily_search`; `_route_after_supervisor` uses `>= 1`; `test_one_tavily_then_agt05` |
| SRCH-04 plan URL + optional fetch | `gigachat_plan_web_use`, `web_plan` / `fetch_page` nodes, `fetch_url_text_plain`, `test_page_fetch.py` |
| WEB-02 provenance in graph + API | `_build_provenance_snapshot`, `details["provenance"]` in `assemble_next_message_details`, `ProvenanceSnapshot`, `test_phase12_provenance.py` |
| Phase 9 fields preserved | `test_next_message_contract_phase9.py` unchanged behavior; legacy `web`, `evidence`, `structured_answer` |

## Automated

- `python3 -m pytest tests/ -q --ignore-glob='*integration*'` — 63 passed (2026-03-28).

## human_verification

_Optional: call `/next_message` with web path and inspect `details.provenance` in JSON._
