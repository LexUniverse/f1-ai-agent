# Features Research

**Domain:** Supervisor agent with RAG sufficiency + Tavily fallback  
**Researched:** 2026-03-27  
**Confidence:** HIGH

## Table Stakes

- **Supervisor routing:** Decide RAG-only vs needs external web evidence.
- **RAG sufficiency signal:** Explicit boolean + reason (empty hits, low score, topic needs “today”).
- **Tavily path:** LLM-generated query → ranked snippets/pages → synthesis with URLs in citations.
- **Removal of F1 REST:** No `f1api.dev` branch; freshness from Tavily when RAG insufficient.
- **RU answers:** Preserve structured `details`, confidence, citations compatible with Streamlit.

## Differentiators (optional this milestone)

- **Parallel fan-out:** Supervisor triggers RAG retrieval while classifying intent (if latency budget allows).
- **Multi-query Tavily:** Reformulate query on empty/low-quality results (phase 2 of graph).

## Anti-Features

- Silent web search without user-visible source attribution.
- Unlimited Tavily calls per question (cost + latency).

## Dependencies on Existing System

- Chroma + f1db ingestion unchanged.
- Async API session model unchanged.
- GigaChat outage → keep template fallback policy from v1.1.

## Complexity Notes

- Evaluating RAG “sufficiency” via pure scores is brittle; combine **retrieval metrics + LLM judge** behind a single internal API to simplify phases.
