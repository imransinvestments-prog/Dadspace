import copy
import datetime as dt
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from library_portal import collect_portal, published_records
from mylibrary_calendar import CalendarError
import events_worker as quality

URL='https://libraries.ealing.gov.uk/events'
TODAY=dt.date(2026,10,11)
RECORDS=json.loads((Path(__file__).parent/'fixtures/library-portal-records.json').read_text(encoding='utf-8'))

def page(records,description=None):
    stream=''
    if description:
        stream='a:T'+format(len(description.encode('utf-8')),'x')+','+description
    stream+='b:'+json.dumps(['$','component',None,dict(isEvents=True,source=records)],ensure_ascii=False)+'\n'
    return '<main>Public events</main><script>self.__next_f.push('+json.dumps([1,stream]) +')</script>'

class PublicPortalTests(unittest.TestCase):
    def collect(self,records=None,**kw):
        return collect_portal(dict(url=URL),TODAY,lambda _:page(records or RECORDS),lambda _:(True,''),{},**kw)

    def test_utf8_length_frames_and_reference_resolution(self):
        records=copy.deepcopy(RECORDS);records[0]['description_html']='$a'
        result=published_records(page(records,'<p>Rhymes for babies — songs £0.</p>'))
        self.assertIn('babies — songs £0',result[0]['description_html'])

    def test_real_public_records_keep_gaps_and_identity(self):
        raw,digest,stats=self.collect()
        southall=next(x for x in raw if x['venue_name']=='Southall library')
        self.assertIn('2026-10-12',southall['occurrence_dates'])
        self.assertNotIn('2026-10-26',southall['occurrence_dates'])
        with patch.object(quality,'_resolve_venue',return_value=None):
            rows=quality.clean_events(raw,dict(id='preview'),URL,'library_portal',TODAY,{})
        self.assertTrue(rows);self.assertTrue(rows[0]['start_date'])
        self.assertEqual(stats['gemini_logical_calls'],0)
        self.assertEqual(digest,self.collect()[1])

    def test_incomplete_window_blocked_private_and_cancelled_data(self):
        with self.assertRaisesRegex(CalendarError,'full collection window'):
            self.collect(RECORDS[:-1])
        records=copy.deepcopy(RECORDS)
        for row in records[:-1]:row['is_cancelled']=True
        raw,_,stats=self.collect(records)
        self.assertEqual(raw,[]);self.assertGreater(stats['cancelled_or_full'],0)
        with self.assertRaisesRegex(CalendarError,'robots'):
            collect_portal(dict(url=URL),TODAY,lambda _:self.fail('fetch called'),lambda _:(False,'disallow'),{})

    def test_same_programme_retains_different_times(self):
        records=copy.deepcopy(RECORDS)
        original=records[0];other=copy.deepcopy(original)
        other['event_id']=999;other['start_time']+=3600;other['end_time']+=3600
        records.append(other);records.sort(key=lambda x:x['start_time'])
        raw,_,_=self.collect(records)
        group=next(x for x in raw if x['venue_name']==original['location_name'])
        self.assertIsNone(group['time_text'])
        self.assertIn('10:00 AM - 11:00 AM',group['schedule_text'])
        self.assertIn('11:00 AM - 12:00 PM',group['schedule_text'])

    def test_private_hosts_and_malformed_frames_never_qualify(self):
        with self.assertRaises(CalendarError):
            collect_portal(dict(url='https://evil.test/events'),TODAY,lambda _:self.fail('fetch called'),lambda _:(True,''),{})
        with self.assertRaises(CalendarError):published_records('<main>Empty calendar shell</main>')

if __name__=='__main__': unittest.main()
