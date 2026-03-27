---
phase: 05
slug: live-enrichment-freshness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python3 -m pytest tests/test_live_enrichment.py -x` |
| **Full suite command** | `python3 -m pytest` |
| **Estimated runtime** | ~30–90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_live_enrichment.py -x`
- **After every plan wave:** Run `python3 -m pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | LIVE-01 | unit | `python3 -m pytest tests/test_live_gate.py -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | LIVE-03 | unit | `python3 -m pytest tests/test_f1api_client.py -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | LIVE-01 | integration | `python3 -m pytest tests/test_live_enrichment.py::test_live_enriches_when_rag_empty -x` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 1 | LIVE-02 | integration | `python3 -m pytest tests/test_live_enrichment.py::test_live_unavailable_degraded -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_live_gate.py` — deterministic live intent (D-03)
- [ ] `tests/test_f1api_client.py` — timeout, breaker, error mapping (D-12)
- [ ] `tests/test_live_enrichment.py` — `/next_message` with mocked f1api client
- [ ] `tests/conftest.py` — extend if needed for app + mock client fixtures

*Existing infrastructure: `pytest.ini`, prior phase tests under `tests/`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real f1api.dev smoke | LIVE-01 | Optional; flaky network | Set `F1API_LIVE_TEST=1`, run marked integration outside CI |

*Default: all phase behaviors covered by automated tests with mocked HTTP.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
