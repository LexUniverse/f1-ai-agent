"""Authoritative clock from TimeAPI.io.

Success path: a single ``GET`` to
``https://timeapi.io/api/v1/time/current/unix`` (no second call to ``/utc``).
We intentionally avoid httpx transport retries here; one request per successful fetch.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import BaseModel, Field

TIMEAPI_BASE = "https://timeapi.io"
_TIME_UNIX_PATH = "/api/v1/time/current/unix"
_TIME_UNIX_URL = f"{TIMEAPI_BASE}{_TIME_UNIX_PATH}"


class TimeApiError(Exception):
    """TimeAPI fetch failed.

    Callers may show :func:`degraded_message_ru` (fixed Russian text) for any
    ``TimeApiError`` instead of exposing exception details to end users.

    Attributes:
        reason: ``timeout`` | ``http`` | ``network`` | ``parse``.
        detail: Optional diagnostic string.
    """

    def __init__(self, message: str, *, reason: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.detail = detail


class TimeApiNow(BaseModel):
    """Instant from TimeAPI ``unix`` endpoint."""

    unix_timestamp: int
    utc_naive: datetime = Field(
        ...,
        description="UTC as naive datetime (aligned with FastF1 Session*DateUtc).",
    )


def degraded_message_ru() -> str:
    """Return the fixed Russian degraded message for time service failures."""
    from src.integrations.messages_ru import TIMEAPI_UNAVAILABLE_MESSAGE_RU

    return TIMEAPI_UNAVAILABLE_MESSAGE_RU


def fetch_timeapi_now() -> TimeApiNow:
    """Fetch current unix time from TimeAPI; derive naive UTC from that instant."""
    timeout = float(os.environ.get("TIMEAPI_TIMEOUT", "10"))
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(_TIME_UNIX_URL)
            response.raise_for_status()
            data: Any = response.json()
    except httpx.TimeoutException as e:
        raise TimeApiError("TimeAPI request timed out", reason="timeout", detail=str(e)) from e
    except httpx.HTTPStatusError as e:
        raise TimeApiError(
            f"TimeAPI HTTP error: {e.response.status_code}",
            reason="http",
            detail=str(e),
        ) from e
    except httpx.RequestError as e:
        raise TimeApiError("TimeAPI network error", reason="network", detail=str(e)) from e
    except ValueError as e:
        raise TimeApiError("TimeAPI response was not valid JSON", reason="parse", detail=str(e)) from e

    if not isinstance(data, dict):
        raise TimeApiError("TimeAPI JSON must be an object", reason="parse")
    raw = data.get("unix_timestamp")
    if raw is None or isinstance(raw, bool):
        raise TimeApiError("TimeAPI JSON missing unix_timestamp", reason="parse")
    try:
        unix_timestamp = int(raw)
    except (TypeError, ValueError) as e:
        raise TimeApiError("unix_timestamp is not an integer", reason="parse", detail=str(e)) from e

    utc_naive = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).replace(tzinfo=None)
    return TimeApiNow(unix_timestamp=unix_timestamp, utc_naive=utc_naive)
