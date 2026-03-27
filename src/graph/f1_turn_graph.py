"""
F1 assistant turn as a compiled LangGraph: retrieve → sufficiency → optional Tavily → synthesis.

top_score is max(hit["score"]) from retrieve_historical_context, matching retriever.py:
score = max(0.0, 1.0 - distance) per hit; hits below min_score are omitted by the retriever.
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
    gigachat_judge_rag_sufficient,
    gigachat_synthesize_from_web_results,
    gigachat_synthesize_historical,
)
from src.answer.russian_qna import build_structured_ru_answer, live_qna_confidence, qna_confidence_from_evidence
from src.graph.tavily_tool import TavilyConfigError, run_tavily_search_once
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer
from src.retrieval.evidence import format_evidence
from src.retrieval.retriever import retrieve_historical_context

JudgeFn = Callable[[str, list[EvidenceItem]], bool]


class F1TurnState(TypedDict, total=False):
    user_question: str
    normalized_query: str
    canonical_entity_ids: list[str]
    entity_tags: list[str]
    evidence: list[EvidenceItem]
    retrieval_hits: list[dict[str, Any]]
    top_score: float
    rag_sufficient: bool
    needs_tavily: bool
    tavily_query: str
    web_results: list[dict[str, Any]]
    synthesis_route: str
    error_code: str | None
    terminal_status: str
    out_message: str
    out_details: dict[str, Any]


def _default_gigachat_judge(_user_question: str, _evidence: list[EvidenceItem]) -> bool:
    raise NotImplementedError(
        "Borderline RAG scores require judge_fn=... in build_compiled_graph() "
        "(production uses gigachat_judge_rag_sufficient via run_f1_turn_sync)."
    )


def _empty_f1_state() -> F1TurnState:
    return cast(F1TurnState, {"user_question": ""})


def _node_retrieve(state: F1TurnState) -> dict[str, Any]:
    hits = retrieve_historical_context(
        state["normalized_query"],
        state["canonical_entity_ids"],
        top_k=5,
        min_score=0.35,
    )
    top_score = max((float(h["score"]) for h in hits), default=0.0)
    evidence = format_evidence(hits, state.get("entity_tags") or [])
    return {
        "retrieval_hits": hits,
        "top_score": top_score,
        "evidence": evidence,
    }


def _make_node_sufficiency(judge_fn: JudgeFn):
    def _node_sufficiency(state: F1TurnState) -> dict[str, Any]:
        evidence = state.get("evidence") or []
        top_score = float(state.get("top_score", 0.0))
        if not evidence:
            return {"rag_sufficient": False, "needs_tavily": True}
        if top_score >= 0.45:
            return {"rag_sufficient": True, "needs_tavily": False}
        if 0.35 <= top_score < 0.45:
            sufficient = bool(judge_fn(state["user_question"], evidence))
            return {"rag_sufficient": sufficient, "needs_tavily": not sufficient}
        return {"rag_sufficient": False, "needs_tavily": True}

    return _node_sufficiency


def _route_after_sufficiency(state: F1TurnState) -> Literal["tavily", "rag_synthesize"]:
    return "tavily" if state.get("needs_tavily") else "rag_synthesize"


def _web_sources_fallback(web_results: list[dict[str, Any]]) -> tuple[str, int]:
    lines: list[str] = ["Источники:"]
    for n, row in enumerate(web_results, start=1):
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        excerpt = content[:80] + ("…" if len(content) > 80 else "")
        lines.append(f"[{n}] {url} — {excerpt}")
    return "\n".join(lines), len(web_results)


def _node_tavily(state: F1TurnState) -> dict[str, Any]:
    uq = state["user_question"]
    try:
        authored = gigachat_author_tavily_query(user_question=uq)
        q = (authored or uq).strip()[:500]
    except Exception:
        q = uq[:500]
    try:
        web = run_tavily_search_once(q)
        if not web:
            return {
                "tavily_query": q,
                "web_results": [],
                "error_code": "WEB_SEARCH_UNAVAILABLE",
                "terminal_status": "failed",
                "out_message": "",
                "synthesis_route": "",
            }
        return {
            "tavily_query": q,
            "web_results": web,
            "error_code": None,
            "terminal_status": "ready",
        }
    except (TavilyConfigError, requests.RequestException, OSError, RuntimeError, ValueError):
        return {
            "tavily_query": q,
            "web_results": [],
            "error_code": "WEB_SEARCH_UNAVAILABLE",
            "terminal_status": "failed",
            "out_message": "",
            "synthesis_route": "",
        }
    except Exception:
        return {
            "tavily_query": q,
            "web_results": [],
            "error_code": "WEB_SEARCH_UNAVAILABLE",
            "terminal_status": "failed",
            "out_message": "",
            "synthesis_route": "",
        }


def _route_after_tavily(state: F1TurnState):
    if state.get("terminal_status") == "failed":
        return END
    return "web_synthesize"


def _node_rag_synthesize(state: F1TurnState) -> dict[str, Any]:
    evidence = state.get("evidence") or []
    try:
        result = gigachat_synthesize_historical(evidence=evidence, user_question=state["user_question"])
        return {
            "out_message": result.message,
            "out_details": {
                "structured_answer": result.structured_answer.model_dump(),
                "confidence": result.confidence.model_dump(),
                "synthesis": {"route": GIGACHAT_SUCCESS_ROUTE},
            },
            "terminal_status": "ready",
            "synthesis_route": GIGACHAT_SUCCESS_ROUTE,
        }
    except Exception as exc:
        structured = build_structured_ru_answer(evidence)
        conf = qna_confidence_from_evidence(evidence)
        summary = evidence[0].snippet.strip()[:120] if evidence else ""
        base_message = f"Историческая сводка: {summary}. Уверенность: {conf.tier_ru}."
        message = append_fallback_disclosure_ru(base_message)
        return {
            "out_message": message,
            "out_details": {
                "structured_answer": structured.model_dump(),
                "confidence": conf.model_dump(),
                "synthesis": {
                    "route": GIGACHAT_FALLBACK_ROUTE,
                    "gigachat_error_class": type(exc).__name__,
                },
            },
            "terminal_status": "ready",
            "synthesis_route": GIGACHAT_FALLBACK_ROUTE,
        }


def _node_web_synthesize(state: F1TurnState) -> dict[str, Any]:
    web = state.get("web_results") or []
    try:
        result = gigachat_synthesize_from_web_results(user_question=state["user_question"], web_results=web)
        return {
            "out_message": result.message,
            "out_details": {
                "structured_answer": result.structured_answer.model_dump(),
                "confidence": result.confidence.model_dump(),
                "synthesis": {"route": GIGACHAT_WEB_ROUTE},
            },
            "terminal_status": "ready",
            "synthesis_route": GIGACHAT_WEB_ROUTE,
        }
    except Exception as exc:
        sources_block_ru, cc = _web_sources_fallback(web)
        body = "\n\n".join(
            str(w.get("content", ""))[:400] for w in web[:5]
        ) or "Краткая выжимка по найденным страницам."
        structured = StructuredRUAnswer(
            sections=[AnswerSection(heading="По данным поиска", body=body)],
            sources_block_ru=sources_block_ru,
            citation_count=cc,
        )
        conf = live_qna_confidence()
        base = "Ответ по найденным веб-источникам (шаблон)."
        message = append_fallback_disclosure_ru(base)
        return {
            "out_message": message,
            "out_details": {
                "structured_answer": structured.model_dump(),
                "confidence": conf.model_dump(),
                "synthesis": {
                    "route": GIGACHAT_FALLBACK_ROUTE,
                    "gigachat_error_class": type(exc).__name__,
                },
            },
            "terminal_status": "ready",
            "synthesis_route": GIGACHAT_FALLBACK_ROUTE,
        }


def build_compiled_graph(*, judge_fn: JudgeFn | None = None):
    judge = judge_fn or _default_gigachat_judge
    graph = StateGraph(F1TurnState)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("sufficiency", _make_node_sufficiency(judge))
    graph.add_node("tavily", _node_tavily)
    graph.add_node("rag_synthesize", _node_rag_synthesize)
    graph.add_node("web_synthesize", _node_web_synthesize)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "sufficiency")
    graph.add_conditional_edges(
        "sufficiency",
        _route_after_sufficiency,
        {"tavily": "tavily", "rag_synthesize": "rag_synthesize"},
    )
    graph.add_conditional_edges(
        "tavily",
        _route_after_tavily,
        {"web_synthesize": "web_synthesize", END: END},
    )
    graph.add_edge("rag_synthesize", END)
    graph.add_edge("web_synthesize", END)
    return graph.compile()


def run_f1_turn_sync(state: F1TurnState) -> F1TurnState:
    merged: F1TurnState = {**_empty_f1_state(), **state}
    return cast(
        F1TurnState,
        build_compiled_graph(judge_fn=gigachat_judge_rag_sufficient).invoke(
            merged,
            config={"recursion_limit": 10},
        ),
    )
