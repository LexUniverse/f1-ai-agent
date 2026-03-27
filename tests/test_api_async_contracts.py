from uuid import UUID

from conftest import assert_error_envelope
from src.api.chat import PROCESS_CALLS


def test_start_chat_returns_uuid_session_id(client):
    response = client.post("/start_chat", json={"access_code": "ABC123"})
    assert response.status_code == 200
    payload = response.json()
    parsed = UUID(payload["session_id"], version=4)
    assert str(parsed) == payload["session_id"]


def test_invalid_payload_returns_enveloped_validation_error(client):
    response = client.post("/start_chat", json={"access_code": {"bad": "type"}})
    assert response.status_code == 422
    body = response.json()
    assert_error_envelope(body, "VALIDATION_ERROR")
    assert "errors" in body["error"]["details"]


def test_auth_failure_is_enveloped(client):
    response = client.post("/start_chat", json={"access_code": "BAD"})
    assert response.status_code == 401
    assert_error_envelope(response.json(), "AUTH_INVALID_CODE")


def test_session_state_http_mapping(client):
    missing = client.get("/message_status", headers={"X-Session-Id": "does-not-exist"})
    assert missing.status_code == 404
    assert_error_envelope(missing.json(), "SESSION_NOT_FOUND")

    unauthorized = client.app.state.session_store.create(authorized=False)
    unauth = client.get("/message_status", headers={"X-Session-Id": unauthorized.session_id})
    assert unauth.status_code == 401
    assert_error_envelope(unauth.json(), "AUTH_UNAUTHORIZED")

    expired = client.app.state.session_store.create(authorized=True)
    expired.expires_at = expired.created_at - 1
    gone = client.get("/message_status", headers={"X-Session-Id": expired.session_id})
    assert gone.status_code == 410
    assert_error_envelope(gone.json(), "SESSION_EXPIRED")


def test_message_status_returns_structured_state(client):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]

    PROCESS_CALLS["count"] = 0
    first = client.get("/message_status", headers={"X-Session-Id": sid})
    second = client.get("/message_status", headers={"X-Session-Id": sid})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] in {"queued", "processing", "ready", "failed"}
    assert second.json()["status"] in {"queued", "processing", "ready", "failed"}
    assert PROCESS_CALLS["count"] == 0


def test_next_message_contract_flow(client):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    status = client.get("/message_status", headers={"X-Session-Id": sid})
    assert status.status_code == 200

    next_message = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert next_message.status_code == 200
    payload = next_message.json()
    assert payload["status"] in {"ready", "failed"}
    assert "message" in payload
    assert "details" in payload

    missing = client.post("/next_message", headers={"X-Session-Id": "unknown"}, json={})
    assert missing.status_code == 404
    assert_error_envelope(missing.json(), "SESSION_NOT_FOUND")


def test_next_message_uses_inline_retrieval_pipeline(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен в Монако"

    monkeypatch.setattr("src.api.chat.resolve_entities", lambda _query: ("max verstappen monaco", ["driver:max_verstappen"], ["driver:max_verstappen"]))
    monkeypatch.setattr(
        "src.api.chat.retrieve_historical_context",
        lambda *_args, **_kwargs: [{"source_id": "f1db:race:2023-monaco", "snippet": "Verstappen won Monaco GP 2023", "score": 0.91}],
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "Историческая сводка" in payload["message"]
    assert payload["details"]["code"] == "OK"
    assert payload["details"]["evidence"]
    assert payload["details"]["evidence"][0]["used_in_answer"] is True
