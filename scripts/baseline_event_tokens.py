#!/usr/bin/env python3
"""Run a fixed, read-only Dadspace event-collector baseline and print Gemini usage.

This deliberately bypasses each source's saved page hash in memory so the source
is fully re-read. It never writes source hashes, events, or any database rows.
The selected source IDs are written to JSON so the exact same set can be rerun
after the Events/Activities split.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from supabase import create_client

import events_worker
import worker as base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", required=True, help="Comma-separated source categories")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--label", required=True)
    parser.add_argument("--source-ids", default="", help="Optional comma-separated IDs to rerun exactly")
    args = parser.parse_args()

    events_worker.install_quality_rules()

    url = os.environ["SUPABASE_URL"]
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY or SUPABASE_KEY is required")
    db = create_client(url, key)

    categories = [x.strip() for x in args.categories.split(",") if x.strip()]
    requested_ids = [x.strip() for x in args.source_ids.split(",") if x.strip()]

    query = db.table("sources").select("*").eq("active", True)
    if categories:
        query = query.in_("category", categories)
    rows = query.order("id").execute().data or []

    if requested_ids:
        wanted = set(requested_ids)
        rows = [r for r in rows if str(r.get("id")) in wanted]
        order = {value: index for index, value in enumerate(requested_ids)}
        rows.sort(key=lambda r: order.get(str(r.get("id")), 10**9))
    else:
        rows = rows[: max(1, args.count)]

    if not rows:
        raise RuntimeError("No active sources matched the baseline selection")

    sources = []
    for row in rows:
        copy = dict(row)
        copy["last_hash"] = None
        copy["last_success_at"] = None
        sources.append(copy)

    extract = base.make_gemini_caller()
    today = base.today_uk()
    source_results = []

    print(f"BASELINE_LABEL={args.label}")
    print("BASELINE_SOURCE_IDS=" + ",".join(str(s.get("id")) for s in sources))
    print(f"BASELINE_SOURCE_COUNT={len(sources)}")

    for source in sources:
        status, event_rows, _new_hash, message, stats = base.process_source(source, extract, today)
        source_results.append({
            "id": source.get("id"),
            "name": source.get("name"),
            "category": source.get("category"),
            "status": status,
            "rows": len(event_rows),
            "message": message,
            "stats": stats,
        })
        print(f"SOURCE {source.get('id')} | {source.get('name')} | {status} | rows={len(event_rows)}")

    metrics = dict(getattr(extract, "metrics", {}))
    summary = {
        "label": args.label,
        "today_uk": today.isoformat(),
        "fetch_engine": base.FETCH_ENGINE,
        "categories": categories,
        "source_ids": [str(s.get("id")) for s in sources],
        "sources": source_results,
        "gemini": metrics,
        "read_only": True,
        "forced_reread": True,
    }

    out = Path("baseline-review")
    out.mkdir(exist_ok=True)
    path = out / f"{args.label}.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("GEMINI_API_ATTEMPTS=" + str(metrics.get("api_attempts", 0)))
    print("GEMINI_PROMPT_TOKENS=" + str(metrics.get("prompt_tokens", 0)))
    print("GEMINI_OUTPUT_TOKENS=" + str(metrics.get("output_tokens", 0)))
    print("GEMINI_THINKING_TOKENS=" + str(metrics.get("thinking_tokens", 0)))
    print("GEMINI_TOTAL_TOKENS=" + str(metrics.get("total_tokens", 0)))
    print(f"BASELINE_JSON={path}")


if __name__ == "__main__":
    main()
