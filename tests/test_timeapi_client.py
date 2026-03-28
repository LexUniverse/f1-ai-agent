"""Unit tests for TimeAPI client (mocked httpx)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
import pytest

from src.integrations.messages_ru import TIMEAPI_UNAVAILABLE_MESSAGE_RU
from src.integrations.timeapi_client import (
    TimeApiError,
    TimeApiNow,
    degraded_message_ru,
    fetch_timeapi_now,
)


class _PatchedClient(httpx.Client):
    """Inject MockTransport while preserving timeout argument from production code."""

    def __init__(self, *args: object, transport: httpx.MockTransport, **kwargs: object) -> None:
        kwargs["transport"] = transport
        super().__init__(*args, **kwargs)


def test_fetch_success_parses_unix_and_utc_naive(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"unix_timestamp": 1700000000})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "src.integrations.timeapi_client.httpx.Client",
        lambda *a, **k: _PatchedClient(transport=transport, *a, **k),
    )

    got = fetch_timeapi_now()
    assert isinstance(got, TimeApiNow)
    assert got.unix_timestamp == 1700000000
    assert got.utc_naive == datetime.fromtimestamp(1700000000, tz=timezone.utc).replace(tzinfo=None)
    assert len(calls) == 1
    assert "time/current/unix" in calls[0]


def test_single_http_call_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        count["n"] += 1
        return httpx.Response(200, json={"unix_timestamp": 1})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "src.integrations.timeapi_client.httpx.Client",
        lambda *a, **k: _PatchedClient(transport=transport, *a, **k),
    )

    fetch_timeapi_now()
    assert count["n"] == 1


def test_timeout_maps_to_timeapi_error(monkeypatch: pytest.MonkeyPatch) -> None:
    req = httpx.Request("GET", "https://timeapi.io/api/v1/time/current/unix")

    def boom(*_a: object, **_k: object) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=req)

    monkeypatch.setattr("src.integrations.timeapi_client.httpx.Client.get", boom)

    with pytest.raises(TimeApiError) as ei:
        fetch_timeapi_now()
    assert ei.value.reason == "timeout"
    assert degraded_message_ru() == TIMEAPI_UNAVAILABLE_MESSAGE_RU


def test_http_error_maps_to_timeapi_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="no")

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "src.integrations.timeapi_client.httpx.Client",
        lambda *a, **k: _PatchedClient(transport=transport, *a, **k),
    )

    with pytest.raises(TimeApiError) as ei:
        fetch_timeapi_now()
    assert ei.value.reason == "http"


def test_parse_error_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(lambda _r: httpx.Response(200, json={}))
    monkeypatch.setattr(
        "src.integrations.timeapi_client.httpx.Client",
        lambda *a, **k: _PatchedClient(transport=transport, *a, **k),
    )

    with pytest.raises(TimeApiError) as ei:
        fetch_timeapi_now()
    assert ei.value.reason == "parse"


def test_parse_error_invalid_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(200, content=b"not-json", headers={"Content-Type": "application/json"})
    )
    monkeypatch.setattr(
        "src.integrations.timeapi_client.httpx.Client",
        lambda *a, **k: _PatchedClient(transport=transport, *a, **k),
    )

    with pytest.raises(TimeApiError) as ei:
        fetch_timeapi_now()
    assert ei.value.reason == "parse"


@pytest.mark.timeapi_live
@pytest.mark.skipif(os.environ.get("RUN_TIMEAPI_SMOKE") != "1", reason="set RUN_TIMEAPI_SMOKE=1 for live call")
def test_live_timeapi_smoke() -> None:
    """Optional: one real GET to TimeAPI (opt-in via RUN_TIMEAPI_SMOKE=1)."""
    out = fetch_timeapi_now()
    assert out.unix_timestamp > 1_000_000_000
