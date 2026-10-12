import importlib.util,json,tempfile,unittest
from pathlib import Path
from cambridgeshire_rhymetime import parse_snapshots

class StorytimeTests(unittest.TestCase):
    def snapshot(self,programme='storytime'):
        return json.loads(Path(f'artefacts/data/ds10-cambridgeshire-{programme}-snapshot-2026-10-12.json').read_text(encoding='utf8'))
    def test_real_schedules_and_missing_or_conflicting_evidence(self):
        items,issues=parse_snapshots(self.snapshot(),'storytime')
        self.assertEqual(len(items),16)
        self.assertEqual(len(issues),6)
        self.assertTrue(all(x['dates']=='' for x in items))
        linton=next(x for x in items if x['venue']=='Linton Library')
        self.assertEqual(linton['ages'],'0-4 year')
        littleport=next(x for x in items if x['venue']=='Littleport Library')
        self.assertIn('Booking at library desk',littleport['notes'])
        central=[x for x in items if x['venue']=='Cambridge Central Library']
        self.assertEqual(len(central),2)
        self.assertTrue(all('Resolve before application' in x['notes'] for x in central))
        cherry=next(x for x in items if x['venue']=='Cherry Hinton Hub')
        self.assertTrue(cherry['booking_url'].startswith('https://www.eventbrite.co.uk/o/'))
        self.assertIn('Every other Saturday',cherry['schedule'])
    def test_shared_sessions_have_same_identity(self):
        stories,_=parse_snapshots(self.snapshot(),'storytime')
        rhymes,_=parse_snapshots(self.snapshot('rhymetime'))
        shared=set(x['proposal_key'] for x in stories)&set(x['proposal_key'] for x in rhymes)
        self.assertEqual(len(shared),2)
    def test_programme_and_unsafe_booking_links_fail_closed(self):
        with self.assertRaises(ValueError):parse_snapshots(self.snapshot())
        s=self.snapshot();s['records'][0]['booking_url']='javascript:alert(1)'
        with self.assertRaises(ValueError):parse_snapshots(s,'storytime')
    def test_replay_preserves_other_programmes_and_merges_shared_sessions(self):
        spec=importlib.util.spec_from_file_location('snapshot_import','scripts/import_ds10_rhymetime_snapshots.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        temp_root=(Path.cwd()/'tests').resolve()
        self.assertTrue(temp_root.is_relative_to(Path.cwd().resolve()))
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            module.ROOT=Path(folder);data=module.ROOT/'artefacts/data';data.mkdir(parents=True)
            names=['ds10-action-console-19-2026-10-12.json','ds10-automated-session-proposals-2026-10-12.json']
            for name in names:(data/name).write_bytes((Path('artefacts/data')/name).read_bytes())
            before=json.loads((data/names[0]).read_text(encoding='utf8'))
            snapshot_path=data/'snapshot.json';snapshot_path.write_text(json.dumps(self.snapshot()),encoding='utf8')
            module.main(snapshot_path);module.main(snapshot_path)
            after=json.loads((data/names[0]).read_text(encoding='utf8'))
            target='bbc6d669-367b-4eb4-9cde-18372c8afe77'
            self.assertEqual([x for x in before['records'] if x['id']!=target],[x for x in after['records'] if x['id']!=target])
            report=json.loads((data/names[1]).read_text(encoding='utf8'))
            entries=report['distinct_session_proposals']
            self.assertEqual(len(entries),len({x['session']['proposal_key'] for x in entries}))
            shared=[x for x in entries if target in x['parent_record_ids'] and '368a7430-a54b-4c02-9af7-0d4702d740dc' in x['parent_record_ids']]
            self.assertEqual(len(shared),2)
            self.assertTrue(all(len(x['parent_record_ids'])==len(set(x['parent_record_ids'])) for x in entries))
