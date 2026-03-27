from dataclasses import dataclass, field
from time import time
from uuid import uuid4

DEFAULT_SESSION_TTL_SECONDS = 1800


@dataclass
class Session:
    session_id: str
    authorized: bool = False
    status: str = "queued"
    next_message: str = "response"
    failure_code: str | None = None
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    expires_at: float = 0


class SessionStore:
    def __init__(self, ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS) -> None:
        self._sessions: dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds

    def create(self, authorized: bool) -> Session:
        now = time()
        session = Session(
            session_id=str(uuid4()),
            authorized=authorized,
            status="ready",
            created_at=now,
            updated_at=now,
            expires_at=now + self.ttl_seconds,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def mark_authorized(self, session_id: str) -> Session | None:
        session = self.get(session_id)
        if session:
            session.authorized = True
            session.updated_at = time()
        return session

    def is_expired(self, session: Session) -> bool:
        return time() >= session.expires_at

    def set_status(self, session_id: str, status: str, failure_code: str | None = None) -> Session | None:
        session = self.get(session_id)
        if session:
            session.status = status
            session.failure_code = failure_code
            session.updated_at = time()
        return session

    def invalidate(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
