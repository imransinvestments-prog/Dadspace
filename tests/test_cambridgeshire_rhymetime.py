import copy,json,unittest
from pathlib import Path
from cambridgeshire_rhymetime import parse_snapshots

class CambridgeshireRhymetimeTests(unittest.TestCase):
    def snapshot(self):return json.loads(Path('artefacts/data/ds10-cambridgeshire-rhymetime-snapshot-2026-10-12.json').read_text(encoding='utf8'))
    def test_real_snapshot_keeps_distinct_groups_and_rejects_relocated_branch_pin(self):
        items,issues=parse_snapshots(self.snapshot())
        self.assertEqual(len(items),31);self.assertEqual(len(issues),4)
        thurs=[x for x in items if x['name']=='Rhymetime on Thursdays at Cambridge Central Library']
        self.assertEqual(len(thurs),2);self.assertNotEqual(thurs[0]['proposal_key'],thurs[1]['proposal_key'])
        self.assertFalse(any('Wisbech' in x['name'] or 'Wiggle and Giggle'==x['name'] for x in items))
        self.assertTrue(all(x['dates']=='' for x in items))
        cottenham=next(x for x in items if 'Cottenham' in x['name'])
        self.assertIn('every 2 weeks',cottenham['schedule']);self.assertIn('term time',cottenham['schedule'])
    def test_foreign_urls_duplicates_and_missing_snapshot_coverage_fail_closed(self):
        for change in ['foreign','duplicate','missing']:
            s=self.snapshot()
            if change=='foreign':s['records'][0]['url']='https://example.com/service.page?id=wrong'
            elif change=='duplicate':s['records'].append(copy.deepcopy(s['records'][0]))
            else:s['records'].pop()
            with self.assertRaises(ValueError):parse_snapshots(s)
    def test_missing_clock_does_not_generate_session_time(self):
        s=self.snapshot();s['records'][0]['fields']['Opening Hours']=''
        items,issues=parse_snapshots(s)
        self.assertEqual(len(items),30)
        self.assertTrue(any(x['reason']=='Missing published session clock range' for x in issues))
    def test_published_intro_age_fallback_and_huntingdon_address_flags(self):
        items,issues=parse_snapshots(self.snapshot())
        soh=next(x for x in items if x['venue']=='Soham Library')
        self.assertEqual(soh['ages'],'birth to 4 years')
        huntingdon=[x for x in items if x['venue']=='Huntingdon Library']
        self.assertEqual(len(huntingdon),2)
        self.assertTrue(all('Street address/postcode missing' in x['notes'] for x in huntingdon))
