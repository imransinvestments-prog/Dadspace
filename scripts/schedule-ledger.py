"""Expected-slot ledger for scheduled workflows (#124 / #125 evidence).

For every slot a workflow's cron promises, find the scheduled run GitHub actually
created and report how late it was dispatched, when it finished and which jobs
failed. A slot with no run before the next slot is MISSING, never assumed run.
Uses the public Actions API; set GITHUB_TOKEN to raise the rate limit.

  python scripts/schedule-ledger.py --days 5
  python scripts/schedule-ledger.py --days 7 --json ledger.json
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = "imransinvestments-prog/Dadspace"
WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
DISPATCH_MINUTES, COMPLETION_MINUTES = 60, 240  # Owner-approved deadlines, 17 Oct 2026 (#124).


def schedules(directory=WORKFLOWS):
    """{workflow file: [(minute, hours, timezone)]}. Only 'M H[,H] * * *' is supported."""
    found = {}
    for path in sorted(directory.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"cron:\s*[\"']([^\"']+)[\"'](?:\s*\n\s*timezone:\s*([\w/]+))?", text):
            fields = match.group(1).split()
            if len(fields) != 5 or fields[2:] != ["*", "*", "*"] or not fields[0].isdigit():
                raise ValueError(f"{path.name}: unsupported cron {match.group(1)!r}")
            found.setdefault(path.name, []).append(
                (int(fields[0]), [int(h) for h in fields[1].split(",")], match.group(2) or "UTC"))
    return found


def expected_slots(rules, start, end):
    slots = []
    for minute, hours, zone in rules:
        tz = ZoneInfo(zone)
        day = start.astimezone(tz).date() - dt.timedelta(days=1)
        while day <= end.astimezone(tz).date():
            for hour in hours:
                slot = dt.datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz).astimezone(dt.timezone.utc)
                if start <= slot <= end:
                    slots.append(slot)
            day += dt.timedelta(days=1)
    return sorted(slots)


def parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def ledger(slots, runs, jobs_for, now):
    """runs: scheduled runs of one workflow. jobs_for(run) -> list of job dicts."""
    runs = sorted(runs, key=lambda r: r["created_at"])
    rows, used = [], set()
    for i, slot in enumerate(slots):
        until = slots[i + 1] if i + 1 < len(slots) else now
        run = next((r for r in runs if r["id"] not in used and slot <= parse(r["created_at"]) < until), None)
        if run is None:
            overdue = (now - slot).total_seconds() / 60 > DISPATCH_MINUTES
            rows.append({"slot": slot.isoformat(), "state": "MISSING" if overdue else "PENDING"})
            continue
        used.add(run["id"])
        delay = round((parse(run["created_at"]) - slot).total_seconds() / 60)
        finished = parse(run["updated_at"]) if run["status"] == "completed" else None
        failed = [j["name"] for j in jobs_for(run) if j.get("conclusion") in ("failure", "timed_out", "cancelled")]
        state = ("FAILED" if run.get("conclusion") not in (None, "success") else
                 "LATE" if delay > DISPATCH_MINUTES else "OK")
        rows.append({"slot": slot.isoformat(), "state": state, "run_id": run["id"], "dispatch_delay_min": delay,
                     "completed_min": round((finished - slot).total_seconds() / 60) if finished else None,
                     "conclusion": run.get("conclusion"), "failed_jobs": failed, "url": run["html_url"]})
    return rows


def github(path):
    request = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "dadspace-schedule-ledger"})
    if os.environ.get("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--json", help="also write the ledger to this file")
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=args.days)
    report = {"generated_at": now.isoformat(), "days": args.days,
              "thresholds_min": {"dispatch": DISPATCH_MINUTES, "completion": COMPLETION_MINUTES}, "workflows": {}}
    for workflow, rules in schedules().items():
        runs = github(f"/actions/workflows/{workflow}/runs?event=schedule&per_page=100&created=>={start.date().isoformat()}")["workflow_runs"]
        jobs = lambda run: github(f"/actions/runs/{run['id']}/jobs?per_page=100")["jobs"] if run.get("conclusion") not in (None, "success") else []
        rows = ledger(expected_slots(rules, start, now), runs, jobs, now)
        report["workflows"][workflow] = rows
        delays = [r["dispatch_delay_min"] for r in rows if "dispatch_delay_min" in r]
        print(f"\n{workflow}: {len(rows)} slots | " + ", ".join(f"{s}={sum(r['state'] == s for r in rows)}"
              for s in ("OK", "LATE", "FAILED", "MISSING", "PENDING")) +
              (f" | median dispatch delay {sorted(delays)[len(delays) // 2]} min" if delays else ""))
        for r in rows:
            local = parse(r["slot"]).astimezone(ZoneInfo("Europe/London")).strftime("%a %d %b %H:%M")
            extra = (f"+{r['dispatch_delay_min']}m dispatch" + (f", done +{r['completed_min']}m" if r.get("completed_min") is not None else "")
                     + (f", failed: {', '.join(r['failed_jobs'])}" if r.get("failed_jobs") else "")) if "run_id" in r else ""
            print(f"  {local}  {r['state']:<8} {extra}")
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
