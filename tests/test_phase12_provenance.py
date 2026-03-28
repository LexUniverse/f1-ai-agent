"""Phase 12 WEB-02: provenance passes through assemble_next_message_details."""

import json

from src.api.chat import assemble_next_message_details
from src.models.api_contracts import AnswerSection, EvidenceItem, StructuredRUAnswer


def test_assemble_details_includes_provenance_without_confidence() -> None:
    ev = [
        EvidenceItem(
            source_id="f1db:x",
            snippet="Фрагмент.",
            entity_tags=["t"],
            rank_score=0.9,
        )
    ]
    structured = StructuredRUAnswer(
        sections=[AnswerSection(heading="Веб", body="Ответ.")],
        sources_block_ru="Источники:\n[1] https://ex",
        citation_count=1,
    )
    out_details = {
        "structured_answer": structured.model_dump(),
        "synthesis": {"route": "gigachat_web"},
        "tavily_queries": ["q1"],
        "web_results": [{"url": "https://a", "title": "T", "content": "c"}],
        "provenance": {
            "rag": {"normalized_query": "nq", "evidence": [{"source_id": "f1db:x", "snippet": "s", "entity_tags": []}]},
            "web": {
                "queries": ["q1"],
                "results": [{"url": "https://a", "title": "T", "content": "c"}],
                "fetch": {"url": "https://a", "ok": True, "error": None, "excerpt_preview": "prev"},
            },
            "synthesis": {"route": "gigachat_web"},
        },
    }
    details = assemble_next_message_details(
        normalized_query="nq",
        canonical_entity_ids=[],
        evidence=ev,
        out_details=out_details,
        synthesis_route="gigachat_web",
    )
    dumped = json.dumps(details, ensure_ascii=False)
    assert "provenance" in dumped
    assert "confidence" not in dumped
    assert details["provenance"]["rag"]["normalized_query"] == "nq"
    assert details["provenance"]["web"]["queries"] == ["q1"]
