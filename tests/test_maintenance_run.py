import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("maintenance_run", Path(__file__).resolve().parents[1] / "scripts/maintenance-run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ID = "22222222-2222-4222-8222-222222222222"
ENV = {"MAINTENANCE_REQUEST": ID, "GITHUB_RUN_ID": "123", "MAINTENANCE_DRY_RUN": "true", "MAINTENANCE_SOURCE": "1", "MAINTENANCE_MAX_NEW": "10", "MAINTENANCE_MAX_MINUTES": "5"}
def claim():
    return {"family": "news", "action": "retry", "run_id": None, "status": "submitted", "before_state": {"inputs": {"source_id": "1", "max_new": "10", "max_minutes": "5", "dry_run": "true"}}}
class MaintenanceRunnerTests(unittest.TestCase):
    def test_exact_claim_consumed_once(self):
        with patch.dict(runner.os.environ, ENV), patch.object(runner, "request", side_effect=[[claim()], [{"id": ID}]]) as remote:
            runner.run("start", "news")
            self.assertIn("run_id=is.null", remote.call_args.args[1])
            self.assertEqual(remote.call_args.args[2]["run_id"], 123)
    def test_changed_mode_or_budget_never_claims(self):
        for change in ({"MAINTENANCE_DRY_RUN": "false"}, {"MAINTENANCE_MAX_NEW": "100"}, {"MAINTENANCE_SOURCE": "2"}):
            with patch.dict(runner.os.environ, {**ENV, **change}), patch.object(runner, "request", return_value=[claim()]) as remote:
                with self.assertRaises(ValueError): runner.run("start", "news")
                self.assertEqual(remote.call_count, 1)
    def test_race_loser_cannot_repeat_run(self):
        with patch.dict(runner.os.environ, ENV), patch.object(runner, "request", side_effect=[[claim()], []]):
            with self.assertRaises(ValueError): runner.run("start", "news")
    def test_failed_start_does_not_clear_someone_elses_run(self):
        row = {**claim(), "run_id": 456}
        with patch.dict(runner.os.environ, ENV), patch.object(runner, "request", return_value=[row]) as remote:
            runner.run("finish", "news")
            self.assertEqual(remote.call_count, 1)
if __name__ == "__main__": unittest.main()
