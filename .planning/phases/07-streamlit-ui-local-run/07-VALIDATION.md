---
phase: 07
slug: streamlit-ui-local-run
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (repo `pytest.ini`) |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest tests/test_streamlit_client.py tests/test_api_async_contracts.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30–90 seconds |

---

## Sampling Rate

- **After every task commit:** Quick run (targeted files for touched areas)
- **After every plan wave:** `pytest`
- **Before `/gsd-verify-work`:** Full suite green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | UI-01 | API | `pytest tests/test_api_async_contracts.py -k question -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | UI-01–03 | unit | `pytest tests/test_streamlit_client.py -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | UI-01–03 | manual | Streamlit smoke | — | ⬜ pending |
| 07-02-01 | 02 | 2 | RUN-01 | grep/doc | `rg "api\\.py|streamlit run" README.md` | — | ⬜ pending |
| 07-02-02 | 02 | 2 | RUN-01 | smoke | `python -c "import api"` optional | — | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/test_streamlit_client.py` — httpx MockTransport, no network
- [ ] `tests/test_api_async_contracts.py` — case for `start_chat` + `question` → session `next_message`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Streamlit E2E polish | UI-03 | Browser | Start API + `streamlit run streamlit_app.py`; submit code + question; verify panels |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or documented manual steps
- [ ] No watch-mode flags
- [ ] `nyquist_compliant: true` set after execution wave

**Approval:** pending
