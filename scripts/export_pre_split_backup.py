#!/usr/bin/env python3
"""Read-only backup of Dadspace collected_events and venues before Events/Activities split."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from supabase import create_client

TABLES = ("collected_events", "venues")
PAGE_SIZE = 1000


def load_all(db, table: str):
    rows = []
    start = 0
    while True:
        batch = db.table(table).select("*").range(start, start + PAGE_SIZE - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def write_csv(path: Path, rows: list[dict]):
    fields = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    url = os.environ["SUPABASE_URL"]
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY or SUPABASE_KEY is required")

    db = create_client(url, key)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("pre-split-backup")
    out.mkdir(exist_ok=True)

    manifest = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "tables": {},
    }

    for table in TABLES:
        rows = load_all(db, table)
        json_path = out / f"{table}_{stamp}.json"
        csv_path = out / f"{table}_{stamp}.csv"
        json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        write_csv(csv_path, rows)
        manifest["tables"][table] = {
            "row_count": len(rows),
            "json": str(json_path),
            "csv": str(csv_path),
        }
        print(f"{table}: {len(rows)} rows")

    manifest_path = out / f"manifest_{stamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
