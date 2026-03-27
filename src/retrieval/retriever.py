DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.35
DATASET_SCOPE = "f1db"
COLLECTION_NAME = "f1_historical"


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
        source_filter = {
            "$and": [
                {"dataset": DATASET_SCOPE},
                {"canonical_entity_id": {"$in": canonical_entity_ids}},
            ]
        }

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
    import chromadb

    client = chromadb.PersistentClient(path=".chroma")
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    results = collection.query(query_texts=[query], n_results=top_k, where=source_filter)

    metadatas = results.get("metadatas", [[]])[0] or []
    documents = results.get("documents", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    hits: list[dict] = []
    for idx, metadata in enumerate(metadatas):
        distance = float(distances[idx]) if idx < len(distances) else 1.0
        score = max(0.0, 1.0 - distance)
        if score < min_score:
            continue
        snippet = str(documents[idx]) if idx < len(documents) else ""
        hits.append(
            {
                "source_id": str(metadata.get("source_id", "")),
                "snippet": snippet[:280],
                "score": score,
            }
        )
    return hits
