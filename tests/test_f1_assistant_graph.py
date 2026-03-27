import pytest

import src.graph.f1_turn_graph as f1g
from src.graph.f1_turn_graph import F1TurnState, build_compiled_graph


def _base_state() -> F1TurnState:
    return {
        "user_question": "Кто выиграл последнюю гонку?",
        "normalized_query": "кто выиграл последнюю гонку",
        "canonical_entity_ids": [],
        "entity_tags": [],
    }


def test_empty_evidence_routes_to_tavily_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])
    monkeypatch.setattr(
        f1g,
        "run_tavily_search_once",
        lambda _q: [{"url": "https://example.com", "content": "x"}],
    )
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("web_results")
    assert out.get("synthesis_route") == "stub_web"


def test_strong_score_skips_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [
        {"source_id": "f1db:t", "snippet": "text", "score": 0.5},
        {"source_id": "f1db:t2", "snippet": "more", "score": 0.48},
    ]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)

    def _fail_tavily(_q: str) -> list[dict]:
        pytest.fail("Tavily must not run when RAG score is strong")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _fail_tavily)
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("synthesis_route") == "stub_rag"


def test_tavily_failure_sets_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])

    def _boom(_q: str) -> list[dict]:
        raise RuntimeError("network")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _boom)
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("error_code") == "WEB_SEARCH_UNAVAILABLE"
    assert out.get("terminal_status") == "failed"
