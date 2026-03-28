import pytest

from src.models.api_contracts import EvidenceItem
from src.retrieval.evidence import format_evidence
from src.retrieval.query_normalize import normalize_retrieval_query
from src.retrieval.retriever import DEFAULT_MIN_SCORE, DEFAULT_TOP_K


def test_retriever_deterministic_defaults():
    assert DEFAULT_TOP_K == 10
    assert DEFAULT_MIN_SCORE == 0.25


def test_evidence_item_contract_fields():
    item = EvidenceItem(
        source_id="f1db:race:monaco-2021",
        snippet="Max Verstappen won after late-race pressure.",
        entity_tags=[],
        rank_score=0.91,
    )
    assert item.source_id == "f1db:race:monaco-2021"
    assert item.used_in_answer is False


def test_format_evidence_truncates_to_280_chars():
    long_text = "x" * 400
    full = "y" * 1200
    hits = [
        {
            "source_id": "f1db:driver:max_verstappen",
            "snippet": long_text,
            "document_full": full,
            "score": 0.88,
        }
    ]

    evidence = format_evidence(hits, entity_tags=[])
    assert len(evidence) == 1
    assert len(evidence[0].snippet) == 280
    assert evidence[0].context_for_llm == full
    dumped = evidence[0].model_dump()
    assert "context_for_llm" not in dumped


def test_normalize_retrieval_query_lowercases_and_strips_punct():
    nq, cids, tags = normalize_retrieval_query("  Гран-при Монако — 2000!  ")
    assert "монако" in nq
    assert "2000" in nq
    assert cids == []
    assert tags == []


def test_normalize_retrieval_query_empty():
    nq, cids, tags = normalize_retrieval_query("   ")
    assert nq == ""
    assert cids == []
