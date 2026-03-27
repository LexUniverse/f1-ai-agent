import logging

from src.auth.allowlist import parse_allowlist
from src.auth.limiter import COOLDOWN_SECONDS, MAX_FAILURES
from src.auth.service import AuthService
from src.api.chat import PROCESS_CALLS
from conftest import assert_error_envelope


def test_allowlist_parsing_and_validation(monkeypatch):
    monkeypatch.setenv("AUTH_ALLOWLIST_CODES", " CODE1 ,CODE2")
    assert parse_allowlist() == ["CODE1", "CODE2"]

    service = AuthService()
    ok = service.validate_access_code("CODE1", limiter_key="ip:test")
    assert ok.ok is True

    bad = service.validate_access_code("NOPE", limiter_key="ip:test")
    assert bad.ok is False
    assert bad.code == "AUTH_INVALID_CODE"


def test_cooldown_and_masked_logging(caplog):
    caplog.set_level(logging.WARNING)
    service = AuthService()

    for _ in range(MAX_FAILURES):
        decision = service.validate_access_code("WRONGCODE", limiter_key="ip:lock")

    assert decision.ok is False
    cooldown = service.validate_access_code("ABC123", limiter_key="ip:lock")
    assert cooldown.code == "AUTH_COOLDOWN"
    assert 1 <= (cooldown.retry_after_seconds or 0) <= COOLDOWN_SECONDS

    joined = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "WRONGCODE" not in joined
    assert "***" in joined


def test_start_chat_valid_code_authorizes(client):
    response = client.post("/start_chat", json={"access_code": "ABC123"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    guarded = client.get("/message_status", headers={"X-Session-Id": session_id})
    assert guarded.status_code == 200


def test_start_chat_invalid_code_rejected(client):
    response = client.post("/start_chat", json={"access_code": "BAD"})
    assert response.status_code == 401
    body = response.json()
    assert_error_envelope(body, "AUTH_INVALID_CODE")
    assert "Неверный код" in body["error"]["message"]


def test_start_chat_authorization_flow(client):
    missing = client.post("/start_chat", json={})
    assert missing.status_code == 401
    assert_error_envelope(missing.json(), "AUTH_MISSING_CODE")

    valid = client.post("/start_chat", json={"access_code": "XYZ789"})
    assert valid.status_code == 200
    sid = valid.json()["session_id"]
    status = client.get("/message_status", headers={"X-Session-Id": sid})
    assert status.status_code == 200


def test_unauthorized_blocked_before_processing(client):
    PROCESS_CALLS["count"] = 0
    response = client.get("/message_status", headers={"X-Session-Id": "missing-session"})
    assert response.status_code == 404
    assert_error_envelope(response.json(), "SESSION_NOT_FOUND")
    assert PROCESS_CALLS["count"] == 0


def test_unauthorized_blocked_before_chat_pipeline(client):
    PROCESS_CALLS["count"] = 0
    response = client.post("/next_message", headers={"X-Session-Id": "bad"}, json={})
    assert response.status_code == 404
    assert PROCESS_CALLS["count"] == 0
