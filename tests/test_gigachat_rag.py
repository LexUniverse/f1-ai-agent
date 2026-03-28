import json
from types import SimpleNamespace

import src.graph.f1_turn_graph as f1g
from src.answer.gigachat_rag import (
    GIGACHAT_SUCCESS_ROUTE,
    GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU,
    GigachatRUSynthesisResult,
    gigachat_supervisor_accept_answer,
    gigachat_synthesize_from_web_results,
    gigachat_synthesize_historical,
)
from src.answer.russian_qna import build_sources_block_ru_from_evidence
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer


def _fake_response_content(obj: dict) -> SimpleNamespace:
    text = json.dumps(obj, ensure_ascii=False)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


def test_gigachat_synthesize_historical_returns_hybrid_structured_answer(monkeypatch):
    evidence = [
        EvidenceItem(
            source_id="f1db:x",
            snippet="Фрагмент про гонку.",
            entity_tags=[],
            rank_score=0.9,
        )
    ]

    class FakeGC:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def chat(self, chat):
            return _fake_response_content(
                {
                    "message": "Краткий ответ.",
                    "sections": [{"heading": "Сводка", "body": "Развërнутый текст."}],
                }
            )

    monkeypatch.setattr("src.answer.gigachat_rag.GigaChat", FakeGC)
    result = gigachat_synthesize_historical(evidence=evidence, user_question="что там?")
    block, _ = build_sources_block_ru_from_evidence(evidence)
    assert block in result.structured_answer.sources_block_ru
    assert "[1]" in result.structured_answer.sources_block_ru
    assert "f1db:x" in result.structured_answer.sources_block_ru
    assert result.message == "Краткий ответ."
    assert result.structured_answer.sections[0].heading == "Сводка"


def test_gigachat_supervisor_repair_round_accepts_after_bad_json(monkeypatch):
    calls = {"n": 0}

    class FakeGC:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def chat(self, chat):
            calls["n"] += 1
            if calls["n"] == 1:
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))]
                )
            return _fake_response_content({"accept": True})

    monkeypatch.setattr("src.answer.gigachat_rag.GigaChat", FakeGC)
    assert gigachat_supervisor_accept_answer(user_question="q?", candidate_answer="ok") is True
    assert calls["n"] == 2


def test_gigachat_synthesize_from_web_results_sources_contain_url(monkeypatch):
    web = [{"url": "https://example.com/f1", "content": "Race result snippet.", "title": "Ex"}]

    class FakeGC:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def chat(self, chat):
            return _fake_response_content(
                {
                    "message": "Ответ по вебу.",
                    "sections": [{"heading": "Итог", "body": "Текст."}],
                }
            )

    monkeypatch.setattr("src.answer.gigachat_rag.GigaChat", FakeGC)
    result = gigachat_synthesize_from_web_results(user_question="Кто выиграл?", web_results=web)
    assert "http" in result.structured_answer.sources_block_ru
    assert "example.com" in result.structured_answer.sources_block_ru


def test_chat_historical_next_message_uses_synthesis_route_when_mocked(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "fixture query"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", ["driver:x"], ["driver:x"]),
    )
    monkeypatch.setattr(
        f1g,
        "retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:test-src", "snippet": "Тестовый отрывок про гонку.", "score": 0.9},
        ],
    )
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)

    def fake_hist(*, evidence, user_question):
        block, cc = build_sources_block_ru_from_evidence(evidence)
        return GigachatRUSynthesisResult(
            message="Мок LLM сообщение.",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Тело.")],
                sources_block_ru=block,
                citation_count=cc,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", fake_hist)
    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_SUCCESS_ROUTE
    assert payload["message"] == "Мок LLM сообщение."


def test_historical_fallback_sets_synthesis_route_and_disclosure(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "fixture query"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", ["driver:x"], ["driver:x"]),
    )
    monkeypatch.setattr(
        f1g,
        "retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:test-src", "snippet": "Тестовый отрывок про гонку.", "score": 0.9},
        ],
    )
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)
    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["synthesis"]["route"] == "template_fallback"
    assert payload["details"]["synthesis"]["gigachat_error_class"] == "RuntimeError"
    assert GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU in payload["message"]


def test_success_path_has_no_disclosure_phrase(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "fixture query"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", ["driver:x"], ["driver:x"]),
    )
    monkeypatch.setattr(
        f1g,
        "retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:test-src", "snippet": "Тестовый отрывок про гонку.", "score": 0.9},
        ],
    )
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)

    def fake_hist(*, evidence, user_question):
        block, cc = build_sources_block_ru_from_evidence(evidence)
        return GigachatRUSynthesisResult(
            message="Успех без шаблона.",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Тело.")],
                sources_block_ru=block,
                citation_count=cc,
            ),
        )

    monkeypatch.setattr(f1g, "gigachat_synthesize_historical", fake_hist)
    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    payload = response.json()
    assert GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU not in payload["message"]
