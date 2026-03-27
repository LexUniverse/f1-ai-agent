import json

from src.models.api_contracts import AnswerSection, EvidenceItem, QnAConfidence, StructuredRUAnswer

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


def summarize_live_next_payload_ru(payload: dict) -> str:
    parts: list[str] = []
    if "raceName" in payload:
        parts.append(str(payload["raceName"]))
    circuit = payload.get("Circuit") if isinstance(payload.get("Circuit"), dict) else None
    if circuit is None and isinstance(payload.get("circuit"), dict):
        circuit = payload["circuit"]
    if isinstance(circuit, dict):
        loc = circuit.get("Location") if isinstance(circuit.get("Location"), dict) else circuit.get("location")
        if isinstance(loc, dict) and loc.get("locality"):
            parts.append(str(loc["locality"]))
        elif circuit.get("circuitName"):
            parts.append(str(circuit["circuitName"]))
    if parts:
        return "Следующая гонка: " + ", ".join(parts)
    return json.dumps(payload, ensure_ascii=False)[:200] + "…"


def live_fresh_user_message_ru(*, as_of_utc_z: str, summary_ru: str) -> str:
    summary_part = _truncate(summary_ru, 160)
    return f"Актуально на {as_of_utc_z} — {summary_part}"


def build_live_structured_ru_answer(*, summary_ru: str, citation_label: str = "live:f1api.dev") -> StructuredRUAnswer:
    snip = _truncate(summary_ru, 80)
    sources_block_ru = f"Источники:\n[1] {citation_label} — {snip}"
    return StructuredRUAnswer(
        sections=[AnswerSection(heading="Актуальные данные", body=summary_ru)],
        sources_block_ru=sources_block_ru,
        citation_count=1,
    )


def live_qna_confidence() -> QnAConfidence:
    return QnAConfidence(tier_ru="средняя", score=0.55)
