import datetime as dt,unittest
from pathlib import Path
from gkfit_sessions import parse_gkfit

class GKFitTests(unittest.TestCase):
    def pages(self):return [(Path('tests/fixtures/gkfit')/(n+'.html')).read_text(encoding='utf8') for n in ['book','daytime','netball','holiday']]
    def test_real_catalogue_dates_places_and_availability(self):
        items,issues=parse_gkfit(*self.pages(),dt.date(2026,10,12))
        self.assertEqual(len(items),11)
        self.assertEqual(len(issues),9)
        self.assertEqual(len({x['proposal_key'] for x in items}),11)
        games=[x for x in items if x['name'].startswith('Game Night')]
        self.assertEqual(len(games),2)
        self.assertTrue(all(x['dates']=='2026-10-22' for x in games))
        self.assertTrue(all(x['dates']=='' for x in items if 'Autumn' in x['name'] or 'Royston' in x['name']))
        royston=[x for x in items if 'Royston' in x['name']]
        self.assertEqual(len(royston),2)
        self.assertIn('10.30-11.30am',royston[0]['schedule'])
        self.assertTrue(all(x['postcode']=='SG8 7XT' for x in royston))
        self.assertFalse(any('Y4-6' in x['name'] or 'Tue 13 Oct' in x['name'] for x in items))
        self.assertEqual({x['dates'] for x in items if 'holiday' in x['name']},{'2026-10-27','2026-10-30'})
    def test_old_occurrences_are_excluded_and_missing_structure_fails(self):
        items,_=parse_gkfit(*self.pages(),dt.date(2026,11,1))
        self.assertTrue(all(not x['dates'] for x in items))
        pages=self.pages();pages[0]='<html>No catalogue</html>'
        with self.assertRaises(ValueError):parse_gkfit(*pages,dt.date(2026,10,12))
    def test_unsafe_booking_and_missing_address_cannot_be_inferred(self):
        pages=self.pages();pages[0]=pages[0].replace('https://www.gkfit.co.uk/service-page/','https://example.com/service-page/',1)
        with self.assertRaises(ValueError):parse_gkfit(*pages,dt.date(2026,10,12))
        pages=self.pages();pages[1]='<main>No published venue addresses</main>'
        items,issues=parse_gkfit(*pages,dt.date(2026,10,12))
        self.assertFalse(any(x['venue']=='Hauxton Centre' for x in items))
        self.assertTrue(any('Missing supported venue' in x['reason'] for x in issues))
