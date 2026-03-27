from fastapi import HTTPException, status

from src.models.auth import AuthErrorPayload

AUTH_INVALID_CODE = "AUTH_INVALID_CODE"
AUTH_MISSING_CODE = "AUTH_MISSING_CODE"
AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
AUTH_COOLDOWN = "AUTH_COOLDOWN"
SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
SESSION_EXPIRED = "SESSION_EXPIRED"


def api_error(
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
    retry_after_seconds: int | None = None,
) -> HTTPException:
    payload = AuthErrorPayload(code=code, message=message).model_dump()
    if details:
        payload["details"] = details
    if retry_after_seconds is not None:
        payload["retry_after_seconds"] = retry_after_seconds

    return HTTPException(status_code=status_code, detail=payload)


def unauthorized_error(code: str, message: str, retry_after_seconds: int | None = None) -> HTTPException:
    http_status = status.HTTP_429_TOO_MANY_REQUESTS if code == AUTH_COOLDOWN else status.HTTP_401_UNAUTHORIZED
    return api_error(code=code, message=message, status_code=http_status, retry_after_seconds=retry_after_seconds)
