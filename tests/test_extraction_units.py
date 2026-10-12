import datetime as dt
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from extraction_cache import ResultCache
from structured_events import complete_events
import worker


class ExtractionUnitsTests(unittest.TestCase):
    today = dt.date(2026, 10, 12)
    source = {'id': 'a', 'name': 'Museum', 'url': 'https://example.org/events', 'extraction_mode': 'per_page'}

    def documents(self):
        return [(self.source['url'] + suffix, '<main><h1>Family ' + title + '</h1><p>' +
                 'Children welcome October 15 2026 2pm. ' * 8 + '</p></main>')
                for suffix, title in [('/one', 'pottery'), ('/two', 'painting')]]

    def test_only_changed_detail_calls_again_and_hits_do_not_extend_expiry(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, patch.dict(os.environ, {'EXTRACTION_CACHE_DIR': directory}):
            calls = []
            def extract(prompt):
                calls.append(prompt)
                return [{'title': 'Family day', 'start_date': '2026-10-15'}]
            docs = self.documents()
            worker.extract_documents(docs, self.source, extract, self.today, {})
            self.assertEqual(len(calls), 2)
            self.assertEqual(list(Path(directory).glob('*.json')), [])
            worker.finish_result_cache(extract, 'a', True)
            stats = {}
            changed = [docs[0], (docs[1][0], docs[1][1].replace('2pm', '3pm'))]
            worker.extract_documents(changed, self.source, extract, self.today, stats)
            self.assertEqual(len(calls), 3)
            self.assertEqual(stats['detail_cache_hits'], 1)
            worker.finish_result_cache(extract, 'a', True)
            future = self.today + dt.timedelta(days=7)
            worker.extract_documents(changed, self.source, extract, future, {})
            self.assertEqual(len(calls), 5)

    def test_budget_failure_discards_earlier_staged_page(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, patch.dict(os.environ, {'EXTRACTION_CACHE_DIR': directory}), \
             patch.object(worker, 'robots_allows', return_value=(True, '')), \
             patch.object(worker, 'fetch_source_html', return_value=self.documents()):
            count = 0
            def extract(prompt):
                nonlocal count
                count += 1
                if count == 2:
                    raise worker.BudgetExhausted('budget')
                return []
            with self.assertRaises(worker.BudgetExhausted):
                worker.process_source(self.source, extract, self.today)
            self.assertEqual(extract.result_cache.pending, {})
            self.assertEqual(list(Path(directory).glob('*')), [])

    def test_failed_persistence_or_dry_run_discards_stage(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            def extract(prompt):
                return []
            extract.result_cache = ResultCache(directory)
            extract.result_cache.stage('a', 'https://x', 'digest', self.today, [])
            worker.finish_result_cache(extract, 'a', False)
            self.assertEqual(extract.result_cache.pending, {})
            self.assertEqual(list(Path(directory).glob('*')), [])

    def test_corrupt_cache_and_version_change_miss(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            cache = ResultCache(directory)
            cache.stage('a', 'https://x', 'one', self.today, [])
            cache.commit('a')
            self.assertEqual(cache.get('a', 'https://x', 'one', self.today), [])
            self.assertIsNone(cache.get('a', 'https://x', 'two', self.today))
            cache.path('a', 'https://x').write_text('{broken')
            self.assertIsNone(cache.get('a', 'https://x', 'one', self.today))

    def test_force_reread_ignores_unit_cache(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, patch.dict(os.environ, {'EXTRACTION_CACHE_DIR': directory}):
            calls = []
            def extract(prompt):
                calls.append(prompt)
                return []
            worker.extract_documents(self.documents(), self.source, extract, self.today, {})
            worker.finish_result_cache(extract, 'a', True)
            with patch.dict(os.environ, {'FORCE_REREAD': 'true'}):
                worker.extract_documents(self.documents(), self.source, extract, self.today, {})
            self.assertEqual(len(calls), 4)

    def test_truncated_page_does_not_call(self):
        def extract(prompt):
            self.fail('Truncated input must not make a paid call')
        with patch.object(worker, 'MAX_CHARS', 100):
            with self.assertRaisesRegex(ValueError, 'input limit'):
                worker.extract_documents(self.documents(), self.source, extract, self.today, {})

    def test_main_commits_only_after_rows_and_source_status_are_persisted(self):
        for returned, save_error, dry_run, expected in [
                ([{'id': 'a'}], None, False, True), ([], None, False, False),
                ([{'id': 'a'}], 'write failed', False, False), ([{'id': 'a'}], None, True, False)]:
            with self.subTest(returned=returned, save_error=save_error, dry_run=dry_run):
                db = Mock()
                db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [self.source]
                db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = returned
                def extract(prompt):
                    return []
                extract.metrics, extract.settings, extract.close = {}, {}, Mock()
                extract.result_cache = Mock()
                row = {'start_date': '2026-10-15', 'title': 'Family day', 'location': 'Museum'}
                with patch.dict('sys.modules', {'supabase': SimpleNamespace(create_client=lambda *_: db)}), \
                     patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_KEY': 'test', 'GEMINI_API_KEY': 'test'}), \
                     patch.object(worker, 'make_gemini_caller', return_value=extract), \
                     patch.object(worker, 'check_events_table', return_value=None), \
                     patch.object(worker, 'process_source', return_value=('ok', [row], 'digest', '', {})), \
                     patch.object(worker, 'save_events', return_value=save_error), \
                     patch.object(worker, 'remove_expired_events', return_value=0), \
                     patch.object(worker, 'log_run'), patch.object(worker, 'CATEGORY_FILTER', []), \
                     patch.object(worker, 'PAUSE_SECONDS', 0), patch.object(worker, 'DRY_RUN', dry_run):
                    worker.main()
                if expected:
                    extract.result_cache.commit.assert_called_once_with('a')
                else:
                    extract.result_cache.commit.assert_not_called()
                    extract.result_cache.discard.assert_called_once_with('a')

    def structured(self, **changes):
        event = {'@type': 'Event', 'name': 'Family pottery', 'description': 'Children create pottery.',
                 'startDate': '2026-10-15T14:00:00+01:00', 'endDate': '2026-10-15T16:00:00+01:00',
                 'url': '/pottery', 'location': {'name': 'Museum', 'address': {
                     'streetAddress': '1 High Street', 'postalCode': 'CF10 1AA'}},
                 'offers': {'price': '8.50', 'priceCurrency': 'GBP'}}
        event.update(changes)
        html = '<script type="application/ld+json">' + json.dumps(event) + '</script>'
        html += '<main>Family pottery Children create pottery. <a href="/pottery">Book</a></main>'
        return [('https://example.org/events', html)]

    def test_complete_structured_event_preserves_fields_without_call(self):
        rows = complete_events(self.structured(), worker.extract_jsonld_events)
        self.assertEqual(rows[0]['start_date'], '2026-10-15')
        self.assertEqual(rows[0]['time_text'], '14:00 - 16:00')
        self.assertEqual(rows[0]['cost_text'], '£8.50')
        self.assertEqual(rows[0]['postcode'], 'CF10 1AA')
        self.assertEqual(rows[0]['event_url'], 'https://example.org/pottery')
        def extract(prompt):
            self.fail('Complete opted-in metadata does not need AI')
        stats = {}
        result = worker.extract_documents(self.structured(), dict(self.source, structured_events_complete=True),
                                          extract, self.today, stats)
        self.assertEqual(result, rows)
        self.assertEqual(stats['structured_events'], 1)

    def test_ambiguous_structured_data_falls_back_as_whole(self):
        for change in ({'endDate': None}, {'description': 'Adult pottery'},
                       {'startDate': '2026-10-15T14:00:00'}, {'offers': {}},
                       {'eventSchedule': {'repeatFrequency': 'P1W'}}):
            with self.subTest(change=change):
                self.assertIsNone(complete_events(self.structured(**change), worker.extract_jsonld_events))


if __name__ == '__main__':
    unittest.main()
