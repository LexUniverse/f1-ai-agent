from src.ui.provenance_display import use_unified_provenance_expander


def test_use_unified_false_when_provenance_missing():
    assert use_unified_provenance_expander({}) is False
    assert use_unified_provenance_expander({"details": {}}) is False


def test_use_unified_true_when_rag_evidence_nonempty():
    d = {"provenance": {"rag": {"normalized_query": "q", "evidence": [{"source_id": "a", "snippet": "x"}]}}}
    assert use_unified_provenance_expander(d) is True


def test_use_unified_true_when_web_results_nonempty():
    d = {"provenance": {"rag": {"normalized_query": "", "evidence": []}, "web": {"results": [{"url": "u"}]}}}
    assert use_unified_provenance_expander(d) is True


def test_use_unified_false_when_provenance_empty_or_nested_empty():
    assert use_unified_provenance_expander({"provenance": {}}) is False
    assert (
        use_unified_provenance_expander(
            {
                "provenance": {
                    "rag": {"normalized_query": "", "evidence": []},
                    "web": {"queries": [], "results": []},
                    "synthesis": {},
                }
            }
        )
        is False
    )
