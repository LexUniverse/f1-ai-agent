from src.retrieval.document_schema import build_document_from_row
from src.retrieval.index_builder import build_historical_index


def test_document_schema_is_deterministic():
    row = {
        "id": "max-verstappen",
        "fullName": "Max Verstappen",
        "name": "Max Verstappen",
        "nationalityCountryId": "netherlands",
    }

    first = build_document_from_row("f1db-drivers", row)
    second = build_document_from_row("f1db-drivers", row)

    assert first["chunk_id"] == second["chunk_id"]
    assert first["metadata"]["canonical_entity_id"] == "driver:max_verstappen"


def test_document_schema_contains_required_metadata():
    row = {
        "id": "1",
        "grandPrixId": "monaco",
        "officialName": "Grand Prix de Monaco 1950",
        "year": "1950",
    }

    document = build_document_from_row("f1db-races", row)

    assert document["metadata"]["dataset"] == "f1db"
    assert document["metadata"]["table"] == "f1db-races"
    assert document["metadata"]["source_id"] == "f1db-races:1"
    assert document["metadata"]["canonical_entity_id"] == "race:monaco_gp"


class FakeCollection:
    def __init__(self):
        self.ids: set[str] = set()
        self.upsert_calls = 0
        self.last_upsert_size = 0

    def upsert(self, *, ids, documents, metadatas):
        self.upsert_calls += 1
        self.last_upsert_size = len(ids)
        self.ids.update(ids)


def test_build_historical_index_upserts_from_csv(monkeypatch, tmp_path):
    csv_root = tmp_path / "csv"
    csv_root.mkdir()
    (csv_root / "f1db-drivers.csv").write_text(
        "\"id\",\"name\"\n\"max-verstappen\",\"Max Verstappen\"\n",
        encoding="utf-8",
    )
    (csv_root / "f1db-constructors.csv").write_text(
        "\"id\",\"name\"\n\"ferrari\",\"Ferrari\"\n",
        encoding="utf-8",
    )
    (csv_root / "f1db-races.csv").write_text(
        "\"id\",\"grandPrixId\",\"officialName\"\n1,\"monaco\",\"Monaco GP\"\n",
        encoding="utf-8",
    )
    (csv_root / "f1db-races-race-results.csv").write_text(
        "\"raceId\",\"positionDisplayOrder\",\"driverId\"\n1,1,\"max-verstappen\"\n",
        encoding="utf-8",
    )

    fake_collection = FakeCollection()
    monkeypatch.setattr("src.retrieval.index_builder._get_collection", lambda *_args, **_kwargs: fake_collection)

    result = build_historical_index(str(csv_root), "f1_historical")
    assert result["documents_indexed"] > 0
    assert fake_collection.upsert_calls > 0
    assert fake_collection.last_upsert_size > 0


def test_build_historical_index_is_idempotent(monkeypatch, tmp_path):
    csv_root = tmp_path / "csv"
    csv_root.mkdir()
    for name, body in {
        "f1db-drivers.csv": "\"id\",\"name\"\n\"max-verstappen\",\"Max Verstappen\"\n",
        "f1db-constructors.csv": "\"id\",\"name\"\n\"ferrari\",\"Ferrari\"\n",
        "f1db-races.csv": "\"id\",\"grandPrixId\",\"officialName\"\n1,\"monaco\",\"Monaco GP\"\n",
        "f1db-races-race-results.csv": "\"raceId\",\"positionDisplayOrder\",\"driverId\"\n1,1,\"max-verstappen\"\n",
    }.items():
        (csv_root / name).write_text(body, encoding="utf-8")

    fake_collection = FakeCollection()
    monkeypatch.setattr("src.retrieval.index_builder._get_collection", lambda *_args, **_kwargs: fake_collection)

    first = build_historical_index(str(csv_root), "f1_historical")
    second = build_historical_index(str(csv_root), "f1_historical")

    assert first["unique_ids"] == second["unique_ids"]
    assert second["unique_ids"] == len(fake_collection.ids)
