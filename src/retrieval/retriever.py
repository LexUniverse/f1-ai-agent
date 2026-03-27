from collections.abc import Sequence

DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.35
DATASET_SCOPE = "f1db"


def retrieve_historical_context(
    query: str,
    canonical_entity_ids: list[str],
    *,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    # Phase 3 stays historical-only: dataset="f1db" snapshot scope only.
    source_filter: dict[str, object] = {"dataset": "f1db"}
    if canonical_entity_ids:
        source_filter["canonical_entity_id"] = {"$in": canonical_entity_ids}

    return _query_historical_index(
        query=query,
        source_filter=source_filter,
        top_k=top_k,
        min_score=min_score,
    )


def _query_historical_index(
    *,
    query: str,
    source_filter: dict[str, object],
    top_k: int,
    min_score: float,
) -> list[dict]:
    del query, source_filter
    # Stubbed deterministic response for Phase 3 plan 01 foundation.
    simulated_hits: Sequence[dict] = []
    return [
        {
            "source_id": hit.get("source_id", ""),
            "snippet": hit.get("snippet", ""),
            "score": float(hit.get("score", 0.0)),
        }
        for hit in simulated_hits
        if float(hit.get("score", 0.0)) >= min_score
    ][:top_k]
