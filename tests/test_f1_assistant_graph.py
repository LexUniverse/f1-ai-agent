import pytest

import src.graph.f1_turn_graph as f1g
from src.answer.gigachat_rag import GIGACHAT_SUCCESS_ROUTE, GIGACHAT_WEB_ROUTE, GigachatRUSynthesisResult
from src.answer.russian_qna import live_qna_confidence, qna_confidence_from_evidence
from src.graph.f1_turn_graph import F1TurnState, build_compiled_graph
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer


def _base_state() -> F1TurnState:
    return {
        "user_question": "Кто выиграл последнюю гонку?",
        "normalized_query": "кто выиграл последнюю гонку",
        "canonical_entity_ids": [],
        "entity_tags": [],
    }


def test_empty_evidence_routes_to_tavily_web(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "test query")
    monkeypatch.setattr(
        f1g,
        "run_tavily_search_once",
        lambda _q: [{"url": "https://example.com", "content": "x"}],
    )

    def _fake_web(**kwargs):
        return GigachatRUSynthesisResult(
            message="ok",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="body")],
                sources_block_ru="Источники:\n[1] https://example.com — x",
                citation_count=1,
            ),
            confidence=live_qna_confidence(),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_from_web_results", lambda **k: _fake_web(**k))
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("web_results")
    assert out.get("synthesis_route") == GIGACHAT_WEB_ROUTE


def test_strong_score_skips_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [
        {"source_id": "f1db:t", "snippet": "text", "score": 0.5},
        {"source_id": "f1db:t2", "snippet": "more", "score": 0.48},
    ]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)

    def _fail_tavily(_q: str) -> list[dict]:
        pytest.fail("Tavily must not run when RAG score is strong")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _fail_tavily)

    ev = [
        EvidenceItem(source_id="f1db:t", snippet="text", entity_tags=[], rank_score=0.5),
        EvidenceItem(source_id="f1db:t2", snippet="more", entity_tags=[], rank_score=0.48),
    ]

    def _fake_hist(**kwargs):
        return GigachatRUSynthesisResult(
            message="hist",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:\n[1] f1db:t",
                citation_count=1,
            ),
            confidence=qna_confidence_from_evidence(ev),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", lambda **k: _fake_hist(**k))
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("synthesis_route") == GIGACHAT_SUCCESS_ROUTE


def test_tavily_failure_sets_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: [])
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "q")

    def _boom(_q: str) -> list[dict]:
        raise RuntimeError("network")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _boom)
    g = build_compiled_graph(judge_fn=lambda *_args, **_kw: True)
    out = g.invoke(_base_state(), config={"recursion_limit": 10})
    assert out.get("error_code") == "WEB_SEARCH_UNAVAILABLE"
    assert out.get("terminal_status") == "failed"
