import pytest

import src.graph.f1_turn_graph as f1g
from src.answer.gigachat_rag import GIGACHAT_SUCCESS_ROUTE, GIGACHAT_WEB_ROUTE, GigachatRUSynthesisResult
from src.graph.f1_turn_graph import F1TurnState, build_compiled_graph
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer


def _base_state() -> F1TurnState:
    return {
        "user_question": "Кто выиграл последнюю гонку?",
        "normalized_query": "кто выиграл последнюю гонку",
        "canonical_entity_ids": [],
        "entity_tags": [],
    }


def test_empty_evidence_supervisor_accepts_after_web(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "test query")
    monkeypatch.setattr(
        f1g,
        "run_tavily_search_once",
        lambda _q: [{"url": "https://example.com", "content": "x"}],
    )

    sup_i = {"n": 0}

    def _sup(**_k):
        sup_i["n"] += 1
        return sup_i["n"] >= 2

    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **k: _sup(**k))

    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **k: GigachatRUSynthesisResult(
            message="rag-empty",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="body")],
                sources_block_ru="Источники:",
                citation_count=0,
            ),
        ),
    )

    def _fake_web(**kwargs):
        return GigachatRUSynthesisResult(
            message="ok",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="body")],
                sources_block_ru="Источники:\n[1] https://example.com — x",
                citation_count=1,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_from_web_results", lambda **k: _fake_web(**k))
    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert out.get("web_results")
    assert out.get("synthesis_route") == GIGACHAT_WEB_ROUTE


def test_strong_score_skips_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [
        {"source_id": "f1db:t", "snippet": "text", "score": 0.5},
        {"source_id": "f1db:t2", "snippet": "more", "score": 0.48},
    ]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)

    def _fail_tavily(_q: str) -> list[dict]:
        pytest.fail("Tavily must not run when supervisor accepts RAG")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _fail_tavily)
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)

    def _fake_hist(**kwargs):
        return GigachatRUSynthesisResult(
            message="hist",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:\n[1] f1db:t",
                citation_count=1,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", lambda **k: _fake_hist(**k))
    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert out.get("synthesis_route") == GIGACHAT_SUCCESS_ROUTE


def test_tavily_failure_sets_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "q")
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: False)

    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **k: GigachatRUSynthesisResult(
            message="x",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:",
                citation_count=0,
            ),
        ),
    )

    def _boom(_q: str) -> list[dict]:
        raise RuntimeError("network")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _boom)
    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert out.get("error_code") == "WEB_SEARCH_UNAVAILABLE"
    assert out.get("terminal_status") == "failed"
