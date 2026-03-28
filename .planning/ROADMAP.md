# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

**v1.0–v1.2:** API, RAG, GigaChat, linear LangGraph + Tavily. **v1.3 Phase 9:** Supervisor + Agent 1, **no confidence**, **`details.web`**.

**v1.4 (phases 12–13):** **Supervisor false-negative audit** (AGT-06), **one Tavily + optional single-page fetch** (AGT-07, SRCH-04), **unified API provenance** (WEB-02), **Streamlit** single expander + chronological chat (UI-04/05/06). *(Originally Phase 14 was README/smokes — moved to **v1.5 Phase 16** together with **README_DETAILED**.)*

**v1.5 (phases 14–16):** **F1DB-aligned RAG** (whitelist CSVs, better chunk text, RU query strategy без обязательного билингва в чанках), **supervisor + web loop** (супервизор «слепой» к каналу данных; **до 2** последовательных fetch’ей после выбора **двух** URL через GigaChat, если title/snippet не хватает), **operator docs** (README + **README_DETAILED.md** + smokes).

**v1.6 (phases 17–18):** **Authoritative «now»** via [TimeAPI.io](https://www.timeapi.io/swagger/index.html) (**TIME-01**: timeout, degraded RU behavior); **next grand prix & session UTC** from FastF1 `EventSchedule` vs that timestamp (**SCHED-01**: `RoundNumber > 0`, testing excluded, year-rollover / ergast caveats); **LangGraph/LangChain tools** on the worker path (**TOOL-01**: RU UX, error propagation, no graph break).

> **Note:** Original **v1.3 phases 10–11** merged into v1.4 as phases **13** (UI) with **UI-06**.

## Phases

- [x] **Phase 1: Access Control** - *(Completed: 2026-03-27)*
- [x] **Phase 2: Async Backend Contracts** - *(Completed: 2026-03-27)*
- [x] **Phase 3: Historical RAG Grounding** - *(Completed: 2026-03-27)*
- [x] **Phase 4: RU Q&A Answer Reliability** - *(Completed: 2026-03-27)*
- [x] **Phase 5: Live Enrichment & Freshness** - *(Completed: 2026-03-27)*
- [x] **Phase 6: GigaChat Classic RAG** - *(Completed: 2026-03-27)*
- [x] **Phase 7: Streamlit UI & Local Run** - *(Completed: 2026-03-27)*
- [x] **Phase 8: LangGraph Supervisor & Tavily Tooling** - *(Completed: 2026-03-28)*
- [x] **Phase 9: Supervisor–Agent Graph, No Confidence, Web Provenance** - *(Completed: 2026-03-28)*
- [x] **Phase 12: Supervisor Reliability & Single-Pass Web** - **AGT-06, AGT-07, SRCH-04, WEB-02**: audit accept path; one Tavily per turn; URL ranking; title-first answer; optional one HTTP fetch; terminal AGT-05 after single pass; API shape for unified provenance. (completed 2026-03-28)
- [x] **Phase 13: Streamlit Unified Provenance & Chat UX** - **UI-04, UI-05, UI-06**: chronological append; message first; **one** collapsed provenance (RAG + web + synthesis); no duplicate sources blocks. (completed 2026-03-28)
- [x] **Phase 14: F1DB RAG Corpus & Cross-Lingual Retrieval** - **RAG-08, RAG-09**: wave **14-01** (whitelist row chunks + aliases + dual query) **completed 2026-03-28**; wave **14-02** (replan): **русские сезонные сводки** из 8 CSV, чанки overview + per-GP; **ai-forever/ru-en-RoSBERTa** для индекса и запроса; **без alias_resolver** и без фильтра по `canonical_entity_id`. (14-02 completed 2026-03-28)
- [ ] **Phase 15: Supervisor & Two-Step Web Fetch** - **AGT-08, AGT-09, SRCH-05**: supervisor judges **only** Q↔answer fit (**blind** to RAG/web/title); user-facing direct answer or abstention; one Tavily → GigaChat: titles/snippets enough? else pick **two** URLs by titles → **max 2** sequential fetches; title/snippet-only answers allowed.
- [ ] **Phase 16: README, README_DETAILED & Smokes** - **DOC-01, DOC-02, TST-01**: onboarding README; **README_DETAILED.md** (per-file / module narrative); opt-in pytest smokes.
- [ ] **Phase 17: TimeAPI & FastF1 schedule services** - **TIME-01, SCHED-01**: current UTC/unix client with timeout + degraded RU; `EventSchedule` next GP vs «now», session UTC fields, year rollover & ergast caveats documented.
- [ ] **Phase 18: Worker time & schedule tools** - **TOOL-01**: LangGraph/LangChain tools wired to worker; Russian-facing behavior; tool errors do not break the turn graph.

## Phase Details (v1.4 — closed)

### Phase 12: Supervisor Reliability & Single-Pass Web
**Goal:** Stop spurious AGT-05; **GigaChat-only** acceptance judgment; **one** search iteration with **smarter** use of results.  
**Depends on:** Phase 9 codebase.  
**Requirements:** AGT-06, AGT-07, SRCH-04, WEB-02  
**Success criteria:**
1. Documented audit: **no** numeric accept gate on supervisor path; parse-fail / API-fail behavior explicit.
2. Graph invokes **Tavily at most once** per turn after RAG rejection; **no** second Tavily loop.
3. Worker **ranks** results, can answer from **titles/snippets**, else **fetches one** URL (bounded) before resubmitting to supervisor.
4. **`details`** (or documented extension) supports **one** UI-facing provenance payload (RAG + web + optional fetch meta).

**Plans:** 2/2 plans complete

### Phase 13: Streamlit Unified Provenance & Chat UX
**Goal:** Operator sees **one** clear expandable «происхождение» with RAG + web; main answer unduplicated.  
**Depends on:** Phase 12 (payload shape stable).  
**Requirements:** UI-04, UI-05, UI-06  
**Success criteria:**
1. Newest turn adjacent to composer; history append order.
2. No stacked redundant «Источники» + raw `web` JSON for the same facts without hierarchy.
3. Labels in **Russian** describe what each subsection is for.

## Phase Details (v1.5 — active)

### Phase 14: F1DB RAG Corpus & Cross-Lingual Retrieval
**Goal:** RAG returns **ground-truth** from a **small whitelist** of f1db tables for realistic Russian questions; тексты чанков **читабельны для эмбеддингов** (не сырой дамп колонок); стратегия RU↔EN **задокументирована** (не обязательно билингвальные чанки).  
**Depends on:** Phase 13.  
**Requirements:** RAG-08, RAG-09  
**Success criteria:**
1. В репозитории зафиксирован **явный список** индексируемых CSV и **исключения** (большие шумные таблицы).
2. Spot checks: «Монако 2000», «чемпион 2021» → релевантные чанки (**david-coulthard** / **max-verstappen** или эквивалент) с выбранной нормализацией запроса.
3. Автотесты или стабильный скрипт проверки retrieval (план).

### Phase 15: Supervisor & Two-Step Web Fetch
**Goal:** Меньше ложных AGT-05, когда ответ уже в **title/snippet**; супервизор не «ломается» из‑за знания источника; до **двух** осмысленных fetch’ей, если первая страница пуста по фактам.  
**Depends on:** Phase 14 (RAG baseline clear).  
**Requirements:** AGT-08, AGT-09, SRCH-05  
**Success criteria:**
1. Супервизор: только **соответствие ответа вопросу**; **без** подсказки «из RAG / из веб / из заголовка».
2. Цепочка: RAG → (reject) → Tavily → достаточно title/snippet? → иначе GigaChat выбирает **2 URL** → fetch #1 → при необходимости fetch #2 (**макс. 2**); суммарные лимиты времени/размера.
3. Воркер: явные инструкции принять ответ **только** из title/snippet, если факт там выражен; супервизор может принять такой кандидат.

### Phase 16: README, README_DETAILED & Smokes
**Goal:** New contributors understand **data flow and file roles**; onboarding stays copy-paste friendly.  
**Depends on:** Phase 15.  
**Requirements:** DOC-01, DOC-02, TST-01  
**Success criteria:**
1. **README**: env, index build, API + Streamlit (DOC-01).
2. **README_DETAILED.md**: map of `src/`, graph nodes, retrieval, API contracts, Streamlit (DOC-02).
3. Pytest marker + opt-in live smokes (TST-01); default CI offline/mocked.

## Phase Details (v1.6 — active)

### Phase 17: TimeAPI & FastF1 schedule services
**Goal:** The system has a **single authoritative UTC/unix «now»** from TimeAPI.io with bounded HTTP behavior, and can resolve the **next Formula 1 grand prix** (non-testing) and **upcoming session times in UTC** from FastF1 relative to that instant—without the model guessing dates.  
**Depends on:** Phase 16  
**Requirements:** TIME-01, SCHED-01  
**Success Criteria** (what must be TRUE):
1. An operator or automated check can call the time service and receive **current UTC** (and/or unix epoch) from TimeAPI within a **configured timeout**; on API/network failure, the user-visible or downstream behavior matches the phase plan (**fixed Russian degraded message**, or **documented** fallback only if explicitly chosen in the plan).
2. For a chosen **season year** (default: calendar year from that UTC «now», with **late-December rollover** handled per plan—e.g. consult next year’s schedule when the next race is in January), the resolver returns the **next race weekend** where **`RoundNumber > 0`**, **testing rounds are excluded**, and the selected event’s **next relevant session or event UTC time** is **strictly after** the TimeAPI timestamp.
3. The resolver’s structured payload includes **event / grand prix naming**, **country or circuit** as FastF1 provides, and **UTC dates/times for sessions** of the upcoming weekend (or the agreed subset documented in the plan).
4. **FastF1 ergast / pre-2018** session-time limitations are **documented** wherever schedule results are described (README, tool docstrings, or operator notes) so users know when times are approximate.

**Plans:** TBD

### Phase 18: Worker time & schedule tools
**Goal:** The GigaChat **worker** can call **LangGraph/LangChain tools** for **«сейчас»** and **next GP / session schedule** so answers about upcoming races are grounded in **TIME-01 + SCHED-01**; failures are explicit and **do not break** the rest of the turn.  
**Depends on:** Phase 17  
**Requirements:** TOOL-01  
**Success Criteria** (what must be TRUE):
1. The worker graph exposes **one or two tools** (combined or separate per plan): **current time** wrapping TIME-01 and **next GP / schedule** wrapping SCHED-01, callable from the same tool surface as other worker tools.
2. In end-to-end or scripted checks, questions about **«когда следующая гонка»** / **current season «now»** lead the worker to use these tools instead of inventing calendar facts when the question requires live schedule or clock.
3. When TimeAPI or schedule resolution fails, the tool returns a **clear error** to the model; the **supervisor/RAG/web loop** continues to behave as for other tool failures (no uncaught exception aborting the graph).
4. **User-facing** assistant text remains **Russian** (or matches existing product language rules); errors are not leaked as raw stack traces to the end user.
5. If the phase plan agrees with **WEB-02** provenance, **`details`** (or the agreed field) **records** that time/schedule tools were used, without duplicating unrelated web payloads.

**Plans:** TBD

## Progress

**Execution order:** … → 9 → **12** → **13** → **14** (v1.5) → **15** → **16** → **17** (v1.6) → **18**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1–9 | … | Complete | 2026-03-27 — 2026-03-28 |
| 12. Supervisor reliability & single-pass web | 2/2 | Complete | 2026-03-28 |
| 13. Streamlit unified provenance & chat UX | 1/1 | Complete | 2026-03-28 |
| 14. F1DB RAG corpus & cross-lingual retrieval | 0/1 planned | Complete    | 2026-03-28 |
| 15. Supervisor & multi-URL web grounding | 0/TBD | Planned (v1.5) | — |
| 16. README, README_DETAILED & smokes | 0/TBD | Planned (v1.5) | — |
| 17. TimeAPI & FastF1 schedule services | 0/TBD | Planned (v1.6) | — |
| 18. Worker time & schedule tools | 0/TBD | Planned (v1.6) | — |
