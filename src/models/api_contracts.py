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
    question: str | None = None


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


class QnAConfidence(BaseModel):
    tier_ru: str
    score: float


class AnswerSection(BaseModel):
    heading: str
    body: str


class StructuredRUAnswer(BaseModel):
    sections: list[AnswerSection]
    sources_block_ru: str
    citation_count: int


class EvidenceItem(BaseModel):
    source_id: str
    snippet: str
    entity_tags: list[str]
    rank_score: float
    used_in_answer: bool = False


class RetrievalArtifacts(BaseModel):
    normalized_query: str
    canonical_entity_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class LiveDetails(BaseModel):
    as_of: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T.*Z$")
    provider: Literal["f1api.dev"] = "f1api.dev"
    endpoint_key: str | None = None
