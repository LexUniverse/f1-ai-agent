from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

MAX_FAILURES = 5
WINDOW_SECONDS = 300
COOLDOWN_SECONDS = 600


@dataclass
class CooldownState:
    locked: bool
    retry_after_seconds: int = 0


class AuthLimiter:
    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: int = WINDOW_SECONDS,
        cooldown_seconds: int = COOLDOWN_SECONDS,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._locked_until: dict[str, float] = {}

    def _now(self) -> float:
        return monotonic()

    def _cleanup(self, key: str) -> None:
        now = self._now()
        events = self._events[key]
        while events and (now - events[0]) > self.window_seconds:
            events.popleft()

    def get_cooldown_state(self, key: str) -> CooldownState:
        now = self._now()
        until = self._locked_until.get(key)
        if until is None or now >= until:
            if until is not None:
                del self._locked_until[key]
            return CooldownState(locked=False)
        return CooldownState(locked=True, retry_after_seconds=max(1, int(until - now)))

    def record_failure(self, key: str) -> CooldownState:
        self._cleanup(key)
        now = self._now()
        events = self._events[key]
        events.append(now)
        if len(events) >= self.max_failures:
            self._locked_until[key] = now + self.cooldown_seconds
            events.clear()
            return CooldownState(locked=True, retry_after_seconds=self.cooldown_seconds)
        return CooldownState(locked=False)

    def reset(self, key: str) -> None:
        self._events.pop(key, None)
        self._locked_until.pop(key, None)
