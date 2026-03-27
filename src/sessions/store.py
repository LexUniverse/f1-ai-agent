from dataclasses import dataclass, field
from time import time
from uuid import uuid4


@dataclass
class Session:
    session_id: str
    authorized: bool = False
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, authorized: bool) -> Session:
        session = Session(session_id=str(uuid4()), authorized=authorized)
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

    def invalidate(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
