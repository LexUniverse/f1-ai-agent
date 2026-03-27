from src.integrations.f1api_client import LiveUpstreamError
from src.live.messages_ru import LIVE_UNAVAILABLE_MESSAGE_RU


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

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["code"] == "OK"
    assert payload["details"]["evidence"]
    assert spy["called"] is False
