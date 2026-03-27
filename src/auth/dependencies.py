from fastapi import Header, status

from src.auth.errors import AUTH_UNAUTHORIZED, SESSION_EXPIRED, SESSION_NOT_FOUND, api_error, unauthorized_error
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
    if session is None:
        raise api_error(
            code=SESSION_NOT_FOUND,
            message="Сессия не найдена.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"session_id": x_session_id},
        )
    if store.is_expired(session):
        raise api_error(
            code=SESSION_EXPIRED,
            message="Сессия истекла.",
            status_code=status.HTTP_410_GONE,
            details={"session_id": x_session_id},
        )
    if not session.authorized:
        raise unauthorized_error(AUTH_UNAUTHORIZED, "Сессия не авторизована.")
    return session
