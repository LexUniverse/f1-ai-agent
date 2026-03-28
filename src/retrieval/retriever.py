from typing import Any

from src.retrieval.embeddings import get_embedding_function

DEFAULT_TOP_K = 10
DEFAULT_MIN_SCORE = 0.25
# Chroma stores full document; we pass this much into the LLM (snippet for UI stays short).
MAX_LLM_CHARS_PER_HIT = 16_000
DATASET_SCOPE = "f1db"
COLLECTION_NAME = "f1_historical"


def retrieve_historical_context(
    query: str,
    _canonical_entity_ids: list[str],
    *,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    """Vector search only; query should match indexed embedding model (RU/EN RoSBERTa by default)."""
    source_filter: dict[str, object] = {"dataset": "f1db"}
    return _query_historical_index(
        query_text=query.strip(),
        source_filter=source_filter,
        top_k=top_k,
        min_score=min_score,
    )


def _query_historical_index(
    *,
    query_text: str,
    source_filter: dict[str, object],
    top_k: int,
    min_score: float,
) -> list[dict]:
    import chromadb

    if not query_text:
        return []

    client = chromadb.PersistentClient(path=".chroma")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )

    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where=source_filter,
    )
    metadatas = results.get("metadatas", [[]])[0] or []
    documents = results.get("documents", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    hits: list[dict] = []
    for idx, metadata in enumerate(metadatas):
        distance = float(distances[idx]) if idx < len(distances) else 1.0
        score = max(0.0, 1.0 - distance)
        if score < min_score:
            continue
        sid = str(metadata.get("source_id", ""))
        full = str(documents[idx]) if idx < len(documents) else ""
        hits.append(
            {
                "source_id": sid,
                "snippet": full[:280],
                "document_full": full[:MAX_LLM_CHARS_PER_HIT],
                "score": score,
            }
        )
    hits.sort(key=lambda x: float(x["score"]), reverse=True)
    return hits
