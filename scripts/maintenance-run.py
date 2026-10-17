"""Bind an Operations dispatch to its exact claimed runner inputs. No secret output."""
import json
import os
import re
import sys
from urllib.request import Request, urlopen

def request(method, query, body=None):
    key = os.environ["SUPABASE_SERVICE_KEY"]
    req = Request(os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/operations_maintenance_audit?" + query,
                  method=method, headers={"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=representation"},
                  data=json.dumps(body).encode() if body is not None else None)
    with urlopen(req, timeout=20) as response:
        raw = response.read()
        return json.loads(raw) if raw else []

def run(phase, family):
    identity = os.environ.get("MAINTENANCE_REQUEST", "")
    if not identity:
        return  # Existing scheduled/manual route retains its independent policy.
    if not re.fullmatch(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", identity):
        raise ValueError("Invalid maintenance request")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not run_id.isdigit() or family not in ("news", "originals"):
        raise ValueError("Invalid runner context")
    rows = request("GET", f"id=eq.{identity}&select=*")
    if len(rows) != 1 or rows[0]["family"] != family or rows[0]["action"] != "retry":
        raise ValueError("Maintenance claim unavailable")
    row = rows[0]
    if phase == "start":
        if row["status"] not in ("claimed", "submitted", "uncertain") or row.get("run_id") not in (None, int(run_id)):
            raise ValueError("Claim already consumed")
        inputs = row["before_state"]["inputs"]
        if str(inputs["dry_run"]).lower() != os.environ.get("MAINTENANCE_DRY_RUN"):
            raise ValueError("Dry/live scope changed")
        if family == "news":
            for key, env in (("source_id", "MAINTENANCE_SOURCE"), ("max_new", "MAINTENANCE_MAX_NEW"), ("max_minutes", "MAINTENANCE_MAX_MINUTES")):
                if inputs[key] != os.environ.get(env):
                    raise ValueError("Bounded source/cap changed")
            if inputs["max_new"] != "10" or inputs["max_minutes"] != "5":
                raise ValueError("Unsupported budget")
        else:
            if inputs["cadence"] != os.environ.get("MAINTENANCE_CADENCE") or inputs["slot_date"] != os.environ.get("MAINTENANCE_SLOT_DATE"):
                raise ValueError("Slot scope changed")
        # CAS run ownership: two dispatches cannot both consume the same claim.
        result = request("PATCH", f"id=eq.{identity}&run_id=is.null&status=in.(claimed,submitted,uncertain)", {"status": "submitted", "run_id": int(run_id)})
        if len(result) != 1:
            raise ValueError("Claim consumed; do not repeat a paid run")
    elif phase == "finish":
        if row.get("run_id") != int(run_id):
            return  # Failed start never clears another runner's claim.
        result = request("PATCH", f"id=eq.{identity}&run_id=eq.{run_id}&status=eq.submitted", {
            "status": "reconciled", "after_state": {**row["after_state"], "runner_result": os.environ.get("MAINTENANCE_RESULT", "unknown")}})
        if len(result) != 1:
            raise ValueError("Result needs manual reconciliation")
    else:
        raise ValueError("Invalid phase")

if __name__ == "__main__":
    try:
        run(*sys.argv[1:])
    except Exception:
        raise SystemExit("Maintenance claim/result could not be verified. No automatic retry; inspect the audit and workflow.")
