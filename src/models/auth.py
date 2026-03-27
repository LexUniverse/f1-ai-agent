from pydantic import BaseModel


class AuthErrorPayload(BaseModel):
    code: str
    message: str


class AuthDecision(BaseModel):
    ok: bool
    code: str | None = None
    message: str | None = None
    retry_after_seconds: int | None = None
