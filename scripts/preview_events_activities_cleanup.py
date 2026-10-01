#!/usr/bin/env python3
"""Read-only preview for classifying existing collected_events rows.

Never writes to Supabase. Recurrence is the primary legacy signal, with explicit
exceptions for camps and seasonal/special listings which remain Events.
Activity merge groups use title + venue/location.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from pathlib import Path

from supabase import create_client

# Existing data is imperfect, so treat any standalone "camp/camps" wording as
# a camp for the migration preview. This is deliberately safer than converting
# a school-holiday camp into an undated Activity.
HOLIDAY_CAMP = re.compile(r"\bcamps?\b", re.I)
SEASONAL_OR_SPECIAL_EVENT = re.compile(
    r"\b(?:summer|christmas|halloween|easter|heritage open days?|open days?|"
    r"steaming days?|steaming weekend|badger watch|festival)\b",
    re.I,
)


def norm(value):
    text = (value or "").lower().replace("&", " and ")
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_all(db):
    rows = []
    start = 0
    while True:
        batch = db.table("collected_events").select("*").range(start, start + 999).execute().data or []
        rows.extend(batch)
        if len(batch) < 1000:
            return rows
        start += 1000


def main():
    url = os.environ["SUPABASE_URL"]
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY or SUPABASE_KEY is required")
    db = create_client(url, key)
    rows = fetch_all(db)

    groups = {}
    preview = []
    for row in rows:
        recurrence = (row.get("recurrence") or "unknown").lower()
        text = f"{row.get('title') or ''} {row.get('description') or ''}"
        holiday = bool(HOLIDAY_CAMP.search(text))
        special_event = bool(SEASONAL_OR_SPECIAL_EVENT.search(text))
        proposed = "activity" if recurrence == "recurring" and not holiday and not special_event else "event"
        reason = ""
        if holiday:
            reason = "camp stays an Event"
        elif special_event:
            reason = "seasonal/special listing stays an Event"
        elif recurrence == "recurring":
            reason = "stored recurrence=recurring"
        else:
            reason = f"stored recurrence={recurrence or 'unknown'}"

        venue = row.get("venue_name") or row.get("location") or ""
        group_key = ""
        if proposed == "activity":
            group_key = hashlib.sha1(f"{norm(row.get('title'))}|{norm(venue)}".encode()).hexdigest()
            groups.setdefault(group_key, []).append(row)
        preview.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "start_date": row.get("start_date"),
            "location": row.get("location"),
            "recurrence": row.get("recurrence"),
            "proposed_listing_type": proposed,
            "classification_reason": reason,
            "proposed_is_holiday_camp": holiday,
            "activity_group_key": group_key,
        })

    for item in preview:
        key = item["activity_group_key"]
        members = groups.get(key, []) if key else []
        item["activity_group_size"] = len(members) if members else 0
        item["proposed_action"] = "keep as event"
        if key:
            ordered = sorted(members, key=lambda r: (r.get("last_verified_at") or "", r.get("id") or ""), reverse=True)
            keep_id = ordered[0].get("id") if ordered else None
            item["proposed_action"] = "keep as activity" if item["id"] == keep_id else "merge into activity"
            item["proposed_keep_id"] = keep_id
        else:
            item["proposed_keep_id"] = ""

    out = Path("events-activities-cleanup-preview")
    out.mkdir(exist_ok=True)
    fields = [
        "id", "title", "start_date", "location", "recurrence", "proposed_listing_type",
        "classification_reason", "proposed_is_holiday_camp", "activity_group_key",
        "activity_group_size", "proposed_action", "proposed_keep_id",
    ]
    with (out / "cleanup_preview.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(preview)

    activity_rows = [p for p in preview if p["proposed_listing_type"] == "activity"]
    merge_rows = [p for p in activity_rows if p["proposed_action"] == "merge into activity"]
    holiday_rows = [p for p in preview if p["proposed_is_holiday_camp"]]
    special_rows = [p for p in preview if p["classification_reason"] == "seasonal/special listing stays an Event"]
    print(f"Rows inspected: {len(preview)}")
    print(f"Proposed Events: {len(preview) - len(activity_rows)}")
    print(f"Proposed Activities: {len(activity_rows)}")
    print(f"Activity rows that would merge: {len(merge_rows)}")
    print(f"Camp rows kept as Events: {len(holiday_rows)}")
    print(f"Seasonal/special rows protected as Events: {len(special_rows)}")
    print("READ ONLY: no database rows changed")


if __name__ == "__main__":
    main()
