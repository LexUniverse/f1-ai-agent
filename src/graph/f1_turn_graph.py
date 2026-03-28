"""
F1 assistant turn as a compiled LangGraph: retrieve → RAG synthesis → supervisor loop
with at most one Tavily call per turn after a rejected RAG answer; optional page fetch
before web synthesis (Phase 12 AGT-07 / SRCH-04).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, TypedDict, cast

import requests
from langgraph.graph import END, START, StateGraph

from src.answer.gigachat_rag import (
    GIGACHAT_FALLBACK_ROUTE,
    GIGACHAT_SUCCESS_ROUTE,
    GIGACHAT_WEB_ROUTE,
    append_fallback_disclosure_ru,
    gigachat_author_tavily_query,
    gigachat_plan_web_use,
    gigachat_supervisor_accept_answer,
    gigachat_synthesize_from_web_results,
    gigachat_synthesize_historical,
)
from src.graph.agent_trace import agent_trace
from src.graph.page_fetch import fetch_url_text_plain
from src.answer.russian_qna import (
    build_sources_block_ru_from_evidence,
    build_structured_ru_answer,
    tier_ru_from_max_score,
)
from src.graph.tavily_tool import TavilyConfigError, run_tavily_search_once
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer
from src.retrieval.evidence import format_evidence
from src.retrieval.retriever import retrieve_historical_context
from src.search.messages_ru import UNABLE_TO_ANSWER_SUPERVISOR_RU, WEB_SEARCH_UNAVAILABLE_MESSAGE_RU

JudgeFn = Callable[[str, list[EvidenceItem]], bool]


class F1TurnState(TypedDict, total=False):
    user_question: str
    normalized_query: str
    canonical_entity_ids: list[str]
    entity_tags: list[str]
    evidence: list[EvidenceItem]
    retrieval_hits: list[dict[str, Any]]
    top_score: float
    web_search_rounds: int
    candidate_message: str
    candidate_structured: dict[str, Any]
    supervisor_accept: bool
    synthesis_route: str
    tavily_queries: list[str]
    web_results: list[dict[str, Any]]
    last_web_batch: list[dict[str, Any]]
    synthesis_meta: dict[str, Any]
    error_code: str | None
    terminal_status: str
    out_message: str
    out_details: dict[str, Any]
    web_plan_best_url: str
    web_titles_sufficient: bool
    fetched_page_excerpt: str
    web_provenance_fetch: dict[str, Any] | None
    tavily_blocked: bool


def _default_gigachat_judge(_user_question: str, _evidence: list[EvidenceItem]) -> bool:
    raise NotImplementedError(
        "Legacy judge_fn is unused in the supervisor graph; pass judge_fn only for API compatibility."
    )


def _empty_f1_state() -> F1TurnState:
    return cast(
        F1TurnState,
        {
            "user_question": "",
            "web_search_rounds": 0,
            "tavily_queries": [],
            "web_results": [],
            "last_web_batch": [],
            "tavily_blocked": False,
        },
    )


def _node_retrieve(state: F1TurnState) -> dict[str, Any]:
    q = (state.get("user_question") or "").strip()
    hits = retrieve_historical_context(
        q,
        [],
        top_k=10,
        min_score=0.25,
    )
    top_score = max((float(h["score"]) for h in hits), default=0.0)
    evidence = format_evidence(hits, state.get("entity_tags") or [])
    preview = ", ".join(f"{h.get('source_id')}({h.get('score', 0):.2f})" for h in hits[:5])
    agent_trace("retrieve", f"hits={len(hits)} top_score={top_score:.3f} | {preview}")
    return {
        "retrieval_hits": hits,
        "top_score": top_score,
        "evidence": evidence,
    }


def _compact_evidence_for_provenance(evidence: list[EvidenceItem]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for e in evidence:
        sn = e.snippet
        if len(sn) > 400:
            sn = sn[:400] + "…"
        out.append(
            {
                "source_id": e.source_id,
                "snippet": sn,
                "entity_tags": list(e.entity_tags or []),
            }
        )
    return out


def _build_provenance_snapshot(state: F1TurnState, synthesis: dict[str, Any]) -> dict[str, Any]:
    evidence = state.get("evidence") or []
    rag = {
        "normalized_query": state.get("normalized_query") or "",
        "evidence": _compact_evidence_for_provenance(evidence),
    }
    prov: dict[str, Any] = {"rag": rag, "synthesis": dict(synthesis)}
    web_used = int(state.get("web_search_rounds", 0)) > 0
    if web_used:
        web_block: dict[str, Any] = {
            "queries": list(state.get("tavily_queries") or []),
            # Same row shape as graph `web_results` (Tavily rows); API layer also mirrors this in details.web.
            "results": list(state.get("web_results") or []),
        }
        wf = state.get("web_provenance_fetch")
        if isinstance(wf, dict) and (wf.get("url") or "").strip():
            web_block["fetch"] = wf
        prov["web"] = web_block
    return prov


def _web_sources_fallback(web_results: list[dict[str, Any]]) -> tuple[str, int]:
    lines: list[str] = ["Источники:"]
    for n, row in enumerate(web_results, start=1):
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        excerpt = content[:80] + ("…" if len(content) > 80 else "")
        lines.append(f"[{n}] {url} — {excerpt}")
    return "\n".join(lines), len(web_results)


def _node_agent1_rag(state: F1TurnState) -> dict[str, Any]:
    evidence = state.get("evidence") or []
    agent_trace(
        "agent1_rag",
        f"evidence={len(evidence)} ctx_lens={[len((e.context_for_llm or e.snippet or '')) for e in evidence[:5]]}",
    )
    try:
        result = gigachat_synthesize_historical(evidence=evidence, user_question=state["user_question"])
        agent_trace("agent1_rag", f"→ GigaChat OK message_preview={(result.message or '')[:180]!r}")
        return {
            "candidate_message": result.message,
            "candidate_structured": result.structured_answer.model_dump(),
            "synthesis_route": GIGACHAT_SUCCESS_ROUTE,
            "synthesis_meta": {},
        }
    except Exception as exc:
        structured = build_structured_ru_answer(evidence)
        summary = evidence[0].snippet.strip()[:120] if evidence else ""
        max_sc = max((e.rank_score for e in evidence), default=0.0)
        tier = tier_ru_from_max_score(max_sc)
        base_message = f"Историческая сводка: {summary}. Уверенность: {tier}."
        message = append_fallback_disclosure_ru(base_message)
        agent_trace("agent1_rag", f"→ template fallback ({type(exc).__name__}) preview={message[:120]!r}")
        return {
            "candidate_message": message,
            "candidate_structured": structured.model_dump(),
            "synthesis_route": GIGACHAT_FALLBACK_ROUTE,
            "synthesis_meta": {"gigachat_error_class": type(exc).__name__},
        }


def _node_supervisor(state: F1TurnState) -> dict[str, Any]:
    accept = gigachat_supervisor_accept_answer(
        user_question=state["user_question"],
        candidate_answer=state["candidate_message"],
    )
    agent_trace(
        "supervisor",
        f"accept={accept} candidate_preview={(state.get('candidate_message') or '')[:200]!r}",
    )
    return {"supervisor_accept": accept}


def _route_after_supervisor(state: F1TurnState) -> Literal["finalize_accept", "finalize_fail", "tavily_search"]:
    if state.get("supervisor_accept"):
        return "finalize_accept"
    if int(state.get("web_search_rounds", 0)) >= 1:
        return "finalize_fail"
    return "tavily_search"


def _node_tavily_search(state: F1TurnState) -> dict[str, Any]:
    uq = state["user_question"]
    prev_q = list(state.get("tavily_queries") or [])
    wr = int(state.get("web_search_rounds", 0))
    try:
        authored = gigachat_author_tavily_query(user_question=uq)
        q = (authored or uq).strip()[:500]
    except Exception:
        q = uq[:500]
    try:
        web = run_tavily_search_once(q)
        if not web:
            agent_trace("tavily", f"no results or disabled, query={q[:80]!r} → fallback RAG-only")
            return {
                "tavily_queries": prev_q + [q],
                "tavily_blocked": True,
            }
        merged = list(state.get("web_results") or [])
        merged.extend(web)
        agent_trace("tavily", f"results={len(web)} query={q[:80]!r}")
        return {
            "tavily_queries": prev_q + [q],
            "web_search_rounds": wr + 1,
            "last_web_batch": web,
            "web_results": merged,
            "error_code": None,
            "tavily_blocked": False,
        }
    except (TavilyConfigError, requests.RequestException, OSError, RuntimeError, ValueError) as exc:
        agent_trace("tavily", f"error {type(exc).__name__}: {exc!s} → fallback RAG-only")
        return {
            "tavily_queries": prev_q + [q],
            "tavily_blocked": True,
        }
    except Exception as exc:
        agent_trace("tavily", f"error {type(exc).__name__}: {exc!s} → fallback RAG-only")
        return {
            "tavily_queries": prev_q + [q],
            "tavily_blocked": True,
        }


def _route_after_tavily(state: F1TurnState):
    if state.get("tavily_blocked"):
        return "finalize_rag_no_tavily"
    return "web_plan"


def _route_after_web_plan(state: F1TurnState) -> Literal["fetch_page", "agent1_web"]:
    if state.get("web_titles_sufficient"):
        return "agent1_web"
    url = (state.get("web_plan_best_url") or "").strip()
    if not url:
        return "agent1_web"
    return "fetch_page"


def _node_finalize_rag_no_tavily(state: F1TurnState) -> dict[str, Any]:
    """После отклонения RAG супервизором веб недоступен — повторный синтез только по полным чанкам."""
    evidence = state.get("evidence") or []
    uq = state["user_question"]
    agent_trace("finalize_rag_no_tavily", f"re-synthesize RAG-only evidence={len(evidence)}")
    hint = (
        "[Поиск в интернете недоступен. Ответь только по контексту ниже. "
        "Если вопрос про победителя гонки и в контексте есть «Итог гонки» / место 1 для нужного Гран-при — назови пилота и команду.]\n"
    )
    try:
        result = gigachat_synthesize_historical(evidence=evidence, user_question=hint + uq)
        agent_trace("finalize_rag_no_tavily", f"→ GigaChat OK {(result.message or '')[:200]!r}")
        return {
            "candidate_message": result.message,
            "candidate_structured": result.structured_answer.model_dump(),
            "synthesis_route": "gigachat_rag_no_web",
            "synthesis_meta": {"skipped_tavily": True},
        }
    except Exception as exc:
        body = ""
        if evidence:
            body = (evidence[0].context_for_llm or evidence[0].snippet or "")[:4000]
        if not body.strip():
            body = "Веб-поиск недоступен; не удалось получить развёрнутый текст из локальной базы для ответа."
        block, cc = build_sources_block_ru_from_evidence(evidence)
        structured = StructuredRUAnswer(
            sections=[AnswerSection(heading="По данным базы", body=body)],
            sources_block_ru=block,
            citation_count=cc,
        )
        msg = append_fallback_disclosure_ru(
            f"Кратко по базе (шаблон, GigaChat: {type(exc).__name__}). См. раздел ниже."
        )
        agent_trace("finalize_rag_no_tavily", f"→ template ({type(exc).__name__})")
        return {
            "candidate_message": msg,
            "candidate_structured": structured.model_dump(),
            "synthesis_route": GIGACHAT_FALLBACK_ROUTE,
            "synthesis_meta": {"skipped_tavily": True, "gigachat_error_class": type(exc).__name__},
        }


def _node_web_plan(state: F1TurnState) -> dict[str, Any]:
    web = state.get("last_web_batch") or []
    plan = gigachat_plan_web_use(user_question=state["user_question"], web_results=web)
    return {
        "web_plan_best_url": (plan.best_url or "").strip(),
        "web_titles_sufficient": bool(plan.titles_sufficient),
        "fetched_page_excerpt": "",
        "web_provenance_fetch": None,
    }


def _node_fetch_page(state: F1TurnState) -> dict[str, Any]:
    url = (state.get("web_plan_best_url") or "").strip()
    if not url:
        return {"fetched_page_excerpt": "", "web_provenance_fetch": None}
    text = fetch_url_text_plain(url)
    ok = bool(text.strip())
    excerpt = (text[:12_000] + "…") if len(text) > 12_000 else text
    preview = (text[:240] + "…") if len(text) > 240 else text
    prov = {
        "url": url,
        "ok": ok,
        "error": None if ok else "empty_or_failed",
        "excerpt_preview": preview if ok else None,
    }
    return {
        "fetched_page_excerpt": excerpt if ok else "",
        "web_provenance_fetch": prov,
    }


def _node_agent1_web(state: F1TurnState) -> dict[str, Any]:
    web = state.get("last_web_batch") or []
    raw_excerpt = state.get("fetched_page_excerpt")
    excerpt = (raw_excerpt or "").strip() or None
    try:
        result = gigachat_synthesize_from_web_results(
            user_question=state["user_question"],
            web_results=web,
            fetched_page_excerpt=excerpt,
        )
        agent_trace("agent1_web", f"→ GigaChat OK {(result.message or '')[:200]!r}")
        return {
            "candidate_message": result.message,
            "candidate_structured": result.structured_answer.model_dump(),
            "synthesis_route": GIGACHAT_WEB_ROUTE,
            "synthesis_meta": {},
        }
    except Exception as exc:
        sources_block_ru, cc = _web_sources_fallback(web)
        body = "\n\n".join(str(w.get("content", ""))[:400] for w in web[:5]) or "Краткая выжимка по найденным страницам."
        structured = StructuredRUAnswer(
            sections=[AnswerSection(heading="По данным поиска", body=body)],
            sources_block_ru=sources_block_ru,
            citation_count=cc,
        )
        tier = tier_ru_from_max_score(0.55)
        base = f"Ответ по найденным веб-источникам (шаблон). Уверенность: {tier}."
        message = append_fallback_disclosure_ru(base)
        return {
            "candidate_message": message,
            "candidate_structured": structured.model_dump(),
            "synthesis_route": GIGACHAT_FALLBACK_ROUTE,
            "synthesis_meta": {"gigachat_error_class": type(exc).__name__},
        }


def _node_finalize_accept(state: F1TurnState) -> dict[str, Any]:
    web_used = int(state.get("web_search_rounds", 0)) > 0
    route = state.get("synthesis_route", GIGACHAT_SUCCESS_ROUTE)
    synthesis: dict[str, Any] = {"route": route}
    meta = state.get("synthesis_meta")
    if isinstance(meta, dict):
        synthesis.update(meta)
    details: dict[str, Any] = {
        "structured_answer": state["candidate_structured"],
        "synthesis": synthesis,
        "provenance": _build_provenance_snapshot(state, synthesis),
    }
    if web_used:
        details["tavily_queries"] = list(state.get("tavily_queries") or [])
        details["web_results"] = list(state.get("web_results") or [])
    return {
        "out_message": state["candidate_message"],
        "out_details": details,
        "terminal_status": "ready",
    }


def _node_finalize_fail(state: F1TurnState) -> dict[str, Any]:
    synthesis_fail: dict[str, Any] = {"route": "supervisor_gave_up"}
    details: dict[str, Any] = {
        "structured_answer": state.get("candidate_structured") or {},
        "synthesis": synthesis_fail,
        "tavily_queries": list(state.get("tavily_queries") or []),
        "web_results": list(state.get("web_results") or []),
        "provenance": _build_provenance_snapshot(state, synthesis_fail),
    }
    return {
        "out_message": UNABLE_TO_ANSWER_SUPERVISOR_RU,
        "out_details": details,
        "terminal_status": "ready",
        "synthesis_route": "supervisor_gave_up",
    }


def build_compiled_graph(*, judge_fn: JudgeFn | None = None):
    _ = judge_fn  # supervisor graph does not use score-based sufficiency
    graph = StateGraph(F1TurnState)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("agent1_rag", _node_agent1_rag)
    graph.add_node("supervisor", _node_supervisor)
    graph.add_node("tavily_search", _node_tavily_search)
    graph.add_node("finalize_rag_no_tavily", _node_finalize_rag_no_tavily)
    graph.add_node("web_plan", _node_web_plan)
    graph.add_node("fetch_page", _node_fetch_page)
    graph.add_node("agent1_web", _node_agent1_web)
    graph.add_node("finalize_accept", _node_finalize_accept)
    graph.add_node("finalize_fail", _node_finalize_fail)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "agent1_rag")
    graph.add_edge("agent1_rag", "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "finalize_accept": "finalize_accept",
            "finalize_fail": "finalize_fail",
            "tavily_search": "tavily_search",
        },
    )
    graph.add_conditional_edges(
        "tavily_search",
        _route_after_tavily,
        {"web_plan": "web_plan", "finalize_rag_no_tavily": "finalize_rag_no_tavily"},
    )
    graph.add_edge("finalize_rag_no_tavily", "finalize_accept")
    graph.add_conditional_edges(
        "web_plan",
        _route_after_web_plan,
        {"fetch_page": "fetch_page", "agent1_web": "agent1_web"},
    )
    graph.add_edge("fetch_page", "agent1_web")
    graph.add_edge("agent1_web", "supervisor")
    graph.add_edge("finalize_accept", END)
    graph.add_edge("finalize_fail", END)
    return graph.compile()


def run_f1_turn_sync(state: F1TurnState) -> F1TurnState:
    base = _empty_f1_state()
    merged: F1TurnState = {**base, **state}
    out = build_compiled_graph().invoke(merged, config={"recursion_limit": 25})
    final = cast(F1TurnState, out)
    if (
        final.get("terminal_status") == "failed"
        and final.get("error_code") == "WEB_SEARCH_UNAVAILABLE"
        and not (final.get("out_message") or "").strip()
    ):
        return cast(
            F1TurnState,
            {
                **final,
                "out_message": WEB_SEARCH_UNAVAILABLE_MESSAGE_RU,
            },
        )
    return final
