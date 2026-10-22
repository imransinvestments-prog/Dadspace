import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_context
import worker


def usage(name, status, message=None):
    row = {"source": name, "status": status}
    if message:
        row["message"] = message
    return row


class RunContextTests(unittest.TestCase):
    def test_github_identity_is_recorded_for_matching_runs(self):
        env = {"GITHUB_RUN_ID": "39681099718", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "4a2557b",
               "GITHUB_EVENT_NAME": "schedule", "GITHUB_WORKFLOW": "Dadspace workers", "GITHUB_JOB": "collect"}
        with patch.dict(os.environ, env):
            details = run_context.run_details("ok")
        self.assertEqual(details["github"]["run_id"], "39681099718")
        self.assertEqual(details["github"]["event"], "schedule")
        self.assertEqual((details["reasons"], details["failed_sources"], details["failed_source_count"]), ([], [], 0))

    def test_unknown_status_and_long_failure_lists_are_bounded(self):
        with self.assertRaises(ValueError):
            run_context.run_details("partial")
        details = run_context.run_details("degraded", failed=["x" * 500] * 40)
        self.assertEqual(len(details["failed_sources"]), run_context.MAX_LISTED)
        self.assertEqual(details["failed_source_count"], 40)
        self.assertEqual(len(details["failed_sources"][0]), 200)


class EventsRunEvidenceTests(unittest.TestCase):
    def evidence(self, rows, fatal=None):
        return worker.run_evidence(rows, {"ok": 1}, configured=len(rows), processed=len(rows),
                                   stopped_early=False, fatal=fatal, zero_event_sources=[], run_stats={"kept": 3})

    def test_healthy_and_robots_excluded_sources_are_not_failures(self):
        details = self.evidence([usage("Library", "ok"), usage("Same page", "unchanged"),
                                 usage("Empty", "ok_zero"), usage("Blocked", "skipped_robots", "robots.txt disallows")])
        self.assertEqual(details["status"], "ok")
        self.assertEqual(details["robots_excluded"], ["Blocked"])
        self.assertEqual(details["failed_sources"], [])

    def test_failed_sources_name_the_route_and_error(self):
        details = self.evidence([usage("Library", "ok"), usage("Council", "failed_timeout", "read timed out")])
        self.assertEqual(details["status"], "degraded")
        self.assertEqual(details["reasons"], ["1 source(s) failed"])
        self.assertEqual(details["failed_sources"], ["Council: failed_timeout: read timed out"])

    def test_fatal_error_marks_the_run_failed(self):
        details = self.evidence([usage("Library", "ok")], fatal=RuntimeError("Gemini quota exhausted"))
        self.assertEqual(details["status"], "failed")
        self.assertEqual(details["reasons"], ["fatal: RuntimeError: Gemini quota exhausted"])


if __name__ == "__main__":
    unittest.main()
