import csv
from pathlib import Path
from typing import Any

from src.retrieval.document_schema import build_document_from_row

CSV_TABLES = (
    "f1db-drivers.csv",
    "f1db-constructors.csv",
    "f1db-races.csv",
    "f1db-races-race-results.csv",
)
DEFAULT_COLLECTION = "f1_historical"
UPSERT_BATCH_SIZE = 250


def _get_collection(collection_name: str):
    import chromadb

    client = chromadb.PersistentClient(path=".chroma")
    return client.get_or_create_collection(name=collection_name)


def _iter_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {key: (value or "") for key, value in row.items()}


def build_historical_index(csv_root: str = "f1db-csv", collection_name: str = DEFAULT_COLLECTION) -> dict[str, Any]:
    collection = _get_collection(collection_name)
    root = Path(csv_root)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    tables_processed = 0

    for csv_name in CSV_TABLES:
        csv_path = root / csv_name
        if not csv_path.exists():
            continue
        tables_processed += 1
        table_name = csv_name.removesuffix(".csv")
        for row in _iter_rows(csv_path):
            doc = build_document_from_row(table_name, row)
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

    return {
        "dataset": "f1db",
        "collection_name": collection_name,
        "tables_processed": tables_processed,
        "documents_indexed": len(ids),
        "unique_ids": len(set(ids)),
    }
