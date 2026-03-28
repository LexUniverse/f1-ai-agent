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


class WebSearchResultItem(BaseModel):
    """One row shown in API `details.web.results` after a web-augmented turn."""

    url: str
    title: str | None = None
    content_snippet: str


class WebSearchDetails(BaseModel):
    """Shape of `details.web` in JSON responses (from `model_dump()` in the chat layer)."""

    queries: list[str]
    results: list[WebSearchResultItem]


class EvidenceItem(BaseModel):
    source_id: str
    snippet: str
    entity_tags: list[str]
    rank_score: float
    used_in_answer: bool = False
    # Full chunk text for LLM synthesis (excluded from API JSON — snippets stay short for UI).
    context_for_llm: str = Field(default="", exclude=True)


class RetrievalArtifacts(BaseModel):
    normalized_query: str
    canonical_entity_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class LiveDetails(BaseModel):
    as_of: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T.*Z$")
    provider: Literal["f1api.dev"] = "f1api.dev"
    endpoint_key: str | None = None


class ProvenanceRag(BaseModel):
    """RAG slice of `details[\"provenance\"]` (Phase 12 WEB-02 / Phase 13 UI)."""

    normalized_query: str
    evidence: list[dict] = Field(default_factory=list)


class ProvenanceWebFetch(BaseModel):
    """Optional single-page fetch metadata after Tavily (same URL as planning step)."""

    url: str
    ok: bool
    error: str | None = None
    excerpt_preview: str | None = None


class ProvenanceWeb(BaseModel):
    """Web slice: mirrors graph `web_results` rows; `fetch` only if HTTP fetch ran."""

    queries: list[str] = Field(default_factory=list)
    results: list[dict] = Field(default_factory=list)
    fetch: ProvenanceWebFetch | None = None


class ProvenanceSnapshot(BaseModel):
    """Unified provenance for `/next_message` `details[\"provenance\"]` — Streamlit Phase 13 reads this first."""

    rag: ProvenanceRag
    web: ProvenanceWeb | None = None
    synthesis: dict = Field(default_factory=dict)
