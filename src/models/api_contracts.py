from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorEnvelopeBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorEnvelopeBody


class StartChatRequest(BaseModel):
    access_code: str | None = None


class StartChatResponse(BaseModel):
    session_id: UUID


MessageStatusType = Literal["queued", "processing", "ready", "failed"]


class MessageStatusResponse(BaseModel):
    status: MessageStatusType
    details: dict = Field(default_factory=dict)


class NextMessageResponse(BaseModel):
    message: str
    status: Literal["ready", "failed"]
    details: dict = Field(default_factory=dict)
