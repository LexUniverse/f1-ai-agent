def test_historical_answer_uses_retrieved_context(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Феррари в Монако"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("ferrari monaco", ["team:ferrari", "race:monaco_gp"], ["team:ferrari", "race:monaco_gp"]),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [{"source_id": "f1db:race:1955-monaco", "snippet": "Ferrari won in Monaco 1955", "score": 0.88}],
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "Историческая сводка" in payload["message"]
    assert payload["details"]["evidence"]


def test_response_contains_traceable_evidence(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("max verstappen", ["driver:max_verstappen"], ["driver:max_verstappen"]),
    )
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [{"source_id": "f1db:driver:verstappen", "snippet": "Multiple wins in modern era", "score": 0.93}],
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    evidence = payload["details"]["evidence"][0]
    assert evidence["source_id"]
    assert evidence["snippet"]
    assert evidence["entity_tags"] == ["driver:max_verstappen"]
    assert evidence["rank_score"] > 0
    assert evidence["used_in_answer"] is True
