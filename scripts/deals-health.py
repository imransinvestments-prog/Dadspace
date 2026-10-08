"""Bounded, read-only feed audit. Uses the exact public Node selector; no AI calls."""
import csv
import json
import os
import pathlib
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import deals_worker as worker
from deals_worker_db import read_all


def age_hours(value, now):
    try:
        return (now - datetime.fromisoformat(value.replace("Z", "+00:00"))).total_seconds() / 3600
    except (ValueError, TypeError, AttributeError):
        return None


def main():
    now = datetime.now(timezone.utc)
    taxonomy = read_all("parent_discount_items")
    sources = read_all("deal_sources")
    rows = read_all("deals")
    runs = worker.sb("GET", "pipeline_runs", params={"select": "*", "worker": "eq.deals", "ran_at": "gte."+(now-timedelta(days=7)).isoformat(), "order": "ran_at.desc", "limit": 1000}) or []
    by_id = {t["id"]: t for t in taxonomy}
    candidates = []
    for row in rows:
        item = by_id.get(row.get("item_id"))
        if item and item["active"]:
            candidates.append({**row, "display_group": item["display_group"], "matched_item": item["item_or_service"], "deal_type": item["deal_type"], "equivalent_item_id": item.get("equivalent_item_id")})
    out = ROOT / "review"
    out.mkdir(exist_ok=True)
    snapshot = out / "display-candidates.json"
    snapshot.write_text(json.dumps(candidates), encoding="utf-8")
    result = subprocess.run(["node", str(ROOT/"scripts/deals-published.mjs"), str(snapshot)], check=True, capture_output=True, text=True)
    published = json.loads(result.stdout)
    (out/"published.json").write_text(json.dumps(published, indent=2), encoding="utf-8")
    subprocess.run(["node", str(ROOT/"scripts/export-deals-review.mjs"), str(snapshot), str(out)], check=True)
    active_sources = [s for s in sources if s["active"]]
    alerts = []
    for source in active_sources:
        age = age_hours(source.get("last_checked_at"), now)
        if age is None or age > 54:
            alerts.append(f"Missed refresh: {source['name']}")
        if source.get("last_status") not in {"ok", "empty"}:
            alerts.append(f"Source failure: {source['name']} ({source.get('last_status')})")
        if not source.get("last_counts", {}).get("verified", 0):
            alerts.append(f"No verified offers on latest fetch: {source['name']}")
    groups = Counter(d["display_group"] for d in published)
    merchants = Counter(d["retailer"] for d in published)
    source_map = {s["id"]: s for s in sources}
    from urllib.parse import urlsplit
    providers = Counter(urlsplit(source_map.get(d.get("source_id"), {}).get("url", "")).hostname for d in published)
    missing_groups = [group for group in worker.GROUPS if not groups[group]]
    if missing_groups:
        alerts.append(f"Coverage shortfall: {len(groups)}/{len(worker.GROUPS)} target groups; missing: {', '.join(missing_groups)}")
    if published and max(merchants.values()) > len(published)/2:
        alerts.append("Merchant concentration above 50%")
    report = {"checked_at": now.isoformat(), "published": len(published), "by_group": groups, "by_merchant": merchants, "by_provider": providers, "by_item": Counter(d.get("item_id") for d in published), "stale_hidden": sum(d["status"] == "live" and (age_hours(d.get("last_seen"), now) or 0) > 72 for d in rows), "alerts": alerts, "sources": active_sources, "observation_days": 7, "runs": [{"id":r["id"], "ran_at":r["ran_at"], "dry_run":r["dry_run"], "details":r["details"]} for r in runs]}
    (out/"feed-health.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    counts = Counter(d.get("item_id") for d in published)
    with (out/"taxonomy-coverage.csv").open("w", newline="", encoding="utf-8") as f:
        columns = ["id", "item_or_service", "category", "subcategory", "active", "inactive_reason", "display_group", "uk_terms", "tier", "deal_type", "value_band", "needs_child_evidence", "equivalent_item_id", "published", "coverage"]
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for item in taxonomy:
            writer.writerow({**item, "published": counts[item["id"]], "coverage": "current offer" if counts[item["id"]] else "no verified supply; discovery/classifier gap to review" if item["active"] else "inactive: "+str(item["inactive_reason"])})
    summary = f"### Deals feed health\n\n{len(published)} published offers; {len(groups)} groups; {len(providers)} providers.\n\n" + "\n".join("- "+a for a in alerts) + "\n\nHuman quality labels and seven-day observation remain required. See the deals-review artifact.\n"
    (out/"feed-health.md").write_text(summary, encoding="utf-8")
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    print(summary)


if __name__ == "__main__":
    main()
