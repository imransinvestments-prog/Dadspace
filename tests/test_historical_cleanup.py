import unittest
from historical_cleanup import build_sql

class HistoricalCleanupTests(unittest.TestCase):
    def plan(self,**patch):
        return dict(changes=[dict(id='73b4f656-41ac-4037-9030-6d79e94c5636',expected_fingerprint='a'*32,patch=patch)])
    def test_default_rolls_back_and_checks_provenance_and_visibility(self):
        sql=build_sql(self.plan(schedule_text='First Saturday, except December'))
        self.assertIn('rollback;',sql)
        self.assertIn('Concurrent change/missing row',sql)
        self.assertIn('Protected provenance changed',sql)
        self.assertIn('Withdrawn record remains in public feed',sql)
    def test_unreviewed_fields_and_unsafe_data_are_rejected(self):
        for patch in [dict(last_seen_at='now'),dict(schedule_text='$ds10_cleanup_plan$'),dict(withdrawn_at='2026-10-12')]:
            with self.assertRaises(ValueError):build_sql(self.plan(**patch))
    def test_duplicate_plan_ids_are_rejected(self):
        plan=self.plan(schedule_text='Weekly')
        plan['changes']*=2
        with self.assertRaises(ValueError):build_sql(plan)
