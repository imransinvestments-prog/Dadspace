#!/usr/bin/env python3
"""Normal worker dry run for reviewed sources; optionally register inactive.

No live deal writes or activation. Uses canonical database taxonomy and exclusions.
"""
import argparse
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deals_worker as worker
import deals_worker_db as db
from deals_shopify import SHOPS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true", help="Register missing sources inactive after successful dry run")
    args = parser.parse_args()
    worker.DRY_RUN = True
    worker.ENABLE_PAID_AI = False
    db.configure_worker()
    sources = [{"id": -index, "name": "Shopify pilot — " + shop["name"],
                "source_type": "direct", "url": url, "active": True}
               for index, (url, shop) in enumerate(SHOPS.items(), 1)]
    db.get_all_sources = lambda: sources
    result = db.run()
    if result or not args.register:
        return result
    existing = worker.sb("GET", "deal_sources", params={"select": "id,url,active"}) or []
    for source in sources:
        matches = [row for row in existing if row["url"] == source["url"]]
        if len(matches) > 1:
            raise RuntimeError("Duplicate Shopify source registration needs review")
        if matches:
            worker.log(f"Already registered: {source['name']}; activation unchanged")
            continue
        worker.sb("POST", "deal_sources", json={"name": source["name"], "url": source["url"],
                  "source_type": "direct", "active": False,
                  "notes": "Reviewed Shopify public Atom collection; bounded pilot; inactive pending useful value evidence and review. No AI."})
        check = worker.sb("GET", "deal_sources", params={"select": "id,url,active", "url": "eq." + source["url"]}) or []
        if len(check) != 1 or check[0]["active"] is not False:
            raise RuntimeError("Inactive registration readback failed")
        worker.log(f"Registered inactive and confirmed: {source['name']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("Shopify pilot failed; check source reports and database access. No credentials logged.")
        sys.exit(1)
