import copy
import importlib.util
import json
from pathlib import Path
import unittest
from provider_session_identity import metadata, row_identity

spec=importlib.util.spec_from_file_location('worker_fixture',Path(__file__).resolve().parents[1]/'scripts/export_provider_worker_fixture.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

class ProviderSessionTests(unittest.TestCase):
    def test_real_collector_cleaner_keeps_same_title_same_venue_sessions_separate(self):
        rows=f.fixture()
        self.assertEqual(len(rows),2)
        self.assertEqual(len({r['dedupe_key'] for r in rows}),2)
        self.assertEqual(len({r['title'] for r in rows}),1)
        self.assertEqual([len(r['provider_occurrences']) for r in rows],[2,2])
        frozen=json.loads(Path('tests/fixtures/provider-session-worker-rows.json').read_text(encoding='utf-8'))
        self.assertEqual(rows,frozen)

    def test_rename_preserves_worker_key_and_unknown_metadata_cannot_fall_back(self):
        records=json.loads(Path('tests/fixtures/library-portal-records.json').read_text(encoding='utf-8'))
        a=f.worker_rows(records)
        for r in records:r['name']='Renamed recurring family programme'
        b=f.worker_rows(records)
        self.assertEqual([r['dedupe_key'] for r in a],[r['dedupe_key'] for r in b])
        with self.assertRaises(ValueError): row_identity({},f.SOURCE,f.SOURCE['source_adapter'])
        with self.assertRaises(ValueError): row_identity(a[0],{'source_adapter':'library_portal'},'library_portal')

    def test_duplicate_or_contradictory_occurrences_rejected(self):
        row=f.fixture()[0]
        occurrences=copy.deepcopy(row['provider_occurrences'])
        occurrences[0]['url']='https://evil.invalid/event?id=1'
        with self.assertRaises(ValueError):metadata(row['provider_namespace'],row['provider_session_id'],occurrences)
        with self.assertRaises(ValueError):metadata(row['provider_namespace'],row['provider_session_id'],[row['provider_occurrences'][0]]*2)

if __name__=='__main__':unittest.main()
