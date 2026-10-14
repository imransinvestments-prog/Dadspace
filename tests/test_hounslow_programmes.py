import unittest
from unittest.mock import patch
import datetime as dt
import hounslow_programmes as h

URL=next(iter(h.REVIEWED_URLS))
HTML='''<header><h1>Library Storytime</h1></header><main>
<h2>Key information</h2><h3>Eligibility</h3><p>Ages 0 - 5 years.</p>
<h2>What is this service?</h2><p>When: Every Tuesday morning (Term-time only)</p>
<p>Time: from 11am to 11.30am</p><p>Who can attend: Children aged 0-5</p>
<p>Cost: Free</p><p>Spaces are limited and booking is required.</p>
<p>No school holidays. October Half Term - 26/10/2026 - 02/11/2026</p>
<p>Christmas - 21/12/2026 - 04/01/2027</p>
<h2>Location</h2><h3>Chiswick Library</h3><h4>Location</h4><div>Duke’s Avenue, Chiswick W4 2AB</div>
<h4>Date and time</h4><div>Every Tuesday 11:00 11:30</div>
<h2>Other results you might be interested in</h2><p>Ages 12–18, Wednesday, ZZ1 1ZZ</p></main>'''

class HounslowProgrammes(unittest.TestCase):
    def test_full_regular_schedule_exclusions_and_place_preserved_without_generated_dates(self):
        item=h.parse_programme(HTML,URL)[0]
        self.assertEqual(item['listing_type'],'activity')
        self.assertEqual(item['venue_name'],'Chiswick Library')
        self.assertEqual(item['postcode'],'W4 2AB')
        self.assertEqual(item['age_range'],'0–5 years')
        self.assertIsNone(item['start_date'])
        self.assertIsNone(item['end_date'])
        self.assertEqual(item['occurrence_dates'],[])
        self.assertIn('26/10/2026–02/11/2026',item['schedule_text'])
        self.assertIn('21/12/2026–04/01/2027',item['schedule_text'])
        self.assertNotIn('Wednesday',item['schedule_text'])
        self.assertEqual(item['cost_text'],'Free')
    def test_unreviewed_and_robots_denied_routes_never_fetch(self):
        for source,robots in [({'url':'https://evil.invalid/'},lambda u:(True,'')),({'url':URL},lambda u:(False,'denied'))]:
            with patch('builtins.print'):
                with self.assertRaises(ValueError):
                    h.collect(source,dt.date(2026,10,14),lambda u:self.fail('must not fetch'),robots)
    def test_partial_or_ambiguous_evidence_fails_instead_of_fresh_empty(self):
        for html in [HTML.replace('Ages 0 - 5 years.','Ages unknown'),HTML.replace('W4 2AB','No postcode'),HTML.replace('Every Tuesday','Regular',1),
                     HTML.replace('26/10/2026 - 02/11/2026','').replace('21/12/2026 - 04/01/2027',''),HTML+'<h1>Other title</h1>']:
            with self.assertRaises(ValueError):h.parse_programme(html,URL)
    def test_normal_worker_cleaner_keeps_regular_programme_and_zero_model_path(self):
        import events_worker as worker
        worker.base.DRY_RUN=True
        stats={}
        with patch.object(worker,'_resolve_venue',return_value=None):
            rows=worker.clean_events(h.parse_programme(HTML,URL),{'id':'00000000-0000-0000-0000-000000000001'},URL,'hounslow_programme',dt.date(2026,10,14),stats)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['listing_type'],'activity')
        self.assertIsNone(rows[0]['venue_id'])
        self.assertIsNone(rows[0]['start_date'])
        self.assertIn('school holidays',rows[0]['schedule_text'])
        self.assertEqual(rows[0]['event_url'],URL)

if __name__=='__main__':unittest.main()
