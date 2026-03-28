import asyncio
import logging

from fastapi import APIRouter, Depends, Header, Request

from src.auth.dependencies import require_authorized_session
from src.auth.errors import AUTH_UNAUTHORIZED, unauthorized_error
from src.auth.service import AuthService
from src.graph.f1_turn_graph import F1TurnState, run_f1_turn_sync
from pydantic import ValidationError

from src.models.api_contracts import (
    EvidenceItem,
    MessageStatusResponse,
    NextMessageResponse,
    ProvenanceSnapshot,
    StartChatRequest,
    StartChatResponse,
    WebSearchDetails,
    WebSearchResultItem,
)
from src.retrieval.query_normalize import normalize_retrieval_query
from src.search.messages_ru import WEB_SEARCH_UNAVAILABLE_MESSAGE_RU
from src.sessions.store import SessionStore

router = APIRouter()

PROCESS_CALLS = {"count": 0}

logger = logging.getLogger(__name__)


def _coerce_evidence_list(raw: list | None) -> list[EvidenceItem]:
    """LangGraph возвращает evidence как list[dict] после сериализации — приводим к EvidenceItem."""
    if not raw:
        return []
    out: list[EvidenceItem] = []
    for item in raw:
        if isinstance(item, EvidenceItem):
            ev = item.model_copy(deep=True)
        elif isinstance(item, dict):
            try:
                ev = EvidenceItem.model_validate(item)
            except Exception:
                logger.warning("skip invalid evidence row: %s", item)
                continue
        else:
            logger.warning("skip evidence item of type %s", type(item).__name__)
            continue
        ev.used_in_answer = True
        out.append(ev)
    return out


def process_chat_message() -> str:
    PROCESS_CALLS["count"] += 1
    return "ok"


def assemble_next_message_details(
    *,
    normalized_query: str,
    canonical_entity_ids: list[str],
    evidence: list[EvidenceItem],
    out_details: dict,
    synthesis_route: str,
) -> dict:
    """Build the `details` dict for a successful `/next_message` response (tested in phase 9)."""
    synthesis_raw = out_details.get("synthesis")
    synthesis_out: dict = dict(synthesis_raw) if isinstance(synthesis_raw, dict) else {}
    if synthesis_route and "route" not in synthesis_out:
        synthesis_out["route"] = synthesis_route

    details: dict = {
        "code": "OK",
        "normalized_query": normalized_query,
        "canonical_entity_ids": canonical_entity_ids,
        "evidence": [item.model_dump() for item in evidence],
        "synthesis": synthesis_out,
    }
    structured = out_details.get("structured_answer")
    if isinstance(structured, dict):
        details["structured_answer"] = structured

    tq = out_details.get("tavily_queries")
    wr = out_details.get("web_results")
    if isinstance(tq, list) and isinstance(wr, list) and (tq or wr):
        items: list[WebSearchResultItem] = []
        for row in wr:
            if not isinstance(row, dict):
                continue
            content = str(row.get("content", ""))
            snippet = content[:500] + ("…" if len(content) > 500 else "")
            title_raw = row.get("title")
            items.append(
                WebSearchResultItem(
                    url=str(row.get("url", "")),
                    title=str(title_raw) if title_raw is not None else None,
                    content_snippet=snippet,
                )
            )
        web = WebSearchDetails(queries=[str(x) for x in tq], results=items)
        details["web"] = web.model_dump()

    raw_prov = out_details.get("provenance")
    if isinstance(raw_prov, dict):
        try:
            details["provenance"] = ProvenanceSnapshot.model_validate(raw_prov).model_dump()
        except ValidationError:
            details["provenance"] = raw_prov
    return details


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
        normalized_query, canonical_entity_ids, entity_tags = normalize_retrieval_query(_session.next_message)
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

        evidence = _coerce_evidence_list(final.get("evidence"))

        out_details = final.get("out_details") or {}
        synthesis_raw = out_details.get("synthesis")
        route = ""
        if isinstance(synthesis_raw, dict) and synthesis_raw.get("route"):
            route = str(synthesis_raw["route"])
        if not route:
            route = str(final.get("synthesis_route") or "")

        details = assemble_next_message_details(
            normalized_query=normalized_query,
            canonical_entity_ids=canonical_entity_ids,
            evidence=evidence,
            out_details=out_details,
            synthesis_route=route,
        )

        store.set_status(_session.session_id, "ready", None)
        out_msg = (final.get("out_message") or "").strip()
        if not out_msg:
            logger.warning(
                "empty out_message after graph session=%s route=%s evidence_count=%s",
                _session.session_id,
                route,
                len(evidence),
            )
            out_msg = (
                "Ответ не сформирован (пустая строка). См. логи сервера или проверьте GIGACHAT_CREDENTIALS."
            )

        return NextMessageResponse(
            message=out_msg,
            status="ready",
            details=details,
        )
    except Exception:
        logger.exception("next_message failed session_id=%s", getattr(_session, "session_id", "?"))
        store.set_status(_session.session_id, "failed", "RETRIEVAL_FAILED")
        return NextMessageResponse(
            message="Ошибка при обработке запроса (RETRIEVAL_FAILED). Подробности в логах API.",
            status="failed",
            details={"code": "RETRIEVAL_FAILED", "evidence": []},
        )
