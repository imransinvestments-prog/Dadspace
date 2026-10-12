import datetime as dt
import unittest
from classforkids_calendar import parse_detail,collect

URL='https://little-movers-gym.classforkids.io/info/123'
HTML='''<div><span class="label">Class details</span><h4>Mini Movers Gymnastics <span>(18mth - 3yrs)</span></h4><p>Wednesday 10:30am - 11:15am</p></div>
<div><span class="label">Venue details</span><p><strong>Grace Point,</strong><small><strong>N1 2SN</strong></small></p></div>
<h5>Price:</h5><h2>£150.00</h2><p class="label-list"><span class="info"><strong>2</strong> sessions</span><span class="reverse">Wed 14 Oct 26</span><span class="reverse">Wed 28 Oct 26</span></p>'''

class ClassForKidsCalendarTests(unittest.TestCase):
    def test_actual_class_details_keep_age_price_and_session_gaps(self):
        item=parse_detail(HTML,URL,dt.date(2026,10,12))
        self.assertEqual(item['title'],'Mini Movers Gymnastics')
        self.assertEqual(item['age_range'],'18mth - 3yrs')
        self.assertEqual(item['occurrence_dates'],['2026-10-14','2026-10-28'])
        self.assertIn('remaining published sessions',item['cost_text'])
        self.assertEqual(item['postcode'],'N1 2SN')

    def test_expired_sessions_and_shells_fail(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            parse_detail(HTML.replace('<strong>2</strong>','<strong>3</strong>'),URL,dt.date(2026,10,12))
        with self.assertRaisesRegex(ValueError,'remaining'):
            parse_detail(HTML,URL,dt.date(2026,11,1))
        with self.assertRaisesRegex(ValueError,'shell'):
            collect(dict(url='https://little-movers-gym.classforkids.io/'),dt.date(2026,10,12),lambda _:'<h1>Classes</h1>',lambda _:(True,''),{})

    def test_only_observed_same_host_links_are_collected(self):
        origin='https://little-movers-gym.classforkids.io/'
        index='<a data-test="infoAndBooking" href="/info/123">Info</a>'
        stats={};calls=[]
        def fetch(url):calls.append(url);return index if url==origin else HTML
        rows,_=collect(dict(url=origin),dt.date(2026,10,12),fetch,lambda _:(True,''),stats)
        self.assertEqual(len(rows),1);self.assertEqual(calls,[origin,URL])
        with self.assertRaisesRegex(ValueError,'Unreviewed'):
            collect(dict(url=origin),dt.date(2026,10,12),lambda _:index.replace('/info/123','https://foreign.test/info/123'),lambda _:(True,''),{})
