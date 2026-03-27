import json

import httpx

from src.ui.f1_chat_http import get_message_status, post_next_message, start_chat_http


def test_start_chat_http_sends_access_code_and_question():
    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/start_chat"):
            body = json.loads(request.content.decode())
            captured.append(body)
            return httpx.Response(200, json={"session_id": "00000000-0000-4000-8000-000000000001"})
        return httpx.Response(404, text="unexpected")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as client:
        sid = start_chat_http(client, "http://test", "ABC123", "Who won Monaco?")

    assert sid == "00000000-0000-4000-8000-000000000001"
    assert captured == [{"access_code": "ABC123", "question": "Who won Monaco?"}]


def test_status_then_next_message_sequence():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/message_status"):
            calls.append("status")
            assert request.headers.get("x-session-id") == "sid-1"
            if len(calls) == 1:
                return httpx.Response(200, json={"status": "processing", "details": {}})
            return httpx.Response(200, json={"status": "ready", "details": {}})
        if path.endswith("/next_message"):
            calls.append("next")
            assert request.headers.get("x-session-id") == "sid-1"
            return httpx.Response(
                200,
                json={
                    "message": "Ответ",
                    "status": "ready",
                    "details": {"code": "OK"},
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as client:
        s1 = get_message_status(client, "http://test", "sid-1")
        assert s1["status"] == "processing"
        s2 = get_message_status(client, "http://test", "sid-1")
        assert s2["status"] == "ready"
        n = post_next_message(client, "http://test", "sid-1")

    assert n["message"] == "Ответ"
    assert calls == ["status", "status", "next"]
