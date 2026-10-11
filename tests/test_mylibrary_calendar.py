import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

import events_worker as quality
from mylibrary_calendar import CalendarError, Page, collect, parse_detail, parse_ics, public_url

URL='https://ealing.events.mylibrary.digital/event?id=319317'
SERIES='https://ealing.events.mylibrary.digital/series?si=319285'
TODAY=dt.date(2026,10,11)
HTML=(Path(__file__).parent/'fixtures/mylibrary-southall.html').read_text(encoding='utf-8')
SERIES_HTML='''<div id="main"><table id="resultsTable"><tbody>
<tr><td><a href="/event?id=319317">Bounce and Rhyme and Storytime</a></td><td>Tomorrow at 10:00 AM</td><td>Southall Library</td></tr>
<tr><td><a href="/event?id=319318">Bounce and Rhyme and Storytime</a></td><td>19 October 2026 at 10:00 AM</td><td>Southall Library</td></tr>
<tr><td><a href="/event?id=319319">Bounce and Rhyme and Storytime</a></td><td>2 November 2026 at 10:00 AM</td><td>Southall Library</td></tr>
</tbody></table></div>'''


class MyLibraryTests(unittest.TestCase):
    def fetch(self,url):
        return {URL:HTML,SERIES:SERIES_HTML,
                'https://ealing.events.mylibrary.digital/event?id=319318':HTML.replace('12 October 2026','19 October 2026'),
                'https://ealing.events.mylibrary.digital/event?id=319319':HTML.replace('12 October 2026','2 November 2026')}[url]
    def collect(self,**kwargs): return collect({'url':URL},TODAY,self.fetch,lambda _: (True,''),**kwargs)

    def test_detail_keeps_programme_type_cost_location_and_missing_age(self):
        item=parse_detail(HTML,URL)
        self.assertEqual(item['listing_type'],'activity')
        self.assertIsNone(item['age_range'])
        self.assertEqual(item['postcode'],'UB2 4BQ')
        self.assertEqual(item['cost_text'],'FREE')
        self.assertEqual(item['ics_url'],'https://ealing.events.mylibrary.digital/ics?id=319317')

    def test_exact_gaps_survive_normal_quality_cleaning(self):
        raw,_,_=self.collect()
        with patch.object(quality,'_resolve_venue',return_value=None):
            rows=quality.clean_events(raw,{'id':'test'},URL,'mylibrary_calendar',TODAY,{})
        self.assertEqual(len(rows),1)
        row=rows[0]
        self.assertEqual(row['start_date'],'2026-10-12')
        self.assertEqual(row['end_date'],'2026-11-02')
        self.assertIn('2026-10-19',row['schedule_text'])
        self.assertNotIn('2026-10-26',row['schedule_text'])
        self.assertNotIn('Every Monday',row['schedule_text'])

    def test_repeat_has_stable_key_and_hash_without_model_calls(self):
        a,ha,stats=self.collect(); b,hb,_=self.collect()
        self.assertEqual(ha,hb)
        with patch.object(quality,'_resolve_venue',return_value=None):
            clean=lambda raw: quality.clean_events(raw,{'id':'test'},URL,'mylibrary_calendar',TODAY,{})
            self.assertEqual(clean(a)[0]['dedupe_key'],clean(b)[0]['dedupe_key'])
        self.assertEqual(stats['gemini_logical_calls'],0)

    def test_series_change_changes_hash(self):
        _,before,_=self.collect()
        def fetch(url): return self.fetch(url).replace('2 November 2026','9 November 2026')
        _,after,_=collect({'url':URL},TODAY,fetch,lambda _: (True,''))
        self.assertNotEqual(before,after)

    def test_robots_failure_never_fetches_series(self):
        calls=[]
        def fetch(url): calls.append(url); return self.fetch(url)
        with self.assertRaisesRegex(CalendarError,'robots'):
            collect({'url':URL},TODAY,fetch,lambda u:(u!=SERIES,'disallow'))
        self.assertEqual(calls,[URL])

    def test_partial_requests_fail_without_hash(self):
        with self.assertRaisesRegex(CalendarError,'budget'): self.collect(max_requests=1)

    def test_shell_empty_and_incomplete_index_are_not_success(self):
        origin='https://ealing.events.mylibrary.digital/'
        for page in [Page('<title>Just a moment</title><div id="main">Please wait</div>'),
                     Page('<div id="main"><ul id="upcomingEventsList"></ul></div>',True),
                     Page('<div id="main"><ul id="upcomingEventsList"><a href="/event?id=319317">Family</a></ul></div>')]:
            with self.assertRaises(CalendarError): collect({'url':origin},TODAY,lambda _:page,lambda _:(True,''))

    def test_foreign_and_credential_urls_are_rejected(self):
        for url in ['https://evil.test/event?id=1','https://user@ealing.events.mylibrary.digital/event?id=1',
                    'https://ealing.events.mylibrary.digital:444/event?id=1']:
            with self.assertRaises(CalendarError): public_url(url,URL)

    def test_cancelled_and_conflicting_series_rows(self):
        def fetch(url):
            return self.fetch(url).replace('19 October 2026 at 10:00 AM','Cancelled 19 October 2026 at 10:00 AM') if url==SERIES else self.fetch(url)
        rows,_,_=collect({'url':URL},TODAY,fetch,lambda _:(True,''))
        self.assertNotIn('2026-10-19',rows[0]['occurrence_dates'])
        for before,after in [('Southall Library','Other Library'),('10:00 AM','12:00 PM')]:
            with self.assertRaisesRegex(CalendarError,'conflict'):
                collect({'url':URL},TODAY,lambda u:self.fetch(u).replace(before,after) if u==SERIES else HTML,lambda _:(True,''))

    def test_worker_adapter_failure_does_not_call_model_or_refresh(self):
        with patch('mylibrary_calendar.render_page',side_effect=CalendarError('partial snapshot')),patch.object(quality.base,'robots_allows',return_value=(True,'')):
            status,rows,digest,_,_=quality.process_source({'url':URL,'source_adapter':'mylibrary_calendar'},lambda _:self.fail('model called'),TODAY)
        self.assertEqual(status,'failed_fetch'); self.assertEqual(rows,[]); self.assertIsNone(digest)

    def test_worker_adapter_does_not_use_unchanged_source_refresh(self):
        with patch('mylibrary_calendar.render_page',side_effect=self.fetch),patch.object(quality.base,'robots_allows',return_value=(True,'')),patch.object(quality,'_resolve_venue',return_value=None):
            source={'id':'test','url':URL,'source_adapter':'mylibrary_calendar'}
            first=quality.process_source(source,lambda _:self.fail('model called'),TODAY)
            source.update(last_hash=first[2],last_success_at='2026-10-10')
            second=quality.process_source(source,lambda _:self.fail('model called'),TODAY)
        self.assertEqual(second[0],'ok'); self.assertEqual(first[1][0]['dedupe_key'],second[1][0]['dedupe_key'])

    def test_ics_utc_conversion_and_unbounded_recurrence_rejection(self):
        ics='BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:20261012T090000Z\r\nDTEND:20261012T100000Z\r\nEND:VEVENT\r\nEND:VCALENDAR'
        item=parse_ics(ics)
        self.assertEqual(item['time_text'],'10:00 AM - 11:00 AM')
        self.assertEqual(item['date'],'2026-10-12')
        with self.assertRaises(CalendarError): parse_ics(ics.replace('END:VEVENT','RRULE:FREQ=DAILY\r\nEND:VEVENT'))

    def test_dates_alone_do_not_decide_activity_or_event(self):
        item=parse_detail(HTML.replace('Every Monday',''),URL)
        self.assertEqual(item['listing_type'],'unknown')
        festival=HTML.replace('Every Monday','').replace('Bounce and Rhyme and Storytime','Annual family festival')
        self.assertEqual(parse_detail(festival,URL)['listing_type'],'event')

    def test_live_validation_cannot_hide_failed_sources_or_unstable_keys(self):
        from scripts.validate_mylibrary_sources import SOURCES, acceptance_errors
        results=[dict(name=name,status='ok',rows=[dict(dedupe_key=name)],
                      stats=dict(gemini_logical_calls=0)) for name,_ in SOURCES for _ in (1,2)]
        self.assertEqual(acceptance_errors(results),[])
        results[-1]['status']='failed_403'
        self.assertTrue(acceptance_errors(results))
        results[-1]['status']='ok'
        results[-1]['rows']=[dict(dedupe_key='changed')]
        self.assertTrue(acceptance_errors(results))

    def test_named_rhymetime_series_uses_regular_programme_evidence(self):
        url='https://events.sutton.gov.uk/event?id=364833'
        html=(Path(__file__).parent/'fixtures/mylibrary-sutton.html').read_text(encoding='utf-8')
        item=parse_detail(html,url)
        self.assertEqual(item['listing_type'],'unknown')
        self.assertIn('each child and adult',item['booking_text'])
        series='<main><table><tbody>'+''.join(
            '<tr><td><a href="/event?id='+str(i)+'">Rhymetime in Sutton Central Library</a></td>'
            '<td>'+date+' at 11:15 AM</td><td>Sutton Central Library</td><td>Ages 0-5</td></tr>'
            for i,date in [(364834,'19 October 2026'),(364835,'26 October 2026'),(364838,'16 November 2026')])+'</tbody></table></main>'
        def fetch(u):
            if '/series?' in u: return series
            if u.endswith('364834'): return html.replace('12 October 2026','19 October 2026')
            if u.endswith('364835'): return html.replace('12 October 2026','26 October 2026')
            return html
        rows,_,stats=collect({'url':url},TODAY,fetch,lambda _:(True,''))
        self.assertEqual(rows[0]['listing_type'],'activity')
        self.assertEqual(rows[0]['occurrence_dates'],['2026-10-12','2026-10-19','2026-10-26'])
        self.assertEqual(stats['collection_window_days'],30)
        festival=html.replace('Rhymetime in Sutton Central Library','Annual Rhymetime festival in Sutton Central Library')
        self.assertEqual(parse_detail(festival,url)['listing_type'],'event')

    def test_cancelled_detail_and_description_regularity(self):
        # Use the actual description section rather than unrelated paragraphs.
        from bs4 import BeautifulSoup
        soup=BeautifulSoup(HTML.replace('Every Monday',''),'html.parser')
        description=next(h for h in soup.select('h2') if h.get_text(strip=True)=='Event Description').find_next_sibling()
        description.string='This session is cancelled. Weekly storytime for families.'
        item=parse_detail(str(soup),URL)
        self.assertTrue(item['cancelled'])
        self.assertEqual(item['listing_type'],'activity')

    def test_historical_series_conflicts_do_not_block_current_window(self):
        item=parse_detail(HTML,URL)
        from mylibrary_calendar import series_dates
        historical='<main><table><tr><td><a href="/event?id=111">Old programme</a></td><td>1 January 2023 at 1:00 PM</td><td>Old venue</td></tr></table></main>'
        self.assertEqual(series_dates(historical,SERIES,item,first_date=TODAY.isoformat()),[])

    def test_occurrence_end_time_changes_and_cancelled_details(self):
        future='https://ealing.events.mylibrary.digital/event?id=319318'
        def changed(u): return self.fetch(u).replace('11:00 AM','11:30 AM') if u==future else self.fetch(u)
        with self.assertRaisesRegex(CalendarError,'time_text conflict'):
            collect({'url':URL},TODAY,changed,lambda _:(True,''))
        def cancelled(u): return self.fetch(u).replace('Bounce and Rhyme and Storytime','Cancelled Bounce and Rhyme and Storytime') if u==future else self.fetch(u)
        rows,_,_=collect({'url':URL},TODAY,cancelled,lambda _:(True,''))
        self.assertNotIn('2026-10-19',rows[0]['occurrence_dates'])

if __name__=='__main__': unittest.main()
