"""Read-only Matalan trial through normal rules and independent verification."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ENABLE_PAID_AI"] = "false"
os.environ["DRY_RUN"] = "true"
import deals_worker as worker
from deals_matalan import SOURCE_URL, fetch_matalan
from deals_verification import verify_kept


def deny_database(*args, **kwargs):
    raise RuntimeError("Read-only trial must never access the database")


def main():
    worker.sb = deny_database
    status, raw, info = fetch_matalan({"url": SOURCE_URL})
    taxonomy = json.loads((ROOT / "artefacts/data/sprint7-deals-baseline.json").read_text(encoding="utf-8"))["taxonomy"]
    rows = [worker.normalise(r) for r in raw]
    for row in rows:
        reason = worker.validate_deal(row)
        if reason:worker.reject(row, reason)
    worker.process_items(rows, worker.compile_items(taxonomy), [], None)
    verify_kept(rows, worker.reject)
    output = ROOT / "review/sprint7-uniform-trial.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"source": SOURCE_URL, "status": status, "info": info, "published": False, "owner_accepted": False, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "candidates": len(rows), "kept": sum(r.get("decision")=="kept" for r in rows), "rejections": [r.get("reason") for r in rows if r.get("decision")!="kept"], "database_writes":0,"model_calls":0}))


if __name__ == '__main__':main()
