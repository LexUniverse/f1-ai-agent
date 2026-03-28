"""API-05 / WEB-01: `/next_message` details shape (no confidence; web when used)."""

import json

from src.api.chat import assemble_next_message_details
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer


def _sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            source_id="f1db:x",
            snippet="Фрагмент.",
            entity_tags=["driver:x"],
            rank_score=0.9,
        )
    ]


def test_rag_only_details_json_excludes_confidence() -> None:
    ev = _sample_evidence()
    structured = StructuredRUAnswer(
        sections=[AnswerSection(heading="Сводка", body="Текст.")],
        sources_block_ru="Источники:\n[1] f1db:x",
        citation_count=1,
    )
    details = assemble_next_message_details(
        normalized_query="q",
        canonical_entity_ids=["driver:x"],
        evidence=ev,
        out_details={
            "structured_answer": structured.model_dump(),
            "synthesis": {"route": "gigachat_rag"},
        },
        synthesis_route="gigachat_rag",
    )
    dumped = json.dumps(details, ensure_ascii=False)
    assert "confidence" not in dumped
    assert details["structured_answer"]["sections"]


def test_web_details_include_queries_and_results_shape() -> None:
    ev = _sample_evidence()
    structured = StructuredRUAnswer(
        sections=[AnswerSection(heading="Веб", body="Ответ.")],
        sources_block_ru="Источники:\n[1] https://ex",
        citation_count=1,
    )
    out = {
        "structured_answer": structured.model_dump(),
        "synthesis": {"route": "gigachat_web"},
        "tavily_queries": ["monaco f1 winner"],
        "web_results": [
            {"url": "https://example.com/a", "title": "T", "content": "Snippet text here."},
        ],
    }
    details = assemble_next_message_details(
        normalized_query="q",
        canonical_entity_ids=[],
        evidence=ev,
        out_details=out,
        synthesis_route="gigachat_web",
    )
    dumped = json.dumps(details, ensure_ascii=False)
    assert "confidence" not in dumped
    web = details.get("web")
    assert isinstance(web, dict)
    assert web["queries"] == ["monaco f1 winner"]
    assert len(web["results"]) == 1
    row = web["results"][0]
    assert row["url"] == "https://example.com/a"
    assert row["title"] == "T"
    assert "Snippet" in row["content_snippet"]


def test_assemble_happy_path_has_ok_and_structured_sections() -> None:
    ev = _sample_evidence()
    details = assemble_next_message_details(
        normalized_query="q",
        canonical_entity_ids=[],
        evidence=ev,
        out_details={
            "structured_answer": StructuredRUAnswer(
                sections=[AnswerSection(heading="Сводка", body="Non-empty body for SRCH-03 checks.")],
                sources_block_ru="Источники:",
                citation_count=1,
            ).model_dump(),
            "synthesis": {"route": "gigachat_rag"},
        },
        synthesis_route="gigachat_rag",
    )
    assert details.get("code") == "OK"
    assert details["structured_answer"]["sections"][0]["body"]
