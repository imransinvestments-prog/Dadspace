#!/usr/bin/env python3
"""Audit obvious Dadspace event duplicates and optionally merge them.

Default mode is READ-ONLY and writes a CSV plan. `--apply` requires a backup
manifest created by export_events_backup.py. Recurring/weekly classes and events
at different venues are never merged automatically.

Automatic merge candidates must point to the exact same official event URL,
have the same start date, and name the same/sufficiently similar venue. This is
intentionally conservative: ambiguous pairs stay for human review.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path

from supabase import create_client

PROTECTED_RE = re.compile(
    r"\b(weekly|every\s+(?:mon|tue|wed|thu|fri|sat|sun)|term[- ]?time|class|lesson|session|club|course)\b",
    re.I,
)


def normalise(value):
    text = str(value or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_similarity(a, b):
    aa = set(normalise(a).split())
    bb = set(normalise(b).split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def same_venue(a, b):
    aa = normalise(a)
    bb = normalise(b)
    if not aa or not bb:
        return False
    return aa == bb or aa in bb or bb in aa or token_similarity(aa, bb) >= 0.75


def protected(row):
    if normalise(row.get("recurrence")) == "recurring":
        return True
    text = f"{row.get('title') or ''} {row.get('description') or ''}"
    return bool(PROTECTED_RE.search(text))


def richness(row):
    useful = ["description", "time_text", "location", "event_url", "cost_text", "age_range", "image_url"]
    return sum(1 for field in useful if row.get(field))


def choose_keep(a, b):
    return (a, b) if richness(a) >= richness(b) else (b, a)


def candidates(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(str(row.get("start_date") or "")[:10], []).append(row)

    plan = []
    already_removed = set()
    for date, same_day in grouped.items():
        for i, left in enumerate(same_day):
            if left.get("id") in already_removed or protected(left):
                continue
            left_url = str(left.get("event_url") or "").strip()
            left_venue = left.get("location")
            if not left_url or not left_venue:
                continue

            for right in same_day[i + 1:]:
                if right.get("id") in already_removed or protected(right):
                    continue
                right_url = str(right.get("event_url") or "").strip()
                if not right_url or left_url != right_url:
                    continue
                if not same_venue(left_venue, right.get("location")):
                    continue

                keep, remove = choose_keep(left, right)
                plan.append({
                    "date": date,
                    "venue": keep.get("location") or "",
                    "kept_id": keep.get("id"),
                    "kept_title": keep.get("title") or "",
                    "removed_id": remove.get("id"),
                    "removed_title": remove.get("title") or "",
                    "kept_source_id": keep.get("source_id") or "",
                    "removed_source_id": remove.get("source_id") or "",
                    "event_url": left_url,
                    "reason": "same official event URL + same date + same/similar venue; non-recurring",
                })
                already_removed.add(remove.get("id"))
                if remove is left:
                    break
    return plan


def load_rows(db):
    rows, start, size = [], 0, 1000
    while True:
        batch = db.table("collected_events").select("*").range(start, start + size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < size:
            return rows
        start += size


def validate_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("table") != "collected_events" or manifest.get("read_only") is not True:
        raise RuntimeError("Backup manifest is not a valid collected_events export")
    if not manifest.get("row_count"):
        raise RuntimeError("Backup manifest has no rows; refusing to mutate data")
    return manifest


def merged_patch(keep, remove):
    patch = {}
    for field in ("description", "time_text", "location", "event_url", "cost_text", "age_range"):
        if not keep.get(field) and remove.get(field):
            patch[field] = remove[field]
    return patch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually merge/delete rows")
    parser.add_argument("--backup-manifest", help="Required with --apply")
    parser.add_argument("--output", default="duplicate-review/duplicate_merge_plan.csv")
    args = parser.parse_args()

    url = os.environ["SUPABASE_URL"]
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY or SUPABASE_KEY is required")
    db = create_client(url, key)

    rows = load_rows(db)
    by_id = {str(row.get("id")): row for row in rows}
    plan = candidates(rows)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "venue", "kept_id", "kept_title", "removed_id", "removed_title", "kept_source_id", "removed_source_id", "event_url", "reason"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(plan)

    print(f"Rows inspected: {len(rows)}")
    print(f"Conservative duplicate candidates: {len(plan)}")
    print(f"Audit file: {output}")

    if not args.apply:
        print("READ-ONLY audit: no event rows changed.")
        return

    if not args.backup_manifest:
        raise RuntimeError("--apply requires --backup-manifest")
    manifest = validate_manifest(args.backup_manifest)
    print(f"Backup verified: {args.backup_manifest} ({manifest['row_count']} rows)")

    applied_log = output.with_name("duplicate_merges_applied.csv")
    applied = []
    for item in plan:
        keep = by_id[str(item["kept_id"])]
        remove = by_id[str(item["removed_id"])]
        patch = merged_patch(keep, remove)
        if patch:
            db.table("collected_events").update(patch).eq("id", keep["id"]).execute()
        db.table("collected_events").delete().eq("id", remove["id"]).execute()
        applied.append(item)

    with applied_log.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(applied)
    print(f"Applied merges: {len(applied)}")
    print(f"Permanent merge log: {applied_log}")


if __name__ == "__main__":
    main()
