"""
Season-level Russian narrative chunks from a small set of f1db CSVs (last N years).

Chunk kinds:
  - overview: driver count, full standings table (team — driver — place — points)
  - grand_prix: one race — country, year, podium / key result context
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator


DATASET = "f1db"


def _iter_rows(csv_path: Path) -> Iterator[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {key: (value or "").strip() for key, value in row.items()}


def _load_map_by_id(csv_root: Path, name: str, id_key: str, label_keys: tuple[str, ...]) -> dict[str, str]:
    path = csv_root / name
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for row in _iter_rows(path):
        rid = row.get(id_key, "")
        if not rid:
            continue
        label = ""
        for k in label_keys:
            label = (row.get(k) or "").strip()
            if label:
                break
        out[rid] = label or rid
    return out


def _rounds_weight(rounds_field: str) -> int:
    if not rounds_field:
        return 0
    return len([p for p in rounds_field.split(";") if p.strip()])


def _driver_constructor_by_season(csv_root: Path) -> dict[tuple[int, str], str]:
    """Pick constructor with most scheduled rounds for (year, driverId)."""
    path = csv_root / "f1db-seasons-entrants-drivers.csv"
    if not path.exists():
        return {}
    best: dict[tuple[int, str], tuple[int, str]] = {}
    for row in _iter_rows(path):
        try:
            year = int(row.get("year", "") or 0)
        except ValueError:
            continue
        did = row.get("driverId", "")
        cid = row.get("constructorId", "")
        if not year or not did or not cid:
            continue
        w = _rounds_weight(row.get("rounds", ""))
        key = (year, did)
        prev = best.get(key)
        if prev is None or w > prev[0]:
            best[key] = (w, cid)
    return {k: v[1] for k, v in best.items()}


def _max_race_year(csv_root: Path) -> int:
    path = csv_root / "f1db-races.csv"
    if not path.exists():
        return 0
    y = 0
    for row in _iter_rows(path):
        try:
            yi = int(row.get("year", "") or 0)
        except ValueError:
            continue
        y = max(y, yi)
    return y


def _years_window(csv_root: Path, span: int) -> tuple[int, int]:
    hi = _max_race_year(csv_root)
    if hi <= 0:
        return 0, 0
    lo = hi - (span - 1)
    return lo, hi


def _season_driver_ids(csv_root: Path) -> dict[int, set[str]]:
    """All driverIds listed for a season in f1db-seasons-drivers (чемпионат — все заявленные/участвовавшие)."""
    path = csv_root / "f1db-seasons-drivers.csv"
    if not path.exists():
        return {}
    by_year: dict[int, set[str]] = defaultdict(set)
    for row in _iter_rows(path):
        try:
            y = int(row.get("year", "") or 0)
        except ValueError:
            continue
        did = row.get("driverId", "")
        if y and did:
            by_year[y].add(did)
    return by_year


def _gp_country_line(gp_id: str, gp_countries: dict[str, str], countries: dict[str, str]) -> str:
    cslug = gp_countries.get(gp_id, "")
    cname = countries.get(cslug, cslug.replace("-", " ").title() if cslug else "")
    if cname:
        return f"страна проведения: {cname} ({cslug})" if cslug else f"страна проведения: {cname}"
    return ""


def build_season_summary_documents(
    csv_root: str | Path = "f1db-csv",
    *,
    years_span: int = 50,
) -> list[dict[str, Any]]:
    root = Path(csv_root)
    lo_year, hi_year = _years_window(root, years_span)
    if hi_year <= 0:
        return []

    drivers = _load_map_by_id(root, "f1db-drivers.csv", "id", ("fullName", "name"))
    constructors = _load_map_by_id(root, "f1db-constructors.csv", "id", ("fullName", "name"))
    gps = _load_map_by_id(root, "f1db-grands-prix.csv", "id", ("fullName", "name"))
    gp_country: dict[str, str] = {}
    gp_path = root / "f1db-grands-prix.csv"
    if gp_path.exists():
        for row in _iter_rows(gp_path):
            gid = row.get("id", "")
            if gid:
                gp_country[gid] = row.get("countryId", "")

    countries = _load_map_by_id(root, "f1db-countries.csv", "id", ("name",))

    dc_map = _driver_constructor_by_season(root)
    season_drivers = _season_driver_ids(root)

    # Standings by year
    standings_by_year: dict[int, list[dict[str, str]]] = defaultdict(list)
    st_path = root / "f1db-seasons-driver-standings.csv"
    if st_path.exists():
        for row in _iter_rows(st_path):
            try:
                y = int(row.get("year", "") or 0)
            except ValueError:
                continue
            if y < lo_year or y > hi_year:
                continue
            standings_by_year[y].append(row)

    # Races by year
    races_by_year: dict[int, list[dict[str, str]]] = defaultdict(list)
    races_path = root / "f1db-races.csv"
    races_by_id: dict[str, dict[str, str]] = {}
    if races_path.exists():
        for row in _iter_rows(races_path):
            try:
                y = int(row.get("year", "") or 0)
            except ValueError:
                continue
            rid = row.get("id", "")
            if rid:
                races_by_id[rid] = row
            if y < lo_year or y > hi_year:
                continue
            races_by_year[y].append(row)

    # Race results indexed by raceId
    results_by_race: dict[str, list[dict[str, str]]] = defaultdict(list)
    rr_path = root / "f1db-races-race-results.csv"
    if rr_path.exists():
        for row in _iter_rows(rr_path):
            rid = row.get("raceId", "")
            if not rid:
                continue
            try:
                y = int(row.get("year", "") or 0)
            except ValueError:
                continue
            if y < lo_year or y > hi_year:
                continue
            results_by_race[rid].append(row)

    docs: list[dict[str, Any]] = []

    for year in range(lo_year, hi_year + 1):
        st_rows = standings_by_year.get(year, [])
        st_by_driver: dict[str, dict[str, str]] = {}
        for r in st_rows:
            did = r.get("driverId", "")
            if did:
                st_by_driver[did] = r

        participant_ids = set(season_drivers.get(year, set()))
        for did in st_by_driver:
            participant_ids.add(did)
        if not participant_ids:
            participant_ids = set(st_by_driver.keys())

        def _sort_key(did: str) -> tuple[int, int, str]:
            r = st_by_driver.get(did)
            if not r:
                return (1, 9999, drivers.get(did, did))
            pos_raw = r.get("positionDisplayOrder") or r.get("positionNumber") or ""
            try:
                return (0, int(pos_raw), drivers.get(did, did))
            except ValueError:
                return (0, 9998, drivers.get(did, did))

        ordered_ids = sorted(participant_ids, key=_sort_key)
        n_drivers = len(ordered_ids)
        lines_table: list[str] = []
        for did in ordered_ids:
            r = st_by_driver.get(did)
            cid = dc_map.get((year, did), "")
            dname = drivers.get(did, did)
            cname = constructors.get(cid, cid) if cid else "—"
            if r:
                pos = r.get("positionDisplayOrder") or r.get("positionNumber") or "—"
                pts = r.get("points", "")
                lines_table.append(f"{pos}. {cname} — {dname} — {pts} очков")
            else:
                lines_table.append(f"—. {cname} — {dname} — вне итоговой классификации / 0 очков")

        champ_note = ""
        for r in st_rows:
            if (r.get("championshipWon") or "").lower() == "true":
                did = r.get("driverId", "")
                champ_note = f" Чемпион мира среди пилотов: {drivers.get(did, did)}."
                break

        overview_lines = [
            f"Формула 1, сезон {year} год. "
            f"В сезоне участвовало {n_drivers} гонщиков (полный список в таблице ниже).{champ_note}",
            "Полная таблица: команда — гонщик — место в чемпионате — очки за сезон:",
            *lines_table,
            f"Контекст для семантического поиска: сезон {year}, итоговая таблица чемпионата Формулы-1, все пилоты сезона.",
        ]
        overview_text = "\n".join(overview_lines)
        overview_sid = f"f1db:season-summary:{year}:overview"
        overview_digest = f"dataset={DATASET}|source_id={overview_sid}"
        docs.append(
            {
                "chunk_id": hashlib.sha1(overview_digest.encode("utf-8")).hexdigest(),
                "document_text": overview_text,
                "metadata": {
                    "dataset": DATASET,
                    "table": "f1db-season-summary",
                    "source_id": overview_sid,
                    "year": str(year),
                    "chunk_kind": "season_overview",
                },
            }
        )

        year_races = races_by_year.get(year, [])
        year_races.sort(key=lambda r: int(r.get("round") or 0))
        for race in year_races:
            rid = race.get("id", "")
            rnd = race.get("round", "")
            gpid = race.get("grandPrixId", "")
            official = race.get("officialName", "")
            gp_en = gps.get(gpid, gpid.replace("-", " ").title())
            country_bit = _gp_country_line(gpid, gp_country, countries)

            rows = sorted(
                results_by_race.get(rid, []),
                key=lambda x: int(x.get("positionDisplayOrder") or x.get("positionNumber") or "9999"),
            )
            podium_lines: list[str] = []
            full_grid_lines: list[str] = []
            for rr in rows:
                pos = rr.get("positionDisplayOrder") or rr.get("positionNumber") or ""
                did = rr.get("driverId", "")
                cid = rr.get("constructorId", "")
                pts = rr.get("points", "")
                tim = (rr.get("time") or "").strip()
                reason = (rr.get("reasonRetired") or "").strip()
                status_bits = tim if tim else (f"сход: {reason}" if reason else "")
                line = (
                    f"место {pos or '?'}: {drivers.get(did, did)} ({constructors.get(cid, cid)}), "
                    f"очки {pts}"
                    + (f", {status_bits}" if status_bits else "")
                )
                full_grid_lines.append(line)
                if not pos:
                    continue
                try:
                    pi = int(pos)
                except ValueError:
                    continue
                if pi <= 3:
                    podium_lines.append(
                        f"место {pos}: {drivers.get(did, did)} ({constructors.get(cid, cid)}), очки за гонку {pts}"
                    )

            headline = f"Итог гонки (победитель): {podium_lines[0]}." if podium_lines else ""
            race_bits = [
                headline,
                f"Формула 1, сезон {year}, этап {rnd} — Гран-при: {gp_en}.",
                f"Официальное название гонки: {official}." if official else "",
                country_bit,
                f"Идентификаторы для поиска: grand prix {gp_en}, {gpid}, год {year}, круг {rnd}, формула 1, победитель, подиум.",
                "Полная классификация гонки (все строки результатов):",
                *full_grid_lines,
            ]
            race_text = "\n".join(b for b in race_bits if b)
            race_sid = f"f1db:season-summary:{year}:gp:{rnd}:{gpid}"
            race_digest = f"dataset={DATASET}|source_id={race_sid}"
            meta: dict[str, Any] = {
                "dataset": DATASET,
                "table": "f1db-season-summary",
                "source_id": race_sid,
                "year": str(year),
                "chunk_kind": "grand_prix_race",
            }
            if gpid:
                meta["grand_prix_id"] = gpid.lower()
            docs.append(
                {
                    "chunk_id": hashlib.sha1(race_digest.encode("utf-8")).hexdigest(),
                    "document_text": race_text,
                    "metadata": meta,
                }
            )

    return docs


def write_summary_artifacts(docs: list[dict[str, Any]], output_dir: str | Path) -> Path:
    """Persist human-readable season files + manifest next to scripts (for diff/review)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.jsonl"
    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)

    with manifest_path.open("w", encoding="utf-8") as mf:
        for d in docs:
            meta = d.get("metadata") or {}
            rec = {
                "chunk_id": d.get("chunk_id"),
                "source_id": meta.get("source_id"),
                "year": meta.get("year"),
                "chunk_kind": meta.get("chunk_kind"),
            }
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            y = meta.get("year", "")
            if str(y).isdigit():
                by_year[int(y)].append(d)

    for year in sorted(by_year):
        parts: list[str] = [f"# Сезон {year}\n"]
        items = sorted(
            by_year[year],
            key=lambda x: (
                0 if (x.get("metadata") or {}).get("chunk_kind") == "season_overview" else 1,
                (x.get("metadata") or {}).get("source_id", ""),
            ),
        )
        for d in items:
            sid = (d.get("metadata") or {}).get("source_id", "")
            parts.append(f"## {sid}\n\n{d.get('document_text', '')}\n")
        (out / f"season_{year}.md").write_text("\n".join(parts), encoding="utf-8")

    return out
