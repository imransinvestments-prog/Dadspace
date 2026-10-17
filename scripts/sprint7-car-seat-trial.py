"""Bounded public merchant trial. No database, AI, source or membership writes.

Run from the app root. Output stays under ignored review/; promoting an exact
snapshot into the protected owner review pack is a separate reviewed step.
"""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ENABLE_PAID_AI"] = "false"
os.environ["DRY_RUN"] = "true"
import deals_worker as worker
from deals_shopify import fetch_shopify, verify_shopify

SOURCE = "https://www.naturalbabyshower.co.uk/collections/sale-car-seats.atom"


def deny_database(*args, **kwargs):
    raise RuntimeError("This trial must never access the database")


def main():
    worker.sb = deny_database
    status, raw, info = fetch_shopify({"url": SOURCE})
    taxonomy = json.loads((ROOT / "artefacts/data/sprint7-deals-baseline.json").read_text(encoding="utf-8"))["taxonomy"]
    rows = [worker.normalise(row) for row in raw]
    for row in rows:
        reason = worker.validate_deal(row)
        if reason:
            worker.reject(row, reason)
    worker.process_items(rows, worker.compile_items(taxonomy), [], None)
    for row in rows:
        if row.get("decision") == "kept":
            reason, basis = verify_shopify(row)
            if reason:
                worker.reject(row, reason)
            else:
                row["verified_basis"] = basis
    output = ROOT / "review/sprint7-car-seat-trial.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"source": SOURCE, "status": status, "info": info, "published": False, "owner_accepted": False, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "candidates": len(rows), "kept": sum(row.get("decision") == "kept" for row in rows), "database_writes": 0, "model_calls": 0}))


if __name__ == "__main__":
    main()
