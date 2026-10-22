import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "schedule-ledger.py"
spec = importlib.util.spec_from_file_location("schedule_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)
UTC = dt.timezone.utc


def at(text):
    return dt.datetime.fromisoformat(text).replace(tzinfo=UTC)


def run(run_id, created, conclusion="success", updated=None, event="schedule", title="Dadspace workers"):
    return {"id": run_id, "created_at": created, "updated_at": updated or created, "status": "completed",
            "conclusion": conclusion, "html_url": f"https://github.com/runs/{run_id}", "event": event, "display_title": title}


class ScheduleLedgerTests(unittest.TestCase):
    def test_reads_cron_and_timezone_and_rejects_unsupported_shapes(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "w.yml").write_text('on:\n  schedule:\n    - cron: "17 7,19 * * *"\n      timezone: Europe/London\n')
            self.assertEqual(ledger.schedules(Path(directory)), {"w.yml": [(17, [7, 19], "Europe/London")]})
            Path(directory, "x.yml").write_text("on:\n  schedule:\n    - cron: '*/5 * * * 1'\n")
            with self.assertRaises(ValueError):
                ledger.schedules(Path(directory))

    def test_london_slots_follow_the_clock_change(self):
        rules = [(17, [7], "Europe/London")]
        slots = ledger.expected_slots(rules, at("2026-10-24T00:00"), at("2026-10-26T23:00"))
        # BST until 25 Oct 2026 01:00 UTC, then GMT.
        self.assertEqual(slots, [at("2026-10-24T06:17"), at("2026-10-25T07:17"), at("2026-10-26T07:17")])

    def test_matches_each_slot_once_and_reports_late_failed_missing_and_pending(self):
        slots = [at("2026-10-21T06:17"), at("2026-10-21T08:17"), at("2026-10-21T18:17"), at("2026-10-21T20:17")]
        runs = [run(1, "2026-10-21T11:48:00Z", updated="2026-10-21T11:50:00Z"),
                run(2, "2026-10-21T18:40:00Z", "failure")]
        jobs = lambda r: [{"name": "deals / collect", "conclusion": "failure"}, {"name": "news / news", "conclusion": "success"}]
        rows = ledger.ledger(slots, runs, jobs, now=at("2026-10-21T20:30"))
        self.assertEqual([r["state"] for r in rows], ["MISSING", "LATE", "FAILED", "PENDING"])
        # A late run belongs to the slot it followed, not to an earlier missed one.
        self.assertEqual((rows[1]["run_id"], rows[1]["dispatch_delay_min"], rows[1]["completed_min"]), (1, 211, 213))
        self.assertEqual((rows[2]["dispatch_delay_min"], rows[2]["failed_jobs"]), (23, ["deals / collect"]))

    def test_timer_dispatch_fills_the_slot_and_late_or_manual_runs_do_not(self):
        runs = [run(10, "2026-10-23T06:18:00Z", event="workflow_dispatch", title="Dadspace workers timer slot 2026-10-23T07:17"),
                run(11, "2026-10-23T09:00:00Z", event="workflow_dispatch", title="Dadspace workers"),  # someone's manual run
                run(12, "2026-10-23T11:40:00Z")]  # GitHub's late scheduled duplicate
        rows = ledger.ledger([at("2026-10-23T06:17")], runs, lambda r: [], now=at("2026-10-23T12:00"))
        self.assertEqual((rows[0]["state"], rows[0]["run_id"], rows[0]["via"], rows[0]["dispatch_delay_min"]), ("OK", 10, "timer", 1))
        manual_only = ledger.ledger([at("2026-10-23T06:17")], [runs[1]], lambda r: [], now=at("2026-10-23T12:00"))
        self.assertEqual(manual_only[0]["state"], "MISSING", "a manual run is not evidence for a scheduled slot")

    def test_on_time_run_is_ok(self):
        rows = ledger.ledger([at("2026-10-22T06:17")], [run(3, "2026-10-22T06:40:00Z")], lambda r: [], now=at("2026-10-22T09:00"))
        self.assertEqual((rows[0]["state"], rows[0]["dispatch_delay_min"]), ("OK", 23))


if __name__ == "__main__":
    unittest.main()
