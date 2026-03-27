---
phase: 05-live-enrichment-freshness
plan: "01"
subsystem: api
tags: [httpx, pydantic, circuit-breaker, f1api]

requires:
  - phase: "04"
    provides: RU Q&A structured answers and RETRIEVAL_NO_EVIDENCE contract
provides:
  - LiveDetails model and UTC-Z validated as_of
  - Deterministic requires_live_data gate (RU/EN allowlists)
  - F1ApiClient with retries, circuit breaker, MockTransport-tested
affects: ["05-02"]

tech-stack:
  added: []
  patterns: [sync httpx client with env-driven config, manual circuit breaker]

key-files:
  created:
    - src/live/gate.py
    - src/live/__init__.py
    - src/integrations/f1api_client.py
    - src/integrations/__init__.py
    - tests/test_live_gate.py
    - tests/test_f1api_client.py
  modified:
    - src/models/api_contracts.py

key-decisions:
  - "Application-level retries limited to ReadTimeout and HTTP 5xx; 404 not retried."
  - "Circuit breaker records one failure per exhausted fetch_current_next attempt."

patterns-established:
  - "LiveUpstreamError carries optional HTTP status_code; circuit_open has no status."

requirements-completed: ["LIVE-02", "LIVE-03"]

duration: 12min
completed: 2026-03-27
---

# Phase 05: Live Enrichment — Plan 05-01

**Foundation for live enrichment:** typed `LiveDetails`, resilient `F1ApiClient` toward f1api.dev, and a pure string-based live-intent gate with locked pytest coverage.

## Performance

- **Tasks:** 2
- **Files:** 7 touched

## Accomplishments

- Added `LiveDetails` with mandatory `as_of` pattern ending in `Z`.
- Implemented `requires_live_data` with RU substrings, EN phrases, and EN keyword regex.
- Delivered httpx sync client with transport retries, bounded GET retries, and manual breaker; full MockTransport unit tests.

## Verification

- `python3 -m pytest tests/test_live_gate.py tests/test_f1api_client.py -x` — pass

## Self-Check: PASSED
