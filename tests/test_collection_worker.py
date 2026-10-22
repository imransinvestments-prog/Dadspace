"""Exercise the real run loop with isolated source/database/model boundaries."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import worker
from gemini_usage import BudgetExhausted


class CollectionWorkerTests(unittest.TestCase):
    def test_partial_save_and_budget_stop_do_not_mark_sources_fresh(self):
        sources = [{'id': key, 'name': key, 'last_hash': 'old'} for key in ('a', 'b', 'c', 'd')]
        sources.insert(0, {'id':'dedicated-nct','name':'NCT','source_adapter':'nct_dedicated'})
        db = Mock()
        db.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = sources
        # CATEGORY_FILTER uses in_ before source selection.
        db.table.return_value.select.return_value.eq.return_value.in_.return_value.limit.return_value.execute.return_value.data = []
        db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = sources
        extract = Mock(metrics={}, settings={})
        row = {'dedupe_key': 'key', 'title': 'Programme'}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'run.jsonl'
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co',
                    'SUPABASE_KEY': 'fake', 'GEMINI_API_KEY': 'fake',
                    'COLLECTION_EVIDENCE_PATH': str(path), 'USAGE_REPORT_PATH': ''}), \
                 patch('supabase.create_client', return_value=db), \
                 patch('shadow_capture.capture_calls', return_value=extract), \
                 patch.object(worker, 'check_events_table', return_value=None), \
                 patch.object(worker, 'make_gemini_caller', return_value=extract), \
                 patch.object(worker, 'process_source', side_effect=[
                     ('ok', [row], 'new', '', {'extracted': 1, 'kept': 1}),
                     ('ok', [row], 'new', '', {'extracted': 1, 'kept': 1}),
                     BudgetExhausted('bounded stop')]), \
                 patch.object(worker, 'save_events', side_effect=['partial save failure', None]), \
                 patch.object(worker, 'remove_expired_events', return_value=None), \
                 patch.object(worker, 'finish_result_cache'), \
                 patch.object(worker, 'log_run'), \
                 patch.object(worker.time, 'sleep'), \
                 patch.object(worker, 'CATEGORY_FILTER', ['activities']), \
                 patch.object(worker, 'LIMIT', 0), \
                 patch.object(worker, 'DRY_RUN', False):
                worker.main()
            records = [json.loads(line) for line in path.read_text().splitlines()]
        outcomes = [row for row in records if row['kind'] == 'source']
        self.assertEqual([row['status'] for row in outcomes],
                         ['failed_save', 'ok', 'deferred_budget', 'deferred_not_processed'])
        self.assertEqual(outcomes[0]['write_state'], 'unknown_partial')
        self.assertEqual(outcomes[0]['validated'], 1)
        self.assertIsNone(outcomes[0]['saved_count'])
        self.assertEqual(outcomes[1]['saved_count'], 1)
        self.assertEqual(outcomes[1]['public_readback']['state'], 'read')
        updates = [call.args[0] for call in db.table.return_value.update.call_args_list]
        self.assertEqual(len(updates), 2)
        self.assertNotIn('last_hash', updates[0])
        self.assertNotIn('last_success_at', updates[0])
        self.assertEqual(updates[1]['last_hash'], 'new')
        self.assertFalse(records[-1]['all_sources_succeeded'])


if __name__ == '__main__':
    unittest.main()
