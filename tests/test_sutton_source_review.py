import copy
import unittest
from scripts.validate_sutton_sources import SOURCES, acceptance_errors


def successful_results():
    return [dict(event_id=event_id, attempt=attempt, status='ok',
                 rows=[dict(title=name, dedupe_key=event_id, time_text='10:00 AM - 11:00 AM',
                            description='London Borough of Sutton only' if event_id == '374590' else 'Family programme',
                            last_seen_at=str(attempt))],
                 stats={'gemini_logical_calls': 0})
            for name, event_id in SOURCES for attempt in (1, 2)]


class SuttonReviewTests(unittest.TestCase):
    def test_only_verification_timestamps_can_change(self):
        results = successful_results()
        self.assertEqual(acceptance_errors(results), [])
        results[1]['rows'][0]['time_text'] = '10:00 AM - 11:30 AM'
        self.assertTrue(acceptance_errors(results))

    def test_one_working_source_cannot_mask_an_empty_source(self):
        results = successful_results()
        results[-1]['status'] = 'ok_zero'
        results[-1]['rows'] = []
        self.assertTrue(acceptance_errors(results))

    def test_resident_requirement_is_required_even_if_both_passes_omit_it(self):
        results = successful_results()
        for result in results:
            if result['event_id'] == '374590':
                result['rows'][0]['description'] = 'Family programme'
        self.assertTrue(acceptance_errors(results))

    def test_duplicate_attempts_and_duplicate_programmes_fail(self):
        results = successful_results()
        results[1]['attempt'] = 1
        self.assertTrue(acceptance_errors(results))
        results = successful_results()
        for result in results[:4]:
            result['rows'][0]['dedupe_key'] = 'same'
        self.assertTrue(acceptance_errors(results))

    def test_missing_identity_or_paid_calls_fail(self):
        for change in ('identity', 'paid'):
            results = successful_results()
            if change == 'identity':
                results[0]['rows'][0]['dedupe_key'] = ''
            else:
                results[0]['stats']['gemini_logical_calls'] = 1
            self.assertTrue(acceptance_errors(results))

