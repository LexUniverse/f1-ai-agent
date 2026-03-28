from src.models.api_contracts import EvidenceItem

SNIPPET_MAX_LEN = 280


def format_evidence(hits: list[dict], entity_tags: list[str]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for hit in hits:
        raw_snip = str(hit.get("snippet", ""))
        full = str(hit.get("document_full", "") or raw_snip)
        evidence.append(
            EvidenceItem(
                source_id=str(hit.get("source_id", "")),
                snippet=raw_snip[:SNIPPET_MAX_LEN],
                context_for_llm=full,
                entity_tags=list(entity_tags),
                rank_score=float(hit.get("score", hit.get("rank_score", 0.0))),
            )
        )
    return evidence
