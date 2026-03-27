from fastapi import HTTPException, status

from src.models.auth import AuthErrorPayload

AUTH_INVALID_CODE = "AUTH_INVALID_CODE"
AUTH_MISSING_CODE = "AUTH_MISSING_CODE"
AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
AUTH_COOLDOWN = "AUTH_COOLDOWN"


def unauthorized_error(code: str, message: str, retry_after_seconds: int | None = None) -> HTTPException:
    payload = AuthErrorPayload(code=code, message=message).model_dump()
    if retry_after_seconds is not None:
        payload["retry_after_seconds"] = retry_after_seconds

    http_status = status.HTTP_429_TOO_MANY_REQUESTS if code == AUTH_COOLDOWN else status.HTTP_401_UNAUTHORIZED
    return HTTPException(status_code=http_status, detail=payload)
