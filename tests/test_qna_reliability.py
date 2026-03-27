from src.answer.gigachat_rag import (
    GIGACHAT_FALLBACK_ROUTE,
    GIGACHAT_SUCCESS_ROUTE,
    GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU,
    GigachatRUSynthesisResult,
)
from src.answer.russian_qna import build_sources_block_ru_from_evidence, qna_confidence_from_evidence
from src.models.api_contracts import AnswerSection, StructuredRUAnswer


def test_success_includes_structured_answer_and_confidence(client, monkeypatch):
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
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:test-src", "snippet": "Тестовый отрывок про гонку.", "score": 0.9},
        ],
    )

    def fake_hist(*, evidence, user_question):
        block, cc = build_sources_block_ru_from_evidence(evidence)
        return GigachatRUSynthesisResult(
            message="Историческая сводка: мок. Уверенность: высокая.",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Тестовый отрывок про гонку.")],
                sources_block_ru=block,
                citation_count=cc,
            ),
            confidence=qna_confidence_from_evidence(evidence),
        )

    monkeypatch.setattr("src.api.chat.gigachat_synthesize_historical", fake_hist)

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "structured_answer" in payload["details"]
    assert "confidence" in payload["details"]
    assert payload["details"]["confidence"]["tier_ru"] == "высокая"
    assert payload["details"]["confidence"]["score"] == 0.9
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_SUCCESS_ROUTE
    sections = payload["details"]["structured_answer"]["sections"]
    assert isinstance(sections, list) and len(sections) >= 1
    assert sections[0]["heading"] == "Сводка"
    assert "Уверенность:" in payload["message"] or "мок" in payload["message"]
    assert payload["details"]["confidence"]["tier_ru"] in payload["message"]
    block = payload["details"]["structured_answer"]["sources_block_ru"]
    assert "[1]" in block
    assert "f1db:test-src" in block


def test_no_evidence_remains_failed_retrieval_no_evidence(client, monkeypatch):
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
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [],
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["details"]["code"] == "RETRIEVAL_NO_EVIDENCE"
    assert payload["details"]["evidence"] == []
    assert payload["message"] == "Недостаточно исторических данных в базе f1db."
    assert "structured_answer" not in payload["details"]


def test_citation_order_matches_evidence_order(client, monkeypatch):
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
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:first", "snippet": "First chunk text here.", "score": 0.7},
            {"source_id": "f1db:second", "snippet": "Second chunk text here.", "score": 0.72},
        ],
    )

    def fake_hist(*, evidence, user_question):
        block, cc = build_sources_block_ru_from_evidence(evidence)
        return GigachatRUSynthesisResult(
            message="Порядок цитат проверен.",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Два фрагмента.")],
                sources_block_ru=block,
                citation_count=cc,
            ),
            confidence=qna_confidence_from_evidence(evidence),
        )

    monkeypatch.setattr("src.api.chat.gigachat_synthesize_historical", fake_hist)

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert len(payload["details"]["evidence"]) == 2
    block = payload["details"]["structured_answer"]["sources_block_ru"]
    assert "Источники:" in block
    after = block.split("Источники:", 1)[1]
    assert "[1]" in after
    pos_first = after.find("f1db:first")
    pos_second = after.find("f1db:second")
    assert pos_first != -1 and pos_second != -1
    assert pos_first < pos_second
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_SUCCESS_ROUTE


def test_historical_template_fallback_includes_disclosure(client, monkeypatch):
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
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [
            {"source_id": "f1db:test-src", "snippet": "Тестовый отрывок про гонку.", "score": 0.9},
        ],
    )
    monkeypatch.setattr(
        "src.api.chat.gigachat_synthesize_historical",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("llm down")),
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_FALLBACK_ROUTE
    assert GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU in payload["message"]
