import pytest

from src.models.api_contracts import EvidenceItem
from src.retrieval.evidence import format_evidence
from src.retrieval.retriever import DEFAULT_MIN_SCORE, DEFAULT_TOP_K
from src.retrieval.alias_resolver import resolve_entities


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


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    [
        ("Макс Ферстаппен", ["driver:max_verstappen"]),
        ("max verstappen", ["driver:max_verstappen"]),
        ("Феррари", ["team:ferrari"]),
        ("scuderia ferrari", ["team:ferrari"]),
        ("Гран-при Монако", ["race:monaco_gp"]),
        ("monaco grand prix", ["race:monaco_gp"]),
    ],
)
def test_ru_en_aliases_map_to_same_canonical_ids(query, expected_ids):
    _, canonical_entity_ids, _ = resolve_entities(query)
    assert canonical_entity_ids == expected_ids


def test_unknown_alias_returns_empty_entities():
    normalized_query, canonical_entity_ids, entity_tags = resolve_entities("Unknown driver 2026")
    assert normalized_query
    assert canonical_entity_ids == []
    assert entity_tags == []
