from src.answer.gigachat_rag import GIGACHAT_SUCCESS_ROUTE, GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU, GigachatRUSynthesisResult
from src.answer.russian_qna import (
    build_live_structured_ru_answer,
    build_sources_block_ru_from_evidence,
    live_fresh_user_message_ru,
    live_qna_confidence,
    qna_confidence_from_evidence,
)
from src.integrations.f1api_client import LiveUpstreamError
from src.live.messages_ru import LIVE_UNAVAILABLE_MESSAGE_RU
from src.models.api_contracts import AnswerSection, StructuredRUAnswer


def test_live_enriches_when_rag_empty_and_gate_true(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "current standings please"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", [], []),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [],
    )

    class _OkClient:
        def fetch_current_next(self):
            return ({"raceName": "Test GP"}, "2026-03-27T12:00:00Z")

    client.app.state.f1_api_client = _OkClient()

    def fake_live(*, summary_ru, user_question, as_of_utc_z):
        base = build_live_structured_ru_answer(summary_ru=summary_ru)
        return GigachatRUSynthesisResult(
            message=live_fresh_user_message_ru(as_of_utc_z=as_of_utc_z, summary_ru=summary_ru),
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Актуальные данные", body=summary_ru)],
                sources_block_ru=base.sources_block_ru,
                citation_count=base.citation_count,
            ),
            confidence=live_qna_confidence(),
        )

    monkeypatch.setattr("src.api.chat.gigachat_synthesize_live", fake_live)

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["code"] == "OK"
    assert "live" in payload["details"]
    assert payload["details"]["live"]["provider"] == "f1api.dev"
    assert payload["details"]["live"]["as_of"] == "2026-03-27T12:00:00Z"
    assert payload["details"]["live"]["as_of"] in payload["message"]
    assert "Актуально на " in payload["message"]
    assert "structured_answer" in payload["details"]
    assert "confidence" in payload["details"]
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_SUCCESS_ROUTE


def test_live_fallback_on_gigachat_error(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "current standings please"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", [], []),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        "src.api.chat.gigachat_synthesize_live",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("llm")),
    )

    class _OkClient:
        def fetch_current_next(self):
            return ({"raceName": "Test GP"}, "2026-03-27T12:00:00Z")

    client.app.state.f1_api_client = _OkClient()

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "live" in payload["details"]
    assert payload["details"]["synthesis"]["route"] == "template_fallback"
    assert payload["details"]["synthesis"]["gigachat_error_class"] == "ValueError"
    assert GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU in payload["message"]


def test_retrieval_no_evidence_when_gate_false(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "who won monaco 1996"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", [], []),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [],
    )

    class _FailIfCalled:
        def fetch_current_next(self):
            raise AssertionError("live client must not be called")

    client.app.state.f1_api_client = _FailIfCalled()

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["details"]["code"] == "RETRIEVAL_NO_EVIDENCE"
    assert payload["message"] == "Недостаточно исторических данных в базе f1db."


def test_live_unavailable_degraded(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "current standings please"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("q", [], []),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [],
    )

    class _Boom:
        def fetch_current_next(self):
            raise LiveUpstreamError("boom")

    client.app.state.f1_api_client = _Boom()

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["details"]["code"] == "LIVE_UNAVAILABLE"
    assert payload["message"] == LIVE_UNAVAILABLE_MESSAGE_RU
    assert "structured_answer" not in payload["details"]
    assert "confidence" not in payload["details"]
    assert payload["details"]["evidence"] == []


def test_no_live_when_evidence_present(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "current standings please"

    spy = {"called": False}

    class _Spy:
        def fetch_current_next(self):
            spy["called"] = True
            raise AssertionError("live client must not be called when RAG has evidence")

    client.app.state.f1_api_client = _Spy()

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
            message="Мок.",
            structured_answer=StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Текст.")],
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
    assert payload["details"]["code"] == "OK"
    assert payload["details"]["evidence"]
    assert spy["called"] is False
