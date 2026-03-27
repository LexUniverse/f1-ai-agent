# Phase 7: Streamlit UI & Local Run - Discussion Log

> **Audit trail only.** Decisions are captured in `07-CONTEXT.md`.

**Date:** 2026-03-27  
**Phase:** 07-streamlit-ui-local-run  
**Areas discussed:** API base URL & config, Structured field presentation, Polling lifecycle, Chat history & new chat, RUN-01 documentation alignment (implicit via recommendations)

---

## Selection

User instruction: **«все, используй рекомендации»** — all four gray areas from discuss-phase accepted with the recommended options.

---

## 1. API base URL & configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Default localhost + env override | `http://127.0.0.1:8000` default, `F1_API_BASE_URL` (or equivalent) in `.env` | ✓ |
| Sidebar-only manual URL | User types base URL each run | |
| Hardcoded only | No override | |

**User's choice:** Recommended — default localhost + env override (`F1_API_BASE_URL`), aligned with `.env`.

---

## 2. Structured details presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Full UI-03 + compact synthesis | message, confidence, citations, live panel; synthesis in badge/expander | ✓ |
| message only | Minimal | |
| Full JSON dump | Always show raw details | |

**User's choice:** Recommended — full UI-03 plus compact `details.synthesis` visibility.

---

## 3. Polling lifecycle

| Option | Description | Selected |
|--------|-------------|----------|
| 0.5–1 s interval, 30–60 s timeout | Spinner + status text | ✓ |
| Fast poll / no timeout | | |
| Single long poll | Not applicable to current API | |

**User's choice:** Recommended.

---

## 4. Chat history in Streamlit

| Option | Description | Selected |
|--------|-------------|----------|
| Accumulate in session_state | Thread per session; new `/start_chat` or «Новый чат» | ✓ |
| Last answer only | | |

**User's choice:** Recommended.

---

## Claude's Discretion

Routine implementation choices (exact seconds, file paths, Streamlit layout) left to planning/execution per CONTEXT.md.

## Deferred Ideas

None recorded.
