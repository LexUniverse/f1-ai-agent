from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from src.auth.dependencies import require_authorized_session
from src.auth.errors import AUTH_UNAUTHORIZED, unauthorized_error
from src.auth.service import AuthService
from src.sessions.store import SessionStore

router = APIRouter()

PROCESS_CALLS = {"count": 0}


class StartChatRequest(BaseModel):
    access_code: str | None = None


class StartChatResponse(BaseModel):
    session_id: str


class MessageStatusResponse(BaseModel):
    status: str


class NextMessageResponse(BaseModel):
    message: str


def process_chat_message() -> str:
    PROCESS_CALLS["count"] += 1
    return "ok"


def _session_dependency(request: Request, x_session_id: str | None = Header(default=None)):
    store: SessionStore = request.app.state.session_store
    return require_authorized_session(x_session_id=x_session_id, store=store)


@router.post("/start_chat", response_model=StartChatResponse)
def start_chat(payload: StartChatRequest, request: Request):
    auth_service: AuthService = request.app.state.auth_service
    session_store: SessionStore = request.app.state.session_store
    client_host = (request.client.host if request.client else "unknown")
    limiter_key = f"ip:{client_host}"
    decision = auth_service.validate_access_code(payload.access_code, limiter_key=limiter_key)
    if not decision.ok:
        raise unauthorized_error(decision.code or AUTH_UNAUTHORIZED, decision.message or "Не авторизован.", decision.retry_after_seconds)

    session = session_store.create(authorized=True)
    return StartChatResponse(session_id=session.session_id)


@router.get("/message_status", response_model=MessageStatusResponse)
def message_status(_session=Depends(_session_dependency)):
    process_chat_message()
    return MessageStatusResponse(status="ready")


@router.post("/next_message", response_model=NextMessageResponse)
def next_message(_session=Depends(_session_dependency)):
    process_chat_message()
    return NextMessageResponse(message="response")
