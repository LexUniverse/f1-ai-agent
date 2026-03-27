import asyncio

from fastapi import APIRouter, Depends, Header, Request

from src.auth.dependencies import require_authorized_session
from src.auth.errors import AUTH_UNAUTHORIZED, unauthorized_error
from src.auth.service import AuthService
from src.graph.f1_turn_graph import F1TurnState, run_f1_turn_sync
from src.models.api_contracts import (
    MessageStatusResponse,
    NextMessageResponse,
    StartChatRequest,
    StartChatResponse,
)
from src.retrieval.alias_resolver import resolve_entities
from src.search.messages_ru import WEB_SEARCH_UNAVAILABLE_MESSAGE_RU
from src.sessions.store import SessionStore

router = APIRouter()

PROCESS_CALLS = {"count": 0}


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
    if payload.question is not None:
        stripped = payload.question.strip()
        if stripped:
            session.next_message = stripped
    return StartChatResponse(session_id=session.session_id)


@router.get("/message_status", response_model=MessageStatusResponse)
def message_status(_session=Depends(_session_dependency)):
    details = {}
    if _session.status == "failed" and _session.failure_code:
        details = {"code": _session.failure_code}
    return MessageStatusResponse(status=_session.status, details=details)


@router.post("/next_message", response_model=NextMessageResponse)
async def next_message(request: Request, _session=Depends(_session_dependency)):
    store: SessionStore = request.app.state.session_store
    process_chat_message()
    if _session.status == "failed":
        return NextMessageResponse(
            message="",
            status="failed",
            details={"code": _session.failure_code or "MESSAGE_FAILED", "evidence": []},
        )

    try:
        normalized_query, canonical_entity_ids, entity_tags = resolve_entities(_session.next_message)
        initial: F1TurnState = {
            "user_question": _session.next_message,
            "normalized_query": normalized_query,
            "canonical_entity_ids": canonical_entity_ids,
            "entity_tags": entity_tags,
        }
        final = await asyncio.to_thread(run_f1_turn_sync, initial)

        if final.get("terminal_status") == "failed" and final.get("error_code") == "WEB_SEARCH_UNAVAILABLE":
            store.set_status(_session.session_id, "failed", "WEB_SEARCH_UNAVAILABLE")
            return NextMessageResponse(
                message=WEB_SEARCH_UNAVAILABLE_MESSAGE_RU,
                status="failed",
                details={"code": "WEB_SEARCH_UNAVAILABLE", "evidence": []},
            )

        evidence = final.get("evidence") or []
        for item in evidence:
            item.used_in_answer = True

        out_details = final.get("out_details") or {}
        structured = out_details.get("structured_answer")
        confidence = out_details.get("confidence")
        synthesis_raw = out_details.get("synthesis")
        route = ""
        if isinstance(synthesis_raw, dict) and synthesis_raw.get("route"):
            route = str(synthesis_raw["route"])
        if not route:
            route = str(final.get("synthesis_route") or "")

        synthesis_out: dict = dict(synthesis_raw) if isinstance(synthesis_raw, dict) else {}
        if route and "route" not in synthesis_out:
            synthesis_out["route"] = route

        details: dict = {
            "code": "OK",
            "normalized_query": normalized_query,
            "canonical_entity_ids": canonical_entity_ids,
            "evidence": [item.model_dump() for item in evidence],
            "synthesis": synthesis_out,
        }
        if isinstance(structured, dict):
            details["structured_answer"] = structured
        if isinstance(confidence, dict):
            details["confidence"] = confidence

        store.set_status(_session.session_id, "ready", None)
        return NextMessageResponse(
            message=final.get("out_message") or "",
            status="ready",
            details=details,
        )
    except Exception:
        store.set_status(_session.session_id, "failed", "RETRIEVAL_FAILED")
        return NextMessageResponse(message="", status="failed", details={"code": "RETRIEVAL_FAILED", "evidence": []})
