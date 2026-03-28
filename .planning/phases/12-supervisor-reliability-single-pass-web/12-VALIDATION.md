---
phase: 12
status: pending_execution
---

# Phase 12 — Validation checklist (Nyquist / UAT hooks)

After execute-phase, verifier should confirm:

1. **AGT-06:** No numeric gate on supervisor path; repair round exists; optional env log works.
2. **AGT-07:** Only one Tavily invocation per turn after RAG reject; AGT-05 after one post-web supervisor reject.
3. **SRCH-04:** `gigachat_plan_web_use` invoked when Tavily returns rows; fetch runs only when `titles_sufficient` is false.
4. **WEB-02:** `details.provenance` present on ready responses; shape matches `ProvenanceSnapshot` or documented dict.
