import logging
from typing import Any

import chromadb
from chromadb.errors import NotFoundError

from src.retrieval.embeddings import get_embedding_function

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 10
DEFAULT_MIN_SCORE = 0.25
# Chroma stores full document; we pass this much into the LLM (snippet for UI stays short).
MAX_LLM_CHARS_PER_HIT = 16_000
DATASET_SCOPE = "f1db"
COLLECTION_NAME = "f1_historical"


def _open_historical_collection():
    """Open collection using persisted embedding config (avoids default vs RoSBERTa conflict on get)."""
    client = chromadb.PersistentClient(path=".chroma")
    try:
        return client.get_collection(name=COLLECTION_NAME, embedding_function=None)
    except NotFoundError:
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )


def retrieve_historical_context(
    query: str,
    _canonical_entity_ids: list[str],
    *,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    year_hint: int | None = None,
) -> list[dict]:
    """Vector search only; query should match indexed embedding model (RU/EN RoSBERTa by default)."""
    base_filter: dict[str, object] = {"dataset": "f1db"}
    return _query_historical_index(
        query_text=query.strip(),
        source_filter=base_filter,
        top_k=top_k,
        min_score=min_score,
        year_hint=year_hint,
    )


def _where_dataset_and_optional_year(
    source_filter: dict[str, object], year_hint: int | None
) -> dict[str, object]:
    if year_hint is None:
        return source_filter
    return {"$and": [source_filter, {"year": str(year_hint)}]}


def _hits_from_chroma_query(
    collection: chromadb.Collection,
    *,
    query_text: str,
    where: dict[str, object],
    top_k: int,
    min_score: float,
) -> list[dict]:
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where,
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
        sid = str((metadata or {}).get("source_id", ""))
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


def _query_historical_index(
    *,
    query_text: str,
    source_filter: dict[str, object],
    top_k: int,
    min_score: float,
    year_hint: int | None = None,
) -> list[dict]:
    if not query_text:
        return []

    collection = _open_historical_collection()
    try:
        n_docs = int(collection.count())
    except Exception:
        n_docs = -1
    if 0 <= n_docs < 20:
        logger.warning(
            "Chroma collection %r содержит только %s документ(ов). "
            "Ожидаются сотни чанков после полной индексации: "
            "python3 scripts/build_f1_season_summaries.py",
            COLLECTION_NAME,
            n_docs,
        )

    where_year = _where_dataset_and_optional_year(source_filter, year_hint)
    hits = _hits_from_chroma_query(
        collection,
        query_text=query_text,
        where=where_year,
        top_k=top_k,
        min_score=min_score,
    )
    if year_hint is not None and not hits:
        hits = _hits_from_chroma_query(
            collection,
            query_text=query_text,
            where=source_filter,
            top_k=top_k,
            min_score=min_score,
        )
    return hits
