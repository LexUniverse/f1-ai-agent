from src.retrieval.document_schema import build_document_from_row


def test_race_result_monaco_2000_narrative_and_canonical():
    row = {
        "raceId": "653",
        "year": "2000",
        "round": "7",
        "positionDisplayOrder": "1",
        "positionNumber": "1",
        "positionText": "1",
        "driverNumber": "2",
        "driverId": "david-coulthard",
        "constructorId": "mclaren",
        "engineManufacturerId": "mercedes",
        "tyreManufacturerId": "bridgestone",
        "sharedCar": "false",
        "laps": "78",
        "time": "1:49:28.213",
        "points": "10",
        "polePosition": "false",
        "qualificationPositionNumber": "3",
        "gridPositionNumber": "3",
        "fastestLap": "false",
    }
    race_context = {
        "id": "653",
        "year": "2000",
        "round": "7",
        "grandPrixId": "monaco",
        "officialName": "Grand Prix de Monaco 2000",
        "circuitId": "monaco",
    }
    doc = build_document_from_row(
        "f1db-races-race-results",
        row,
        race_context=race_context,
        gp_names={"monaco": "Monaco Grand Prix"},
        circuit_names={"monaco": "Circuit de Monaco"},
    )
    text = doc["document_text"].lower()
    assert "david-coulthard" in text
    assert "monaco" in text
    assert "2000" in text
    assert doc["metadata"].get("canonical_entity_id") == "race:monaco_gp"
    assert doc["metadata"].get("grand_prix_id") == "monaco"


def test_seasons_driver_standings_2021_champion_text():
    row = {
        "year": "2021",
        "positionDisplayOrder": "1",
        "positionNumber": "1",
        "positionText": "1",
        "driverId": "max-verstappen",
        "points": "395.5",
        "championshipWon": "true",
    }
    doc = build_document_from_row("f1db-seasons-driver-standings", row)
    text = doc["document_text"].lower()
    assert "champion" in text
    assert "2021" in text
    assert "max-verstappen" in text
