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

from src.graph.tavily_tool import TavilyConfigError, run_tavily_search_once
from src.models.api_contracts import EvidenceItem
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
        "(real GigaChat judge is wired in phase 08-02)."
    )


def _empty_f1_state() -> F1TurnState:
    """Minimal seed so LangGraph START satisfies channel writes."""
    return cast(F1TurnState, {"user_question": ""})


def _node_retrieve(state: F1TurnState) -> dict[str, Any]:
    hits = retrieve_historical_context(
        state["normalized_query"],
        state["canonical_entity_ids"],
        top_k=5,
        min_score=0.35,
    )
    # Mirror retriever: each hit has "score" in [0,1] from 1 - distance.
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


def _route_after_sufficiency(state: F1TurnState) -> Literal["tavily", "rag_synthesize_stub"]:
    return "tavily" if state.get("needs_tavily") else "rag_synthesize_stub"


def _node_tavily(state: F1TurnState) -> dict[str, Any]:
    q = (state.get("tavily_query") or state["user_question"])[:500]
    try:
        web = run_tavily_search_once(q)
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


def _route_after_tavily(
    state: F1TurnState,
) -> Literal["web_synthesize_stub"] | Any:
    if state.get("terminal_status") == "failed":
        return END
    return "web_synthesize_stub"


def _node_rag_synthesize_stub(state: F1TurnState) -> dict[str, Any]:
    return {
        "synthesis_route": "stub_rag",
        "terminal_status": "ready",
        "out_message": "stub",
    }


def _node_web_synthesize_stub(state: F1TurnState) -> dict[str, Any]:
    return {
        "synthesis_route": "stub_web",
        "terminal_status": "ready",
        "out_message": "stub",
    }


def build_compiled_graph(*, judge_fn: JudgeFn | None = None):
    judge = judge_fn or _default_gigachat_judge
    graph = StateGraph(F1TurnState)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("sufficiency", _make_node_sufficiency(judge))
    graph.add_node("tavily", _node_tavily)
    graph.add_node("rag_synthesize_stub", _node_rag_synthesize_stub)
    graph.add_node("web_synthesize_stub", _node_web_synthesize_stub)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "sufficiency")
    graph.add_conditional_edges(
        "sufficiency",
        _route_after_sufficiency,
        {"tavily": "tavily", "rag_synthesize_stub": "rag_synthesize_stub"},
    )
    graph.add_conditional_edges(
        "tavily",
        _route_after_tavily,
        {"web_synthesize_stub": "web_synthesize_stub", END: END},
    )
    graph.add_edge("rag_synthesize_stub", END)
    graph.add_edge("web_synthesize_stub", END)
    return graph.compile()


def run_f1_turn_sync(state: F1TurnState) -> F1TurnState:
    merged: F1TurnState = {**_empty_f1_state(), **state}
    return cast(
        F1TurnState,
        build_compiled_graph().invoke(merged, config={"recursion_limit": 10}),
    )
