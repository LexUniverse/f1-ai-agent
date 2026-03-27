from src.models.api_contracts import EvidenceItem, QnAConfidence, StructuredRUAnswer, AnswerSection

CONFIDENCE_HIGH_MIN = 0.65
CONFIDENCE_MEDIUM_MIN = 0.40


def tier_ru_from_max_score(max_score: float) -> str:
    if max_score >= CONFIDENCE_HIGH_MIN:
        return "высокая"
    if max_score >= CONFIDENCE_MEDIUM_MIN:
        return "средняя"
    return "низкая"


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + "…"


def build_structured_ru_answer(evidence: list[EvidenceItem]) -> StructuredRUAnswer:
    first = evidence[0].snippet if evidence else ""
    body = _truncate(first, 400)
    sections = [AnswerSection(heading="Сводка", body=body)]
    lines: list[str] = ["Источники:"]
    for n, item in enumerate(evidence, start=1):
        snip = _truncate(item.snippet, 80)
        lines.append(f"[{n}] {item.source_id} — {snip}")
    sources_block_ru = "\n".join(lines)
    return StructuredRUAnswer(
        sections=sections,
        sources_block_ru=sources_block_ru,
        citation_count=len(evidence),
    )


def qna_confidence_from_evidence(evidence: list[EvidenceItem]) -> QnAConfidence:
    if not evidence:
        return QnAConfidence(tier_ru=tier_ru_from_max_score(0.0), score=0.0)
    max_score = max(item.rank_score for item in evidence)
    return QnAConfidence(tier_ru=tier_ru_from_max_score(max_score), score=max_score)
