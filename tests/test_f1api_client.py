import httpx
import pytest

from src.integrations.f1api_client import F1ApiClient, LiveUpstreamError, as_of_utc_z_from_completion


def test_as_of_utc_z_ends_with_z():
    s = as_of_utc_z_from_completion()
    assert s.endswith("Z")
    assert "T" in s


def test_fetch_current_next_success_json_and_as_of():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/api/current/next")
        return httpx.Response(200, json={"raceName": "Test GP"})

    transport = httpx.MockTransport(handler)
    client = F1ApiClient(
        base_url="https://f1api.dev",
        timeout_seconds=10.0,
        breaker_fail_max=5,
        breaker_cool_seconds=30.0,
        http_retry_max=2,
        transport=transport,
    )
    try:
        data, as_of = client.fetch_current_next()
        assert data == {"raceName": "Test GP"}
        assert as_of.endswith("Z")
    finally:
        client.close()


def test_fetch_current_next_retries_503_then_success():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = F1ApiClient(
        base_url="https://f1api.dev",
        timeout_seconds=10.0,
        breaker_fail_max=5,
        breaker_cool_seconds=30.0,
        http_retry_max=2,
        transport=transport,
    )
    try:
        data, _as_of = client.fetch_current_next()
        assert data == {"ok": True}
        assert calls["n"] == 2
    finally:
        client.close()


def test_circuit_opens_after_consecutive_failures():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = F1ApiClient(
        base_url="https://f1api.dev",
        timeout_seconds=10.0,
        breaker_fail_max=2,
        breaker_cool_seconds=30.0,
        http_retry_max=0,
        transport=transport,
    )
    try:
        with pytest.raises(LiveUpstreamError) as e1:
            client.fetch_current_next()
        assert e1.value.status_code == 404

        with pytest.raises(LiveUpstreamError) as e2:
            client.fetch_current_next()
        assert e2.value.status_code == 404

        with pytest.raises(LiveUpstreamError) as e3:
            client.fetch_current_next()
        assert "circuit" in str(e3.value).lower()
    finally:
        client.close()
