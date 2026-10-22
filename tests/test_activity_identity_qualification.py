import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qualification', ROOT/'scripts/qualify_activity_identity.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class IdentityQualification(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT/'tests/fixtures/library-portal-records.json').read_text(encoding='utf-8'))

    def test_real_series_group_occurrences_without_inventing_programmes(self):
        report = q.qualify(self.rows, self.rows)
        self.assertEqual([r['session_id'] for r in report['selected_series']], ['264038', '319285'])
        self.assertEqual([len(r['occurrences']) for r in report['selected_series']], [2, 2])
        self.assertTrue(all(r['programme_id'] is None for r in report['selected_series']))

    def test_same_title_or_venue_does_not_merge_series(self):
        rows = copy.deepcopy(self.rows)
        for r in rows:
            r['name'] = 'Same title'
            r['location_id'] = 63
        self.assertEqual(len(q.qualify(rows, rows)['selected_series']), 2)

    def test_captured_live_identity_facts_are_replayable_without_network(self):
        report = json.loads((ROOT/'artefacts/data/sprint9-provider-identity.json').read_text(encoding='utf-8'))
        rows = [r for session in report['selected_series'] for r in session['occurrences']]
        replay = q.qualify(rows, rows)
        self.assertEqual([len(r['occurrences']) for r in replay['selected_series']], [6, 5])
        self.assertEqual(len({r['event_id'] for r in rows}), 11)

    def test_missing_changed_or_single_occurrence_series_cannot_qualify(self):
        for mutate in (lambda r: r.pop(0), lambda r: r[0].update(series_id=123),
                       lambda r: r[0].update(name='Changed')):
            rows = copy.deepcopy(self.rows)
            mutate(rows)
            with self.assertRaises(ValueError):
                q.qualify(self.rows, rows)

    def test_invalid_or_contradictory_provider_identifiers_fail_closed(self):
        for patch in ({'event_id': True}, {'series_id': -1}, {'url': 'https://evil.invalid/event?id=319317'}):
            rows = copy.deepcopy(self.rows)
            rows[0].update(patch)
            with self.assertRaises(ValueError):
                q.identity_facts(rows)
        rows = copy.deepcopy(self.rows)
        rows.append({**rows[0], 'series_id': 42})
        with self.assertRaises(ValueError):
            q.identity_facts(rows)


if __name__ == '__main__':
    unittest.main()
