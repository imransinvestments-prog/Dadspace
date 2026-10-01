#!/usr/bin/env python3
"""Export all Dadspace collected events to JSON and CSV. This script is read-only."""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from supabase import create_client


def main():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    db = create_client(url, key)

    rows = []
    start = 0
    batch_size = 1000
    while True:
        batch = db.table("collected_events").select("*").range(start, start + batch_size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        start += batch_size

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("event-backup")
    out.mkdir(exist_ok=True)

    json_file = out / f"collected_events_{stamp}.json"
    csv_file = out / f"collected_events_{stamp}.csv"
    manifest_file = out / f"manifest_{stamp}.json"

    json_file.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    fields = sorted({field for row in rows for field in row})
    with csv_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    manifest_file.write_text(json.dumps({
        "table": "collected_events",
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "json": str(json_file),
        "csv": str(csv_file),
        "read_only": True
    }, indent=2), encoding="utf-8")

    print(f"Exported {len(rows)} rows")
    print(json_file)
    print(csv_file)
    print(manifest_file)


if __name__ == "__main__":
    main()
