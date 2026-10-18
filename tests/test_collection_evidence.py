import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from collection_evidence import CollectionEvidence, public_view_readback


class EvidenceTests(unittest.TestCase):
    def test_partial_failure_and_deferred_sources_are_retained(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'evidence.jsonl'
            report = CollectionEvidence([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], dry_run=False, path=path)
            report.source({'id': 'a'}, 'ok', {'extracted': 4, 'kept': 2, 'duplicates': 1},
                          [{'dedupe_key': 'one'}, {'dedupe_key': 'two'}],
                          write_state='succeeded', health_state='succeeded')
            report.source({'id': 'b'}, 'failed_save', {'extracted': 1, 'kept': 1},
                          [{'dedupe_key': 'three'}], write_state='unknown_partial', health_state='failed')
            # Source records survive even before finalisation.
            self.assertEqual(len(path.read_text().splitlines()), 3)
            summary = report.finish(stopped_early=True, fatal=False)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(rows[1]['rejected'], 1)
            self.assertEqual(rows[1]['saved_count'], 2)
            self.assertEqual(rows[1]['public_readback']['state'], 'not_checked')
            self.assertIsNone(rows[2]['saved_count'])
            self.assertEqual(rows[3]['status'], 'deferred_not_processed')
            self.assertFalse(summary['all_sources_checked'])
            self.assertFalse(summary['all_sources_succeeded'])

    def test_unchanged_is_not_item_coverage_and_zero_is_flagged(self):
        report = CollectionEvidence([{'id': 'a'}, {'id': 'b'}], dry_run=True)
        report.source({'id': 'a'}, 'unchanged', {}, [], write_state='dry_run', health_state='dry_run')
        report.source({'id': 'b'}, 'ok_zero', {'extracted': 2, 'kept': 0}, [],
                      write_state='dry_run', health_state='dry_run')
        self.assertEqual(report.outcomes[0]['coverage'], 'unknown')
        self.assertIsNone(report.outcomes[0]['validated'])
        self.assertTrue(report.outcomes[1]['suspicious_zero'])
        self.assertEqual(report.outcomes[1]['rejected'], 2)
        self.assertIsNone(report.outcomes[1]['saved_count'])

    def test_budget_stop_does_not_become_success(self):
        report = CollectionEvidence([{'id': 'a'}], dry_run=False)
        report.source({'id': 'a'}, 'deferred_budget', {}, [],
                      write_state='not_attempted', health_state='not_attempted')
        result = report.finish(stopped_early=True, fatal=False)
        self.assertFalse(result['all_sources_checked'])
        self.assertFalse(result['all_sources_succeeded'])

    def test_cannot_overwrite_previous_invocation_or_duplicate_source(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'evidence.jsonl'
            report = CollectionEvidence([{'id': 'a'}], dry_run=False, path=path)
            with self.assertRaises(FileExistsError):
                CollectionEvidence([], dry_run=False, path=path)
            report.source({'id': 'a'}, 'failed_404', {}, [],
                          write_state='not_attempted', health_state='succeeded')
            with self.assertRaises(ValueError):
                report.source({'id': 'a'}, 'ok_zero', {}, [],
                              write_state='not_attempted', health_state='succeeded')

    def test_health_write_failure_is_not_hidden_by_valid_rows(self):
        report = CollectionEvidence([{'id': 'a'}], dry_run=False)
        report.source({'id': 'a'}, 'ok', {'kept': 1}, [{'dedupe_key': 'one'}],
                      write_state='succeeded', health_state='unconfirmed')
        self.assertFalse(report.finish(stopped_early=False, fatal=False)['all_sources_succeeded'])

    def test_public_view_readback_is_bounded_and_errors_are_not_empty_success(self):
        db = Mock()
        query = db.table.return_value.select.return_value.eq.return_value.in_.return_value.limit.return_value
        query.execute.return_value = SimpleNamespace(data=[{'id': 'published', 'dedupe_key': 'a'}])
        rows = [{'dedupe_key': key} for key in ('a', 'b', 'c')]
        result = public_view_readback(db, 'source', rows, limit=2)
        self.assertEqual(result['state'], 'read')
        self.assertEqual(result['unmatched_keys'], ['b'])
        self.assertFalse(result['sample_complete'])
        self.assertEqual(result['candidate_count'], 3)
        query.execute.side_effect = RuntimeError('private credentials must not appear')
        result = public_view_readback(db, 'source', rows)
        self.assertEqual(result['state'], 'unavailable')
        self.assertIsNone(result['rows'])
        self.assertNotIn('credentials', json.dumps(result))

    def test_empty_public_readback_is_a_real_read_and_no_candidates_is_not_checked(self):
        db = Mock()
        query = db.table.return_value.select.return_value.eq.return_value.in_.return_value.limit.return_value
        query.execute.return_value = SimpleNamespace(data=[])
        self.assertEqual(public_view_readback(db, 'source', [{'dedupe_key': 'a'}])['rows'], [])
        self.assertEqual(public_view_readback(db, 'source', [])['state'], 'not_checked')


if __name__ == '__main__':
    unittest.main()
