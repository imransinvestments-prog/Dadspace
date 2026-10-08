import datetime as dt
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import events_worker as quality
import worker
from activity_source_discovery import detail_urls, fetch_listing_documents


class FakeDB:
    def __init__(self, error='21000', row_failure=False):
        self.calls = []
        self.error = error
        self.row_failure = row_failure

    def table(self, name):
        return self

    def upsert(self, payload, on_conflict):
        self.calls.append(payload)
        return self

    def execute(self):
        if isinstance(self.calls[-1], list):
            raise RuntimeError(self.error)
        if self.row_failure:
            raise RuntimeError('save failed')


class ActivityIngestionTests(unittest.TestCase):
    def test_trigger_collision_retries_sequentially(self):
        rows = [{'dedupe_key':'a'}, {'dedupe_key':'b'}]
        db = FakeDB()
        self.assertIsNone(worker.save_events(db, rows))
        self.assertEqual(db.calls, [rows, *rows])

    def test_partial_retry_reports_failure(self):
        self.assertIn('save failed', worker.save_events(FakeDB(row_failure=True), [{'dedupe_key':'a'}]))

    def test_non_collision_is_not_retried(self):
        db = FakeDB(error='permission denied')
        self.assertIn('permission denied', worker.save_events(db, [{'dedupe_key':'a'}]))
        self.assertEqual(len(db.calls), 1)

    def test_bounded_same_host_detail_discovery(self):
        html = '''<nav><a href='/events/nav'>Events</a></nav><main>
        <a href='/events/lego'>Family LEGO workshop</a>
        <a href='/events/lego#book'>Book event</a>
        <a href='https://evil.test/event'>Family event</a>
        <a href='/account/events'>Events</a>
        <a href='/events/story'>Storytime event</a></main>'''
        self.assertEqual(detail_urls(html, 'https://museum.test/whats-on', 1), ['https://museum.test/events/lego'])

    def test_detail_failure_does_not_become_success(self):
        def fetch(url):
            if url.endswith('lego'):
                raise RuntimeError('unavailable')
            return '<main><a href="/events/lego">Family event</a></main>'
        with self.assertRaises(RuntimeError):
            fetch_listing_documents({'url':'https://museum.test/whats-on'}, fetch, lambda _: (True, ''), lambda: None)

    def test_robots_blocked_detail_is_not_fetched(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            return '<main><a href="/events/lego">Family event</a></main>'
        with self.assertRaises(RuntimeError):
            fetch_listing_documents({'url':'https://museum.test/whats-on'}, fetch, lambda _: (False, 'blocked'), lambda: None)
        self.assertEqual(len(calls), 1)

    def activity(self, **overrides):
        return dict(title='Family LEGO club', listing_type='activity', family_relevance=5,
                    audience='families', confidence=.9, venue_name='Central Library',
                    location='Central Library', schedule_text='Every Saturday at 10am',
                    event_url='/events/lego', **overrides)

    def clean(self, item):
        stats={}
        with patch.object(quality, '_resolve_venue', return_value=None):
            rows=quality.clean_events([item], {'id':'test'}, 'https://library.test/', 'test', dt.date(2026,10,8), stats)
        return rows, stats

    def test_actionable_recurring_activity_kept(self):
        rows, _=self.clean(self.activity())
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['start_date'])
        self.assertEqual(rows[0]['event_url'], 'https://library.test/events/lego')

    def test_bare_time_and_duration_rejected(self):
        for schedule in ('09:00','30 minutes','Regular sessions',None):
            item=self.activity(); item['schedule_text']=schedule
            rows,stats=self.clean(item)
            self.assertEqual(rows, [])
            self.assertEqual(stats['missing_activity_schedule'],1)

    def test_missing_location_and_link_rejected(self):
        item=self.activity(); item.update(location=None,venue_name=None)
        self.assertEqual(self.clean(item)[1]['missing_activity_location'],1)
        item=self.activity(); item['event_url']=None
        self.assertEqual(self.clean(item)[1]['missing_activity_url'],1)

    def test_activity_venue_suffix_drift_does_not_duplicate(self):
        first=self.activity(); first['title']='Family LEGO club @ Central Library'
        a=self.clean(first)[0][0]; b=self.clean(self.activity())[0][0]
        self.assertEqual(a['dedupe_key'],b['dedupe_key'])
        self.assertEqual(a['title'],'Family LEGO club')
        self.assertEqual(quality._listing_title('LEGO at Home','Central Library'),'LEGO at Home')

    def test_specific_event_url_survives_title_and_address_drift(self):
        a=dict(title='Halloween Crafts @ Canton Library',start_date='2026-10-28',
               venue_name='Canton Library',location='Canton Library, Library Street',
               event_url='https://library.test/events/crafts',source_url='https://library.test/events')
        b=dict(a,title='Halloween Crafts',location='Canton Library')
        self.assertEqual(quality._event_dedupe_key(a),quality._event_dedupe_key(b))
        self.assertNotEqual(quality._event_dedupe_key(a),quality._event_dedupe_key(dict(b,venue_name='Other Library')))
        self.assertNotEqual(quality._event_dedupe_key(a),quality._event_dedupe_key(dict(b,start_date='2026-10-29')))

    def test_recorded_cardiff_extraction_keeps_all_seven_identities(self):
        runs=json.loads((Path(__file__).parent/'fixtures/activity-repeat-cardiff.json').read_text(encoding='utf-8'))
        keys=[]
        for rows in runs:
            identities=set()
            for row in rows:
                row=dict(row,title=quality._listing_title(row['title'],row['venue_name']))
                key=quality._activity_dedupe_key(row['title'],row['venue_name'] or row['location']) if row['listing_type']=='activity' else quality._event_dedupe_key(row)
                identities.add(key)
            keys.append(identities)
        self.assertEqual(len(keys[0]),7)
        self.assertEqual(keys[0],keys[1])


if __name__=='__main__':
    unittest.main()
