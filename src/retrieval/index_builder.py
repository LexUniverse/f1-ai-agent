import os
from pathlib import Path
from typing import Any

from src.retrieval.embeddings import get_embedding_function
from src.retrieval.season_summary_corpus import build_season_summary_documents, write_summary_artifacts

# Small CSV set consumed inside season_summary_corpus (not row-wise index):
# f1db-seasons-driver-standings, f1db-seasons-entrants-drivers, f1db-drivers,
# f1db-constructors, f1db-grands-prix, f1db-countries, f1db-races, f1db-races-race-results

DEFAULT_COLLECTION = "f1_historical"
UPSERT_BATCH_SIZE = 250


def _get_collection(collection_name: str):
    import chromadb

    client = chromadb.PersistentClient(path=".chroma")
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=get_embedding_function(),
    )


def build_historical_index(
    csv_root: str = "f1db-csv",
    collection_name: str = DEFAULT_COLLECTION,
    *,
    years_span: int = 50,
    write_markdown_summaries: bool = True,
    summaries_dir: str | Path | None = None,
) -> dict[str, Any]:
    collection = _get_collection(collection_name)
    root = Path(csv_root)

    docs = build_season_summary_documents(root, years_span=years_span)
    summaries_out: str | None = None
    if write_markdown_summaries and docs:
        sdir = Path(summaries_dir) if summaries_dir else Path(__file__).resolve().parents[2] / "scripts" / "summaries"
        write_summary_artifacts(docs, sdir)
        summaries_out = str(sdir.resolve())
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for doc in docs:
        ids.append(doc["chunk_id"])
        documents.append(doc["document_text"])
        metadatas.append(doc["metadata"])

    for start in range(0, len(ids), UPSERT_BATCH_SIZE):
        end = start + UPSERT_BATCH_SIZE
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    emb_label = "chromadb_default" if os.environ.get("F1_CHROMA_DEFAULT_EMBEDDINGS", "").strip() in ("1", "true", "yes") else os.environ.get("F1_EMBEDDING_MODEL", "ai-forever/ru-en-RoSBERTa")
    out: dict[str, Any] = {
        "dataset": "f1db",
        "collection_name": collection_name,
        "documents_indexed": len(ids),
        "unique_ids": len(set(ids)),
        "years_span": years_span,
        "embedding_model": emb_label,
    }
    if summaries_out:
        out["summaries_written_to"] = summaries_out
    return out
