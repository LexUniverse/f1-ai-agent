from src.retrieval.document_schema import build_document_from_row


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
