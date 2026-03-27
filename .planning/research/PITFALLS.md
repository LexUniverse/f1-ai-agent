# Pitfalls Research

**Domain:** Adding Tavily + supervisor to RAG stack; removing F1 API  
**Researched:** 2026-03-27  
**Confidence:** HIGH

## Pitfalls

1. **Hidden web hallucination:** Model cites Tavily snippets that do not support the claim.  
   **Prevention:** Require URL-per-fact in prompt; surface raw URLs in `details`; lower confidence when only web.

2. **Cost/latency blowups:** Recursive search or broad queries.  
   **Prevention:** Cap Tavily calls per session turn; timeout; single reformulation max.

3. **Sufficiency gate always passes:** Weak retrieval still triggers confident answers.  
   **Prevention:** Minimum score/top-k diversity checks + LLM “can you answer from evidence only?” judge.

4. **LangGraph + async FastAPI deadlocks:** Blocking LLM in async route.  
   **Prevention:** Explicit executor; document in phase plan.

5. **Schema drift:** Removing `details.live` breaks Streamlit.  
   **Prevention:** Migration mapping `live` → `web_search` or version field; update UI in same phase.

6. **Integration tests flaky:** Live Tavily in CI.  
   **Prevention:** `pytest -m integration` optional; mock by default; document `RUN_INTEGRATION=1`.

7. **.env leakage in README:** Keys in examples.  
   **Prevention:** `.env.example` only placeholders; link to provider consoles.

## Phase Ownership

| Pitfall | Best addressed in |
|---------|-------------------|
| Web hallucination | Phase 9 (answer reliability) |
| Cost caps | Phase 8 or 9 |
| Streamlit contract | Phase 9 or dedicated UI sub-phase |
| CI integration | Phase 10 (tests + README) |
