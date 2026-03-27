from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.chat import router as chat_router
from src.auth.service import AuthService
from src.integrations.f1api_client import F1ApiClient
from src.models.api_contracts import ErrorEnvelope, ErrorEnvelopeBody
from src.sessions.store import SessionStore

app = FastAPI(title="F1 Assistant API")
app.state.session_store = SessionStore()
app.state.auth_service = AuthService()
app.state.f1_api_client = F1ApiClient.from_env()
app.include_router(chat_router)


def _normalize_http_exception(exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    code = detail.get("code", "HTTP_ERROR")
    message = detail.get("message", "Request failed.")
    details = detail.get("details", {})
    if "retry_after_seconds" in detail:
        details["retry_after_seconds"] = detail["retry_after_seconds"]
    envelope = ErrorEnvelope(error=ErrorEnvelopeBody(code=code, message=message, details=details))
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return _normalize_http_exception(exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    envelope = ErrorEnvelope(
        error=ErrorEnvelopeBody(
            code="VALIDATION_ERROR",
            message="Некорректный запрос.",
            details={"errors": exc.errors()},
        )
    )
    return JSONResponse(status_code=422, content=envelope.model_dump())
