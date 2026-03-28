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


def test_build_historical_index_upserts_season_summaries(monkeypatch, tmp_path):
    fake_collection = FakeCollection()
    monkeypatch.setattr("src.retrieval.index_builder._get_collection", lambda *_args, **_kwargs: fake_collection)
    monkeypatch.setattr("src.retrieval.index_builder.write_summary_artifacts", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "src.retrieval.index_builder.build_season_summary_documents",
        lambda *_a, **_k: [
            {
                "chunk_id": "deadbeef",
                "document_text": "Формула 1 сезон 2024",
                "metadata": {"dataset": "f1db", "source_id": "f1db:season-summary:2024:overview"},
            }
        ],
    )

    result = build_historical_index(str(tmp_path), "f1_historical")
    assert result["documents_indexed"] == 1
    assert fake_collection.upsert_calls == 1
    assert fake_collection.last_upsert_size == 1


def test_build_historical_index_is_idempotent(monkeypatch, tmp_path):
    fake_collection = FakeCollection()
    monkeypatch.setattr("src.retrieval.index_builder._get_collection", lambda *_args, **_kwargs: fake_collection)
    monkeypatch.setattr("src.retrieval.index_builder.write_summary_artifacts", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "src.retrieval.index_builder.build_season_summary_documents",
        lambda *_a, **_k: [
            {
                "chunk_id": "abc",
                "document_text": "x",
                "metadata": {"dataset": "f1db", "source_id": "s1"},
            },
            {
                "chunk_id": "def",
                "document_text": "y",
                "metadata": {"dataset": "f1db", "source_id": "s2"},
            },
        ],
    )

    first = build_historical_index(str(tmp_path), "f1_historical")
    second = build_historical_index(str(tmp_path), "f1_historical")

    assert first["unique_ids"] == second["unique_ids"]
    assert second["unique_ids"] == len(fake_collection.ids)
