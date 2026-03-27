from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import httpx


class LiveUpstreamError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def as_of_utc_z_from_completion(when: datetime | None = None) -> str:
    dt = when if when is not None else datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    iso = dt.isoformat()
    if iso.endswith("+00:00"):
        return iso.replace("+00:00", "Z")
    if iso.endswith("Z"):
        return iso
    return iso + "Z" if "+" not in iso and "-" not in iso[-6:] else iso.replace("+00:00", "Z")


class _CircuitBreaker:
    def __init__(self, fail_max: int, cool_seconds: float) -> None:
        self.fail_max = fail_max
        self.cool_seconds = cool_seconds
        self._consecutive = 0
        self._open_until: float | None = None

    def before_request(self) -> None:
        if self._open_until is not None:
            if time.monotonic() >= self._open_until:
                self._open_until = None
                self._consecutive = 0
            else:
                raise LiveUpstreamError("circuit_open")

    def record_success(self) -> None:
        self._consecutive = 0
        self._open_until = None

    def record_failure(self) -> None:
        self._consecutive += 1
        if self._consecutive >= self.fail_max:
            self._open_until = time.monotonic() + self.cool_seconds
            self._consecutive = 0


class F1ApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        breaker_fail_max: int,
        breaker_cool_seconds: float,
        http_retry_max: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._http_retry_max = http_retry_max
        self._breaker = _CircuitBreaker(breaker_fail_max, float(breaker_cool_seconds))
        t = transport if transport is not None else httpx.HTTPTransport(retries=1)
        self._client = httpx.Client(base_url=base_url.rstrip("/") + "/", timeout=self._timeout, transport=t)

    def close(self) -> None:
        self._client.close()

    @classmethod
    def from_env(cls) -> F1ApiClient:
        base = os.environ.get("F1API_BASE_URL", "https://f1api.dev")
        timeout = float(os.environ.get("F1API_TIMEOUT_SECONDS", "10"))
        fail_max = int(os.environ.get("F1API_BREAKER_FAIL_MAX", "5"))
        cool = float(os.environ.get("F1API_BREAKER_COOL_SECONDS", "30"))
        retries = int(os.environ.get("F1API_HTTP_RETRY_MAX", "2"))
        return cls(
            base_url=base,
            timeout_seconds=timeout,
            breaker_fail_max=fail_max,
            breaker_cool_seconds=cool,
            http_retry_max=retries,
        )

    def fetch_current_next(self) -> tuple[dict, str]:
        self._breaker.before_request()
        attempts = self._http_retry_max + 1
        for attempt in range(attempts):
            try:
                response = self._client.get("api/current/next")
                response.raise_for_status()
                raw = response.json()
                data = raw if isinstance(raw, dict) else {"value": raw}
                as_of = as_of_utc_z_from_completion()
                self._breaker.record_success()
                return data, as_of
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                if code == 404 or (400 <= code < 500):
                    err = LiveUpstreamError(f"http_{code}", status_code=code)
                    self._breaker.record_failure()
                    raise err from e
                if code >= 500:
                    if attempt + 1 < attempts:
                        continue
                    err = LiveUpstreamError(f"http_{code}", status_code=code)
                    self._breaker.record_failure()
                    raise err from e
            except httpx.ReadTimeout:
                if attempt + 1 < attempts:
                    continue
                self._breaker.record_failure()
                raise LiveUpstreamError("read_timeout") from None
            except httpx.RequestError as e:
                self._breaker.record_failure()
                raise LiveUpstreamError("transport_error") from e
        self._breaker.record_failure()
        raise LiveUpstreamError("exhausted_retries")
