from src.models.api_contracts import EvidenceItem

SNIPPET_MAX_LEN = 280


def format_evidence(hits: list[dict], entity_tags: list[str]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for hit in hits:
        evidence.append(
            EvidenceItem(
                source_id=str(hit.get("source_id", "")),
                snippet=str(hit.get("snippet", ""))[:SNIPPET_MAX_LEN],
                entity_tags=list(entity_tags),
                rank_score=float(hit.get("score", hit.get("rank_score", 0.0))),
            )
        )
    return evidence
