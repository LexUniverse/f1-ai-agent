from fastapi import Header

from src.auth.errors import AUTH_UNAUTHORIZED, unauthorized_error
from src.sessions.store import Session, SessionStore


def require_authorized_session(
    x_session_id: str | None = Header(default=None),
    store: SessionStore | None = None,
) -> Session:
    if x_session_id is None:
        raise unauthorized_error(AUTH_UNAUTHORIZED, "Сессия не авторизована.")
    if store is None:
        raise unauthorized_error(AUTH_UNAUTHORIZED, "Сессия не авторизована.")
    session = store.get(x_session_id)
    if session is None or not session.authorized:
        raise unauthorized_error(AUTH_UNAUTHORIZED, "Сессия не авторизована.")
    return session
