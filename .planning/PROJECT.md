# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines **RAG over historical F1 data** with **web search (Tavily via LangChain)** when needed, orchestrated by a **LangGraph + LangChain** turn: a **supervisor** (GigaChat) **accepts or rejects candidate answers** from a **worker agent** that first answers **from RAG only**, then may run **one bounded web pass** (result ranking, **title-first** reasoning, **optional fetch of a single chosen page**) — no separate numeric “confidence” gate for acceptance. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.6 — Real-time clock & F1 schedule tools

**Goal:** Дать агенту **инструменты** с **текущим временем** через [TimeAPI.io](https://www.timeapi.io/swagger/index.html) (авторитетная метка «сейчас») и **календарём F1** через [FastF1](https://github.com/theOehrly/Fast-F1) (`EventSchedule` / `Event`, поля `Session[1-5]DateUtc`, `EventDate`, `RoundNumber` и т.д.), чтобы на вопросы вроде «какая следующая гонка» ответ строился от **UTC-сейчас** и **расписания сезона**, а не от догадок модели.

**Target features:**

- **TIME:** HTTP-клиент к TimeAPI (например `GET https://www.timeapi.io/api/v1/time/current/utc` или unix); таймауты; явный **degraded** режим при ошибке сети/API.
- **SCHEDULE:** Загрузка расписания сезона FastF1; выбор **следующего гран-при** (исключить тесты: `RoundNumber > 0`) относительно времени с TimeAPI; при необходимости — ближайшая **сессия** (FP1… Race) в UTC для уточнения «когда старт».
- **Agent integration:** Зарегистрированные **LangGraph / LangChain tools** для воркера; ответы пользователю по-прежнему **на русском**; согласование с существующим RAG → supervisor → web циклом (инструменты — отдельный канал фактов о «сейчас» и календаре).

**Key context:** FastF1: для сезонов **≥2018** — точные времена сессий; при `backend='ergast'` и до-2018 — ограничения из документации FastF1 (оценочные слоты сессий). TimeAPI — внешняя зависимость; опционально задокументировать fallback на системное UTC только если согласовано в плане фазы.

## Previous milestone (roadmap not finished)

**v1.5** — Фазы **15–16** в `.planning/ROADMAP.md`: слепой супервизор, до двух fetch, документация и smokes (**AGT-08**, **AGT-09**, **SRCH-05**, **DOC-01**, **DOC-02**, **TST-01**). Требования остаются в `.planning/REQUIREMENTS.md` до закрытия соответствующих фаз.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability); *Phase 4 also shipped explicit confidence — **superseded by v1.3 (confidence removed)**.*
- ✓ Live enrichment after historical retrieval uses a deterministic gate, surfaces `LiveDetails` / `as_of` in responses, and returns a fixed Russian degraded message when f1api.dev is unavailable — validated in Phase 05 (live-enrichment-freshness)
- ✓ GigaChat classic RAG on historical paths with hybrid citations and explicit template fallback + disclosure when the LLM fails — validated in Phase 06 (gigachat-classic-rag); *confidence on that path superseded by v1.3.*
- ✓ Streamlit operator UI (`/start_chat`, status polling, `/next_message`) with citations and synthesis metadata; documented local **API + Streamlit** run — validated in Phase 07 (streamlit-ui-local-run); *UI confidence superseded by v1.3.*
- ✓ **LangGraph** turn with **RAG** + **Tavily (LangChain)** and **GigaChat**; **f1api.dev** removed from answer path — validated in Phase 08 (langgraph-supervisor-tavily-tooling); *linear orchestration superseded by v1.3 supervisor–agent loop.*
- ✓ **Supervisor–Agent 1** LangGraph (RAG-first, ≤2 Tavily rounds, AGT-05 terminal copy), **no `confidence`** in synthesis types or graph outputs, **`details.web`** when search used — validated in Phase 09 (supervisor-agent-graph-no-confidence-web-provenance).
- ✓ **Supervisor JSON repair + optional decision logging; one Tavily per turn; web URL plan + optional single-page fetch; `details.provenance`** (RAG + web + synthesis, legacy `web` preserved) — validated in Phase 12 (supervisor-reliability-single-pass-web): **AGT-06, AGT-07, SRCH-04, WEB-02**.
- ✓ **Streamlit chronological chat, answer before provenance UI, single Russian «Происхождение ответа» expander** (RAG + web + synthesis; legacy fallback; separate live panel) — validated in Phase 13 (streamlit-unified-provenance-chat-ux): **UI-04, UI-05, UI-06**.

### Active (v1.6 + residual v1.5)

- **v1.6:** **TIME-01, SCHED-01, TOOL-01** — TimeAPI «сейчас», FastF1 следующий ГП/сессии, инструменты в графе — see `.planning/REQUIREMENTS.md`.
- **v1.5 (until phases 15–16 close):** **AGT-08, AGT-09, SRCH-05, DOC-01, DOC-02, TST-01** — same file, v1.5 section.

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.
- **Confidence as a product field** — removed in v1.3; not deferred for recalibration.

## Context

Backend is FastAPI with async endpoints and Pydantic models. Frontend is Streamlit. Historical data: f1db in ChromaDB (whitelist tables). Web: **Tavily** (one query per turn after RAG path fails supervisor) plus **up to 2** sequential **bounded** HTTP fetches of URLs **chosen by GigaChat** from the result list when titles/snippets are insufficient (**AGT-09**). **GigaChat** drives worker steps (title sufficiency, URL pick). **Supervisor** judges accept/reject **without** being told whether the candidate came from RAG, web body, or titles only (**AGT-08**). No product confidence field.

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests (supervisor loops may tighten budgets per plan).
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment:** Local run — API + Streamlit; Docker not a milestone goal unless scoped later.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, web-second response policy (v1.2) | Stabilize quality | v1.3 keeps RAG-first **via Agent 1**; web only after **supervisor** rejection. |
| Explicit degraded-mode when web search fails | Prevent silent failures | Preserve; align copy with new terminal failure path where relevant. |
| v1.3: Supervisor judges answers | Linear sufficiency gate insufficient for answer quality | Supervisor accepts/rejects **full candidate answers** vs user question. |
| v1.3: Max two search iterations | Cost/latency + avoid infinite loops | Delivered in Phase 9; **v1.4 replaces** with **one** Tavily + optional single-page fetch. |
| v1.3: Remove confidence entirely | Misleading constant / no calibration | Drop from schemas, details, Streamlit, tests. |
| v1.4: Single web pass + fetch | Richer answers without double Tavily | Rank URLs → titles → optional one fetch → synthesize once. |
| v1.4: Supervisor false-negative audit | Operators hit AGT-05 too often | Trace rejects; fix parse fallback / prompts; confirm no numeric accept gate. |
| v1.4: Unified Streamlit provenance | Duplicate source blocks confuse operators | One expander: RAG + web + synthesis labels. |
| v1.5: RAG whitelist + chunk/query strategy | Много CSV шумят; RU vs EN данные | Явный whitelist; EN чанки + нормализация запроса / алиасы / гибрид (план). |
| v1.5: Two-fetch web pass | Один нерелевантный URL → AGT-05 | GigaChat: 2 кандидата по заголовкам; макс. **2** fetch подряд. |
| v1.5: Blind supervisor | Источник влияет на ложные reject | Судить только Q↔answer; title/snippet-кандидат = такой же приём. |
| v1.5: Supervisor output shape | Вопрос на вопрос | Только прямой ответ или abstention. |
| v1.5: README_DETAILED | Onboarding README too shallow for graph/RAG | **DOC-02** full file/module map. |
| v1.6: Authoritative «now» | Модель не знает текущую дату для «следующей гонки» | **TIME-01** — TimeAPI.io как источник UTC/unix. |
| v1.6: Calendar facts | Расписание из FastF1 EventSchedule vs произвольный веб | **SCHED-01** + **TOOL-01** в воркере. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 — **v1.6** started (TimeAPI + FastF1 schedule tools); **v1.5** phases **15–16** still on roadmap until closed.*
