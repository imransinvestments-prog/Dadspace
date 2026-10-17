import copy
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
import original_content_worker as worker

def draft():
    return {"title": "An easy drawing game for today", "summary": "Turn a quiet moment together into a playful drawing adventure with a simple shared story.", "sections": [{"heading": "Start together", "paragraphs": ["Try " + "a shared drawing idea " * 35]}, {"heading": "Make it your own", "paragraphs": ["Then " + "take turns adding details " * 10]}]}

class OriginalContentTests(unittest.TestCase):
    def test_friday_in_both_seasons(self):
        for value in ("2026-10-09T06:17:00+00:00", "2026-12-04T07:17:00+00:00"):
            self.assertEqual([s[0] for s in worker.due_slots(datetime.fromisoformat(value))], ["daily", "weekly"])
    def test_no_early_or_midweek_guide(self):
        self.assertEqual(worker.due_slots(datetime(2026, 12, 4, 6, tzinfo=timezone.utc)), [])
        self.assertEqual([s[0] for s in worker.due_slots(datetime(2026, 10, 10, 8, tzinfo=timezone.utc))], ["daily"])
        for minute in (0,16):
            self.assertEqual(worker.due_slots(datetime(2026,12,4,7,minute,tzinfo=timezone.utc)),[])
    def test_validation(self):
        self.assertEqual(worker.validate(draft(), "daily")["title"], draft()["title"])
        for change in ({"title": "short"}, {"sections": []}, {"summary": "https://example.com " * 5}):
            with self.assertRaises(ValueError):
                worker.validate({**draft(), **change}, "daily")
        with self.assertRaises(ValueError):
            worker.validate(draft(), "daily", [draft()["title"].upper()])
        with self.assertRaises(ValueError):
            worker.validate(draft(), "weekly")
    def test_existing_slot_never_calls_model(self):
        env = {"SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test", "GEMINI_API_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "due_slots", return_value=[("daily", datetime.now().date())]), patch.object(worker, "api", side_effect=[[], [{"slug": "exists"}]]), patch.object(worker, "gemini") as generate:
            worker.run()
            generate.assert_not_called()
    def test_rejection_does_not_write(self):
        env = {"SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test", "GEMINI_API_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "due_slots", return_value=[("daily", datetime.now().date())]), patch.object(worker, "api", side_effect=[[], []]) as api, patch.object(worker, "gemini", side_effect=[draft(), {"approved": False, "reason": "unsafe"}] * 2) as generate:
            with self.assertRaises(ValueError): worker.run()
            self.assertEqual(api.call_count, 2)
            self.assertEqual(generate.call_count, 4)
    def test_editor_feedback_repairs_once_before_publication(self):
        env = {"SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test", "GEMINI_API_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "due_slots", return_value=[("daily", datetime.now().date())]), patch.object(worker, "api", side_effect=[[], [], [{}]]) as api, patch.object(worker, "gemini", side_effect=[draft(), {"approved": False, "reason": "add supervision"}, draft(), {"approved": True, "reason": "ok"}]) as generate:
            worker.run()
            self.assertEqual(api.call_count, 3)
            self.assertIn("add supervision", generate.call_args_list[2].args[0])
    def test_invalid_word_count_is_revised_before_review(self):
        invalid = draft()
        invalid['sections'][0]['paragraphs'] = ['A short drawing idea to share together.']
        with patch.object(worker, "gemini", side_effect=[invalid, draft(), {"approved": True}]) as generate:
            self.assertEqual(worker.reviewed_post('brief', 'daily', []), draft())
            self.assertEqual(generate.call_count, 3)
            self.assertIn('Invalid word count', generate.call_args_list[1].args[0])
    def test_remote_denial_is_not_retried(self):
        with patch.object(worker, "gemini", side_effect=RuntimeError('Remote service returned HTTP 403')) as generate:
            with self.assertRaises(RuntimeError):
                worker.reviewed_post('brief', 'daily', [])
            generate.assert_called_once()
    def test_dry_run_does_not_write(self):
        env = {"SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test", "GEMINI_API_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "due_slots", return_value=[("daily", datetime.now().date())]), patch.object(worker, "api", side_effect=[[], []]) as api, patch.object(worker, "gemini", side_effect=[draft(), {"approved": True, "reason": "ok"}]):
            worker.run(dry_run=True)
            self.assertEqual(api.call_count, 2)

    def test_future_rejected_drafts_are_retained_with_unknown_billing(self):
        context = {"cadence": "daily", "slot_date": "2026-10-17", "dry_run": True, "run_id": "123", "model_calls": 0}
        env = {"ORIGINAL_CONTENT_RETAIN_EVIDENCE": "true", "SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "api") as api, patch.object(worker, "gemini", side_effect=[draft(), {"approved": False, "reason": "needs supervision"}] * 2):
            with self.assertRaises(ValueError): worker.reviewed_post("brief", "daily", [], context)
            records = [call.args[2][0] for call in api.call_args_list]
            self.assertEqual([r["stage"] for r in records], ["draft", "editor_rejected", "draft", "editor_rejected"])
            self.assertEqual(records[-1]["model_calls"], 4)
            self.assertIsNone(records[-1]["input_tokens"])
            self.assertIsNone(records[-1]["output_tokens"])
            self.assertTrue(records[-1]["draft"])

    def test_evidence_failure_stops_before_editor_or_publication(self):
        context = {"cadence": "daily", "slot_date": "2026-10-17", "dry_run": False, "run_id": "123", "model_calls": 0}
        with patch.dict(worker.os.environ, {"ORIGINAL_CONTENT_RETAIN_EVIDENCE": "true", "SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test"}), patch.object(worker, "api", side_effect=RuntimeError("store unavailable")), patch.object(worker, "gemini", return_value=draft()) as generate:
            with self.assertRaises(RuntimeError): worker.reviewed_post("brief", "daily", [], context)
            generate.assert_called_once()

    def test_historical_slot_retry_cannot_generate(self):
        env = {"SUPABASE_URL": "https://example.com", "SUPABASE_SERVICE_KEY": "test", "GEMINI_API_KEY": "test"}
        with patch.dict(worker.os.environ, env), patch.object(worker, "api", return_value=[]), patch.object(worker, "gemini") as generate:
            with self.assertRaises(ValueError): worker.run(slot_date="2000-01-01")
            generate.assert_not_called()

if __name__ == "__main__": unittest.main()
