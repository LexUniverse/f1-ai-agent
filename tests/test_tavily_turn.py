from src.answer.gigachat_rag import GIGACHAT_SUCCESS_ROUTE
from src.models.api_contracts import EvidenceItem
from src.search.messages_ru import WEB_SEARCH_UNAVAILABLE_MESSAGE_RU


def test_web_search_unavailable_message_stable(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "current standings please"

    monkeypatch.setattr(
        "src.api.chat.run_f1_turn_sync",
        lambda _state: {
            "terminal_status": "failed",
            "error_code": "WEB_SEARCH_UNAVAILABLE",
            "evidence": [],
            "out_message": "",
            "out_details": {},
        },
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["details"]["code"] == "WEB_SEARCH_UNAVAILABLE"
    assert payload["message"] == WEB_SEARCH_UNAVAILABLE_MESSAGE_RU
    assert payload["details"]["evidence"] == []
    assert "structured_answer" not in payload["details"]


def test_historical_path_still_works(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "who won monaco 1996"

    ev = [
        EvidenceItem(
            source_id="f1db:test-src",
            snippet="Тестовый отрывок про гонку.",
            entity_tags=["driver:x"],
            rank_score=0.9,
            used_in_answer=True,
        )
    ]

    monkeypatch.setattr(
        "src.api.chat.run_f1_turn_sync",
        lambda _state: {
            "terminal_status": "ready",
            "error_code": None,
            "evidence": ev,
            "out_message": "Мок.",
            "out_details": {
                "structured_answer": {
                    "sections": [{"heading": "Сводка", "body": "Текст."}],
                    "sources_block_ru": "Источники:\n[1] x",
                    "citation_count": 1,
                },
                "synthesis": {"route": GIGACHAT_SUCCESS_ROUTE},
            },
            "synthesis_route": GIGACHAT_SUCCESS_ROUTE,
        },
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["details"]["code"] == "OK"
    assert payload["details"]["synthesis"]["route"] == GIGACHAT_SUCCESS_ROUTE
    assert "structured_answer" in payload["details"]
