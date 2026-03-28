# Research summary — v1.6 TimeAPI + FastF1 schedule tools

**Milestone:** v1.6 — condensed from user spec + public API docs (full 4-dimension research skipped).

## Stack additions

- **HTTP:** `httpx` or existing project HTTP client for `https://www.timeapi.io/api/v1/time/current/utc` and/or `.../unix` ([Swagger](https://www.timeapi.io/swagger/index.html)).
- **Python:** `fastf1` (already common in F1 stacks; confirm in `pyproject.toml` / lockfile — add if missing).
- **No new DB** for v1.6 unless caching schedule in-memory per process is desired (FastF1 caches to disk by default).

## Feature table stakes

- One call returns **UTC now** for deterministic “next event” comparisons.
- **EventSchedule** for target year; filter **race weekends** (`RoundNumber > 0`), exclude **`testing`** format unless user asks for tests.
- **Session*DateUtc** for ordering “next session” / weekend boundaries (2018+ full fidelity).

## Architecture notes

- Implement **thin service modules** (time client, schedule resolver) bound as **LangChain `@tool`** or graph node callables; keep **secrets**: none for TimeAPI (public GET).
- **Year selection:** default `year = pd.Timestamp(utc_now).year` with edge case: late December — next season’s first event might be next calendar year (plan should handle December → try current and next year schedule).

## Pitfalls

- **TimeAPI** rate limits / downtime → degraded UX (**TIME-01**).
- **FastF1** first load can be slow (cache dir); document cache path for operators.
- **Ergast / pre-2018** session times approximate — document in tool docstrings or operator README when v1.6 touches docs.
- **Timezone:** compare using **UTC** everywhere; FastF1 provides `Session*DateUtc`.

---
*Synthesized: 2026-03-28 — lightweight substitute for parallel project-research agents.*
