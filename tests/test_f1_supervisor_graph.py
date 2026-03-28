from types import SimpleNamespace

import pytest

import src.graph.f1_turn_graph as f1g
from src.answer.gigachat_rag import GIGACHAT_SUCCESS_ROUTE, GIGACHAT_WEB_ROUTE, GigachatRUSynthesisResult
from src.graph.f1_turn_graph import F1TurnState, build_compiled_graph
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer
from src.search.messages_ru import UNABLE_TO_ANSWER_SUPERVISOR_RU


def _base_state() -> F1TurnState:
    return {
        "user_question": "Кто выиграл последнюю гонку?",
        "normalized_query": "кто выиграл последнюю гонку",
        "canonical_entity_ids": [],
        "entity_tags": [],
    }


def test_supervisor_accepts_rag_skips_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [
        {"source_id": "f1db:t", "snippet": "text", "score": 0.5},
    ]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)

    def _fail_tavily(_q: str) -> list[dict]:
        pytest.fail("Tavily must not run when supervisor accepts RAG")

    monkeypatch.setattr(f1g, "run_tavily_search_once", _fail_tavily)
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)

    def _fake_hist(**kwargs):
        return GigachatRUSynthesisResult(
            message="rag-ok",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:\n[1] f1db:t",
                citation_count=1,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", lambda **k: _fake_hist(**k))
    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert out.get("out_message") == "rag-ok"
    assert out.get("synthesis_route") == GIGACHAT_SUCCESS_ROUTE


def test_one_tavily_then_agt05(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [{"source_id": "f1db:t", "snippet": "text", "score": 0.5}]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: False)
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "q")
    monkeypatch.setattr(
        f1g,
        "gigachat_plan_web_use",
        lambda **_: SimpleNamespace(best_url="https://ex.test", titles_sufficient=True),
    )

    calls = {"n": 0}

    def _fake_tavily(_q: str) -> list[dict]:
        calls["n"] += 1
        if calls["n"] > 1:
            pytest.fail("At most one Tavily invocation per turn")
        return [{"url": "https://ex.test", "content": "snippet"}]

    monkeypatch.setattr(f1g, "run_tavily_search_once", _fake_tavily)

    def _fake_hist(**kwargs):
        return GigachatRUSynthesisResult(
            message="rag-first",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:\n[1] f1db:t",
                citation_count=1,
            ),
        )

    def _fake_web(**kwargs):
        return GigachatRUSynthesisResult(
            message="web-attempt",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Веб", body="w")],
                sources_block_ru="Источники:\n[1] https://ex.test",
                citation_count=1,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", lambda **k: _fake_hist(**k))
    monkeypatch.setattr(f1g, "gigachat_synthesize_from_web_results", lambda **k: _fake_web(**k))

    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert out.get("web_search_rounds") == 1
    assert out.get("out_message") == UNABLE_TO_ANSWER_SUPERVISOR_RU
    assert out.get("synthesis_route") == "supervisor_gave_up"


def test_supervisor_accepts_after_one_web(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [{"source_id": "f1db:t", "snippet": "text", "score": 0.5}]
    monkeypatch.setattr(f1g, "retrieve_historical_context", lambda *_a, **_k: hits)
    monkeypatch.setattr(f1g, "gigachat_author_tavily_query", lambda **_: "q")
    monkeypatch.setattr(
        f1g,
        "gigachat_plan_web_use",
        lambda **_: SimpleNamespace(best_url="https://ex.test", titles_sufficient=True),
    )

    sup_calls = {"n": 0}

    def _supervisor(**kwargs):
        sup_calls["n"] += 1
        return sup_calls["n"] >= 2

    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **k: _supervisor(**k))

    tavily_calls = {"n": 0}

    def _tavily(_q: str) -> list[dict]:
        tavily_calls["n"] += 1
        return [{"url": "https://ex.test", "content": "x"}]

    monkeypatch.setattr(f1g, "run_tavily_search_once", _tavily)

    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **k: GigachatRUSynthesisResult(
            message="rag",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="b")],
                sources_block_ru="Источники:\n[1] f1db:t",
                citation_count=1,
            ),
        ),
    )
    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_from_web_results",
        lambda **k: GigachatRUSynthesisResult(
            message="web-accepted",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Веб", body="w")],
                sources_block_ru="Источники:\n[1] https://ex.test",
                citation_count=1,
            ),
        ),
    )

    g = build_compiled_graph()
    out = g.invoke(_base_state(), config={"recursion_limit": 25})
    assert tavily_calls["n"] == 1
    assert out.get("out_message") == "web-accepted"
    assert out.get("synthesis_route") == GIGACHAT_WEB_ROUTE
