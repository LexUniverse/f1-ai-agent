---
phase: 17
slug: timeapi-fastf1-schedule-services
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pytest.ini` (markers) |
| **Quick run command** | `pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds (offline mocks) |

---

## Sampling Rate

- **After every task commit:** Run scoped pytest for the files touched in that plan wave
- **After every plan wave:** Run `pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py -q` once both exist
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01 T1 | 01 | 1 | TIME-01 | grep | `rg "TIMEAPI_UNAVAILABLE_MESSAGE_RU" src/integrations/messages_ru.py && rg "time/current/unix" src/integrations/timeapi_client.py` | ⬜ W1 | ⬜ pending |
| 17-01 T2 | 01 | 1 | TIME-01 | unit | `pytest tests/test_timeapi_client.py -q` | ⬜ W1 | ⬜ pending |
| 17-02 T1 | 02 | 2 | SCHED-01 | grep | `rg "get_event_schedule" src/integrations/f1_schedule_service.py && rg "schedule_data_quality" src/integrations/f1_schedule_service.py` | ⬜ W2 | ⬜ pending |
| 17-02 T2 | 02 | 2 | SCHED-01 | unit | `pytest tests/test_f1_schedule_service.py -q` | ⬜ W2 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_timeapi_client.py` — httpx mock for TimeAPI success/failure/timeout
- [ ] `tests/test_f1_schedule_service.py` — synthetic schedule DataFrame / monkeypatch `get_event_schedule`
- [ ] `pytest.ini` — register `timeapi_live` marker (per 17-01-PLAN.md)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live TimeAPI reachability | TIME-01 | External network | Set `RUN_TIMEAPI_SMOKE=1`, run `@pytest.mark.timeapi_live` test |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
