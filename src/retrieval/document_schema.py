import hashlib
from typing import Any

DATASET = "f1db"


def _bool_csv(value: str) -> bool:
    return str(value).lower() == "true"


def _clean(value: str) -> str:
    return (value or "").strip()


def _slug_to_canonical_race(grand_prix_id: str) -> str:
    return f"race:{grand_prix_id.replace('-', '_')}_gp"


def _slug_to_canonical_gp(gp_id: str) -> str:
    return f"gp:{gp_id.replace('-', '_')}"


def _slug_to_canonical_circuit(circuit_id: str) -> str:
    return f"circuit:{circuit_id.replace('-', '_')}"


def _slug_to_canonical_driver(driver_id: str) -> str:
    return f"driver:{driver_id.replace('-', '_')}"


def _slug_to_canonical_team(team_id: str) -> str:
    return f"team:{team_id.replace('-', '_')}"


def _pick_source_id(table_name: str, row: dict[str, str]) -> str:
    if row.get("id"):
        return f"{table_name}:{row['id']}"
    if table_name == "f1db-races-race-results":
        race_id = row.get("raceId", "")
        position = row.get("positionDisplayOrder", "")
        driver_id = row.get("driverId", "")
        return f"{table_name}:{race_id}:{position}:{driver_id}"
    if table_name == "f1db-seasons-driver-standings":
        year = row.get("year", "")
        driver_id = row.get("driverId", "")
        pos = row.get("positionDisplayOrder", "")
        return f"{table_name}:{year}:{pos}:{driver_id}"
    ordered_pairs = [f"{key}={value}" for key, value in sorted(row.items()) if value]
    return f"{table_name}:{'|'.join(ordered_pairs)}"


def _gp_display(gp_id: str, gp_names: dict[str, str] | None) -> str:
    if gp_names and gp_id in gp_names:
        return gp_names[gp_id]
    return gp_id.replace("-", " ").title() if gp_id else ""


def _circuit_display(circuit_id: str, circuit_names: dict[str, str] | None) -> str:
    if circuit_names and circuit_id in circuit_names:
        return circuit_names[circuit_id]
    return circuit_id.replace("-", " ").title() if circuit_id else ""


def _narrative_race_result(
    row: dict[str, str],
    race_context: dict[str, str] | None,
    gp_names: dict[str, str] | None,
    circuit_names: dict[str, str] | None,
) -> str:
    year = _clean(row.get("year") or (race_context or {}).get("year", ""))
    rnd = _clean(row.get("round") or (race_context or {}).get("round", ""))
    gpid = _clean((race_context or {}).get("grandPrixId", ""))
    official = _clean((race_context or {}).get("officialName", ""))
    gp_label = official or _gp_display(gpid, gp_names) or "Formula 1 Grand Prix"
    if "grand prix" not in gp_label.lower():
        gp_label = f"{gp_label} Grand Prix" if gp_label else "Formula 1 Grand Prix"

    circuit_id = _clean((race_context or {}).get("circuitId", ""))
    circuit_label = _circuit_display(circuit_id, circuit_names)
    driver_id = _clean(row.get("driverId", ""))
    constructor_id = _clean(row.get("constructorId", ""))
    pos_ord = _clean(row.get("positionDisplayOrder", ""))
    pos_num = _clean(row.get("positionNumber", ""))
    points = _clean(row.get("points", ""))
    pole = _bool_csv(row.get("polePosition", ""))
    fastest = _bool_csv(row.get("fastestLap", ""))
    qual_pos = _clean(row.get("qualificationPositionNumber", ""))
    grid_pos = _clean(row.get("gridPositionNumber", ""))

    parts: list[str] = []
    head = f"{gp_label}"
    if year:
        head += f" ({year}"
        if rnd:
            head += f", round {rnd}"
        head += ")"
    parts.append(head + "." if head else "Formula 1 race result.")

    role_bits: list[str] = []
    if pos_ord == "1" or pos_num == "1":
        role_bits.append("race winner (finished P1)")
    else:
        role_bits.append(f"finished in position {pos_text(pos_ord, pos_num)}")
    if driver_id:
        role_bits.append(f"driverId {driver_id}")
    if constructor_id:
        role_bits.append(f"constructorId {constructor_id}")
    parts.append(" ".join(role_bits) + ".")

    extras: list[str] = []
    if points:
        extras.append(f"Championship points scored: {points}.")
    if pole:
        extras.append("Started from pole position.")
    if qual_pos and not pole:
        extras.append(f"Qualifying position: {qual_pos}.")
    if grid_pos:
        extras.append(f"Grid position: {grid_pos}.")
    if fastest:
        extras.append("Set the fastest lap of the race.")
    if circuit_label and gpid:
        extras.append(f"Circuit: {circuit_label}.")

    parts.extend(extras)
    return " ".join(parts)


def pos_text(ord_s: str, num_s: str) -> str:
    if ord_s:
        return ord_s
    return num_s or "unknown"


def _narrative_races_row(row: dict[str, str], gp_names: dict[str, str] | None, circuit_names: dict[str, str] | None) -> str:
    year = _clean(row.get("year", ""))
    rnd = _clean(row.get("round", ""))
    gpid = _clean(row.get("grandPrixId", ""))
    official = _clean(row.get("officialName", ""))
    cid = _clean(row.get("circuitId", ""))
    gp = official or _gp_display(gpid, gp_names) or gpid
    circ = _circuit_display(cid, circuit_names) or cid
    bits = [f"Formula 1 race calendar entry for {year}" if year else "Formula 1 race calendar entry."]
    if rnd:
        bits.append(f"Round {rnd}.")
    if gp:
        bits.append(f"Event: {gp}.")
    if gpid:
        bits.append(f"grandPrixId {gpid}.")
    if circ:
        bits.append(f"Held at circuit {circ}.")
    return " ".join(bits)


def _narrative_seasons_drivers(row: dict[str, str]) -> str:
    year = _clean(row.get("year", ""))
    did = _clean(row.get("driverId", ""))
    wins = _clean(row.get("totalRaceWins", ""))
    pts = _clean(row.get("totalPoints", ""))
    starts = _clean(row.get("totalRaceStarts", ""))
    s = f"In the {year} Formula 1 season, driverId {did} " if year and did else f"Season driver summary for driverId {did}. "
    if starts:
        s += f"Recorded {starts} race starts. "
    if wins:
        s += f"Total race wins that season: {wins}. "
    if pts:
        s += f"Total points: {pts}."
    return s.strip()


def _narrative_drivers_row(row: dict[str, str]) -> str:
    did = _clean(row.get("id", ""))
    full_name = _clean(row.get("fullName", "")) or _clean(row.get("name", ""))
    nat = _clean(row.get("nationalityCountryId", ""))
    wins = _clean(row.get("totalRaceWins", ""))
    s = f"Formula 1 driver profile: id {did}"
    if full_name:
        s += f", {full_name}"
    s += "."
    if nat:
        s += f" Nationality country id: {nat}."
    if wins:
        s += f" Career race wins (total): {wins}."
    return s


def _narrative_grands_prix_row(row: dict[str, str]) -> str:
    gid = _clean(row.get("id", ""))
    full_name = _clean(row.get("fullName", "")) or _clean(row.get("name", ""))
    abbr = _clean(row.get("abbreviation", ""))
    country = _clean(row.get("countryId", ""))
    held = _clean(row.get("totalRacesHeld", ""))
    s = f"Grand Prix series: id {gid}"
    if full_name:
        s += f", {full_name}"
    s += "."
    if abbr:
        s += f" Abbreviation {abbr}."
    if country:
        s += f" Host country id: {country}."
    if held:
        s += f" Total races held in dataset: {held}."
    return s


def _narrative_circuits_row(row: dict[str, str]) -> str:
    cid = _clean(row.get("id", ""))
    name = _clean(row.get("fullName", "")) or _clean(row.get("name", ""))
    place = _clean(row.get("placeName", ""))
    country = _clean(row.get("countryId", ""))
    s = f"Racing circuit id {cid}"
    if name:
        s += f": {name}"
    s += "."
    if place:
        s += f" Location: {place}."
    if country:
        s += f" Country id: {country}."
    return s


def _narrative_constructors_row(row: dict[str, str]) -> str:
    tid = _clean(row.get("id", ""))
    name = _clean(row.get("fullName", "")) or _clean(row.get("name", ""))
    country = _clean(row.get("countryId", ""))
    wins = _clean(row.get("totalRaceWins", ""))
    s = f"Formula 1 constructor (team) id {tid}"
    if name:
        s += f", {name}"
    s += "."
    if country:
        s += f" Country id: {country}."
    if wins:
        s += f" Total race wins: {wins}."
    return s


def _narrative_seasons_row(row: dict[str, str]) -> str:
    year = _clean(row.get("year", ""))
    return f"Formula 1 world championship season {year}." if year else "Formula 1 championship season record."


def _narrative_driver_standings_row(row: dict[str, str]) -> str:
    year = _clean(row.get("year", ""))
    did = _clean(row.get("driverId", ""))
    pos = _clean(row.get("positionDisplayOrder", row.get("positionNumber", "")))
    pts = _clean(row.get("points", ""))
    champ = _bool_csv(row.get("championshipWon", ""))
    s = f"End-of-season drivers' standings for {year}: driverId {did} " if year and did else f"Drivers' standings row for driverId {did}. "
    if pos:
        s += f"finished championship position {pos}. "
    if pts:
        s += f"Points total: {pts}. "
    if champ:
        s += "This driver won the Formula 1 World Drivers' Championship that season (champion)."
    return s.strip()


def _document_text_for_table(
    table_name: str,
    row: dict[str, str],
    *,
    race_context: dict[str, str] | None,
    gp_names: dict[str, str] | None,
    circuit_names: dict[str, str] | None,
) -> str:
    if table_name == "f1db-races-race-results":
        return _narrative_race_result(row, race_context, gp_names, circuit_names)
    if table_name == "f1db-races":
        return _narrative_races_row(row, gp_names, circuit_names)
    if table_name == "f1db-seasons-drivers":
        return _narrative_seasons_drivers(row)
    if table_name == "f1db-drivers":
        return _narrative_drivers_row(row)
    if table_name == "f1db-grands-prix":
        return _narrative_grands_prix_row(row)
    if table_name == "f1db-circuits":
        return _narrative_circuits_row(row)
    if table_name == "f1db-constructors":
        return _narrative_constructors_row(row)
    if table_name == "f1db-seasons":
        return _narrative_seasons_row(row)
    if table_name == "f1db-seasons-driver-standings":
        return _narrative_driver_standings_row(row)
    values = [f"{k}: {v}" for k, v in sorted(row.items()) if v]
    return f"{table_name}\n" + "\n".join(values)


def _canonical_entity_id(
    table_name: str,
    row: dict[str, str],
    *,
    race_context: dict[str, str] | None,
) -> str | None:
    if table_name == "f1db-races-race-results":
        if race_context and _clean(race_context.get("grandPrixId", "")):
            return _slug_to_canonical_race(race_context["grandPrixId"])
        rid = _clean(row.get("raceId", ""))
        return f"race_event:{rid}" if rid else None
    if table_name == "f1db-races" and _clean(row.get("grandPrixId", "")):
        return _slug_to_canonical_race(row["grandPrixId"])
    if table_name == "f1db-drivers" and _clean(row.get("id", "")):
        return _slug_to_canonical_driver(row["id"])
    if table_name == "f1db-constructors" and _clean(row.get("id", "")):
        return _slug_to_canonical_team(row["id"])
    if table_name == "f1db-grands-prix" and _clean(row.get("id", "")):
        return _slug_to_canonical_gp(row["id"])
    if table_name == "f1db-circuits" and _clean(row.get("id", "")):
        return _slug_to_canonical_circuit(row["id"])
    if table_name == "f1db-seasons" and _clean(row.get("year", "")):
        return f"season:{row['year']}"
    if table_name == "f1db-seasons-driver-standings":
        year = _clean(row.get("year", ""))
        did = _clean(row.get("driverId", ""))
        if year and did:
            return f"standings:{year}:{did.replace('-', '_')}"
        return None
    if table_name == "f1db-seasons-drivers":
        year = _clean(row.get("year", ""))
        did = _clean(row.get("driverId", ""))
        if year and did:
            return f"season_driver:{year}:{did.replace('-', '_')}"
        return None
    return None


def _extra_metadata(
    table_name: str,
    row: dict[str, str],
    *,
    race_context: dict[str, str] | None,
) -> dict[str, str]:
    out: dict[str, str] = {}
    if table_name == "f1db-races-race-results":
        year = _clean(row.get("year") or (race_context or {}).get("year", ""))
        gpid = _clean((race_context or {}).get("grandPrixId", ""))
        if year:
            out["year"] = year
        if gpid:
            out["grand_prix_id"] = gpid.lower()
    if table_name == "f1db-seasons-driver-standings" and _clean(row.get("year", "")):
        out["year"] = row["year"]
    if table_name == "f1db-seasons-drivers" and _clean(row.get("year", "")):
        out["year"] = row["year"]
    if table_name == "f1db-races" and _clean(row.get("year", "")):
        out["year"] = row["year"]
    return out


def build_document_from_row(
    table_name: str,
    row: dict[str, str],
    *,
    race_context: dict[str, str] | None = None,
    gp_names: dict[str, str] | None = None,
    circuit_names: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_id = _pick_source_id(table_name, row)
    digest_input = f"dataset={DATASET}|table={table_name}|source_id={source_id}"
    chunk_id = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()

    metadata: dict[str, Any] = {
        "dataset": DATASET,
        "table": table_name,
        "source_id": source_id,
    }
    canonical_entity_id = _canonical_entity_id(table_name, row, race_context=race_context)
    if canonical_entity_id:
        metadata["canonical_entity_id"] = canonical_entity_id

    for key, val in _extra_metadata(table_name, row, race_context=race_context).items():
        metadata[key] = val

    return {
        "chunk_id": chunk_id,
        "document_text": _document_text_for_table(
            table_name,
            row,
            race_context=race_context,
            gp_names=gp_names,
            circuit_names=circuit_names,
        ),
        "metadata": metadata,
    }
