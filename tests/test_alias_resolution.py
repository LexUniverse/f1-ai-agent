from src.models.api_contracts import EvidenceItem
from src.retrieval.evidence import format_evidence
from src.retrieval.retriever import DEFAULT_MIN_SCORE, DEFAULT_TOP_K


def test_retriever_deterministic_defaults():
    assert DEFAULT_TOP_K == 5
    assert DEFAULT_MIN_SCORE == 0.35


def test_evidence_item_contract_fields():
    item = EvidenceItem(
        source_id="f1db:race:monaco-2021",
        snippet="Max Verstappen won after late-race pressure.",
        entity_tags=["driver:max_verstappen", "race:monaco_gp"],
        rank_score=0.91,
    )
    assert item.source_id == "f1db:race:monaco-2021"
    assert item.used_in_answer is False


def test_format_evidence_truncates_to_280_chars():
    long_text = "x" * 400
    hits = [{"source_id": "f1db:driver:max_verstappen", "snippet": long_text, "score": 0.88}]

    evidence = format_evidence(hits, entity_tags=["driver:max_verstappen"])
    assert len(evidence) == 1
    assert len(evidence[0].snippet) == 280
