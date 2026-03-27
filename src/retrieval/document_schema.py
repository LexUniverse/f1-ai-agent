import hashlib
from typing import Any

DATASET = "f1db"


def _pick_source_id(table_name: str, row: dict[str, str]) -> str:
    if row.get("id"):
        return f"{table_name}:{row['id']}"
    if table_name == "f1db-races-race-results":
        race_id = row.get("raceId", "")
        position = row.get("positionDisplayOrder", "")
        driver_id = row.get("driverId", "")
        return f"{table_name}:{race_id}:{position}:{driver_id}"
    ordered_pairs = [f"{key}={value}" for key, value in sorted(row.items()) if value]
    return f"{table_name}:{'|'.join(ordered_pairs)}"


def _canonical_entity_id(table_name: str, row: dict[str, str]) -> str | None:
    if table_name == "f1db-drivers" and row.get("id"):
        return f"driver:{row['id'].replace('-', '_')}"
    if table_name == "f1db-constructors" and row.get("id"):
        return f"team:{row['id'].replace('-', '_')}"
    if table_name == "f1db-races":
        grand_prix_id = row.get("grandPrixId")
        if grand_prix_id:
            return f"race:{grand_prix_id.replace('-', '_')}_gp"
    return None


def _build_document_text(table_name: str, row: dict[str, str]) -> str:
    values = [f"{k}: {v}" for k, v in sorted(row.items()) if v]
    return f"{table_name}\n" + "\n".join(values)


def build_document_from_row(table_name: str, row: dict[str, str]) -> dict[str, Any]:
    source_id = _pick_source_id(table_name, row)
    digest_input = f"dataset={DATASET}|table={table_name}|source_id={source_id}"
    chunk_id = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()

    metadata: dict[str, Any] = {
        "dataset": DATASET,
        "table": table_name,
        "source_id": source_id,
    }
    canonical_entity_id = _canonical_entity_id(table_name, row)
    if canonical_entity_id:
        metadata["canonical_entity_id"] = canonical_entity_id

    return {
        "chunk_id": chunk_id,
        "document_text": _build_document_text(table_name, row),
        "metadata": metadata,
    }
