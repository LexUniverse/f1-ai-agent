from fastapi import APIRouter, Depends, Header, Request

from src.auth.dependencies import require_authorized_session
from src.auth.errors import AUTH_UNAUTHORIZED, unauthorized_error
from src.auth.service import AuthService
from src.answer.gigachat_rag import (
    GIGACHAT_FALLBACK_ROUTE,
    GIGACHAT_SUCCESS_ROUTE,
    append_fallback_disclosure_ru,
    gigachat_synthesize_historical,
    gigachat_synthesize_live,
)
from src.answer.russian_qna import (
    build_live_structured_ru_answer,
    build_structured_ru_answer,
    live_fresh_user_message_ru,
    live_qna_confidence,
    qna_confidence_from_evidence,
    summarize_live_next_payload_ru,
)
from src.integrations.f1api_client import LiveUpstreamError
from src.live.gate import requires_live_data
from src.live.messages_ru import LIVE_UNAVAILABLE_MESSAGE_RU
from src.models.api_contracts import LiveDetails, MessageStatusResponse, NextMessageResponse, StartChatRequest, StartChatResponse
from src.retrieval.alias_resolver import resolve_entities
from src.retrieval.evidence import format_evidence
from src.retrieval.retriever import retrieve_historical_context
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
def next_message(request: Request, _session=Depends(_session_dependency)):
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
        hits = retrieve_historical_context(
            normalized_query,
            canonical_entity_ids,
            top_k=5,
            min_score=0.35,
        )
        evidence = format_evidence(hits, entity_tags)
        for item in evidence:
            item.used_in_answer = True

        if evidence:
            details: dict = {
                "code": "OK",
                "normalized_query": normalized_query,
                "canonical_entity_ids": canonical_entity_ids,
                "evidence": [item.model_dump() for item in evidence],
            }
            try:
                result = gigachat_synthesize_historical(evidence=evidence, user_question=_session.next_message)
                message = result.message
                structured = result.structured_answer
                conf = result.confidence
                details["structured_answer"] = structured.model_dump()
                details["confidence"] = conf.model_dump()
                details["synthesis"] = {"route": GIGACHAT_SUCCESS_ROUTE}
            except Exception as exc:
                structured = build_structured_ru_answer(evidence)
                conf = qna_confidence_from_evidence(evidence)
                summary = evidence[0].snippet.strip()[:120]
                base_message = f"Историческая сводка: {summary}. Уверенность: {conf.tier_ru}."
                message = append_fallback_disclosure_ru(base_message)
                details["structured_answer"] = structured.model_dump()
                details["confidence"] = conf.model_dump()
                details["synthesis"] = {
                    "route": GIGACHAT_FALLBACK_ROUTE,
                    "gigachat_error_class": type(exc).__name__,
                }
            status = "ready"
        elif not requires_live_data(normalized_query=normalized_query, raw_user_text=_session.next_message):
            message = "Недостаточно исторических данных в базе f1db."
            status = "failed"
            details = {"code": "RETRIEVAL_NO_EVIDENCE", "evidence": []}
        else:
            try:
                live_payload, as_of = request.app.state.f1_api_client.fetch_current_next()
            except LiveUpstreamError:
                store.set_status(_session.session_id, "failed", "LIVE_UNAVAILABLE")
                return NextMessageResponse(
                    message=LIVE_UNAVAILABLE_MESSAGE_RU,
                    status="failed",
                    details={"code": "LIVE_UNAVAILABLE", "evidence": []},
                )
            summarized = summarize_live_next_payload_ru(live_payload)
            details = {
                "code": "OK",
                "normalized_query": normalized_query,
                "canonical_entity_ids": canonical_entity_ids,
                "evidence": [],
                "live": LiveDetails(as_of=as_of, provider="f1api.dev", endpoint_key="current_next").model_dump(),
            }
            try:
                result = gigachat_synthesize_live(
                    summary_ru=summarized,
                    user_question=_session.next_message,
                    as_of_utc_z=as_of,
                )
                message = result.message.strip() and result.message or live_fresh_user_message_ru(
                    as_of_utc_z=as_of, summary_ru=summarized
                )
                structured = result.structured_answer
                conf = result.confidence
                details["structured_answer"] = structured.model_dump()
                details["confidence"] = conf.model_dump()
                details["synthesis"] = {"route": GIGACHAT_SUCCESS_ROUTE}
            except Exception as exc:
                structured = build_live_structured_ru_answer(summary_ru=summarized)
                conf = live_qna_confidence()
                base_message = live_fresh_user_message_ru(as_of_utc_z=as_of, summary_ru=summarized)
                message = append_fallback_disclosure_ru(base_message)
                details["structured_answer"] = structured.model_dump()
                details["confidence"] = conf.model_dump()
                details["synthesis"] = {
                    "route": GIGACHAT_FALLBACK_ROUTE,
                    "gigachat_error_class": type(exc).__name__,
                }
            status = "ready"

        store.set_status(_session.session_id, status, details["code"] if status == "failed" else None)
        return NextMessageResponse(message=message, status=status, details=details)
    except Exception:
        store.set_status(_session.session_id, "failed", "RETRIEVAL_FAILED")
        return NextMessageResponse(message="", status="failed", details={"code": "RETRIEVAL_FAILED", "evidence": []})
