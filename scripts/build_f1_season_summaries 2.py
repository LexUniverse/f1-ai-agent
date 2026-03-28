#!/usr/bin/env python3
"""Build Russian season-summary chunks from f1db CSVs and upsert into Chroma."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.index_builder import build_historical_index  # noqa: E402
from src.retrieval.season_summary_corpus import build_season_summary_documents, write_summary_artifacts  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="F1 season summaries → Chroma (ru-en-RoSBERTa by default)")
    p.add_argument("--csv-root", default="f1db-csv", help="Directory with f1db CSV exports")
    p.add_argument("--collection", default="f1_historical", help="Chroma collection name")
    p.add_argument("--years", type=int, default=50, help="How many seasons ending at latest CSV year")
    p.add_argument(
        "--dump-jsonl",
        metavar="PATH",
        help="If set, write chunks as JSONL and skip Chroma (inspect only)",
    )
    args = p.parse_args()

    summaries_dir = ROOT / "scripts" / "summaries"

    if args.dump_jsonl:
        docs = build_season_summary_documents(args.csv_root, years_span=args.years)
        out = Path(args.dump_jsonl)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for d in docs:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        write_summary_artifacts(docs, summaries_dir)
        print(f"Wrote {len(docs)} chunks to {out}")
        print(f"Wrote markdown + manifest under {summaries_dir}")
        return 0

    stats = build_historical_index(args.csv_root, args.collection, years_span=args.years)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
