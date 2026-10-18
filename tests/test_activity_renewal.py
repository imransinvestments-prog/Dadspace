"""Bounded MyLibrary renewal preserves unseen records and explicit uncertainty."""
import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

import events_worker as quality
from mylibrary_calendar import CalendarError, Page, collect

URL = 'https://ealing.events.mylibrary.digital/event?id=319317'
SERIES = 'https://ealing.events.mylibrary.digital/series?si=319285'
HTML = (Path(__file__).parent/'fixtures/mylibrary-southall.html').read_text(encoding='utf-8')
TODAY = dt.date(2026,10,11)


class RenewalTests(unittest.TestCase):
    def fetch(self, url):
        if url == SERIES:
            return '''<main><table id="resultsTable"><tbody>
            <tr><td><a href="/event?id=319317">Bounce and Rhyme and Storytime</a></td><td>12 October 2026 at 10:00 AM</td><td>Southall Library</td></tr>
            </tbody></table></main>'''
        return HTML

    def test_unchanged_detail_is_revalidated_without_blanket_source_refresh(self):
        source = {'id': 'source', 'url': URL, 'source_adapter': 'mylibrary_calendar',
                  'last_hash': 'old', 'last_success_at': '2026-10-11T00:00:00Z'}
        with patch('mylibrary_calendar.render_page', side_effect=self.fetch), \
             patch.object(quality.base,'robots_allows',return_value=(True,'')), \
             patch.object(quality,'_resolve_venue',return_value=None):
            result = quality.process_source(source,lambda _:self.fail('model called'),TODAY)
        self.assertEqual(result[0],'ok')
        coverage = result[-1]['item_coverage']
        self.assertTrue(coverage['complete'])
        self.assertEqual(coverage['included_urls'],[URL])
        self.assertEqual(coverage['renewal'],'accepted_rows_only')
        self.assertEqual(coverage['unseen'],'retain_without_refresh')
        self.assertNotEqual(result[0],'unchanged')

    def test_cancelled_detail_is_not_renewed_or_converted_to_withdrawal(self):
        cancelled = HTML.replace('<h1>Bounce','<h1>Cancelled Bounce')
        raw, _, stats = collect({'url':URL},TODAY,lambda _:cancelled,lambda _:(True,''))
        self.assertEqual(raw,[])
        self.assertEqual(stats['item_coverage']['included_urls'],[])
        self.assertEqual(stats['item_coverage']['withheld'],[{'url':URL,'reason':'cancelled'}])
        self.assertIn('no_automatic_withdrawal',stats['item_coverage']['cancellation'])

    def test_partial_failure_retains_checked_urls_but_never_complete_coverage(self):
        stats = {}
        with self.assertRaises(CalendarError):
            collect({'url':URL},TODAY,self.fetch,lambda _:(True,''),stats=stats,max_requests=1)
        self.assertFalse(stats['item_coverage']['complete'])
        self.assertEqual(stats['item_coverage']['checked_urls'],[URL])

    def test_incomplete_root_and_network_failure_do_not_claim_disappearance(self):
        for fetch in (lambda _:Page('<main><ul id="upcomingEventsList"></ul></main>'),
                      lambda _: (_ for _ in ()).throw(RuntimeError('network unavailable'))):
            stats = {}
            with self.assertRaises((CalendarError,RuntimeError)):
                collect({'url':'https://events.sutton.gov.uk/'},TODAY,fetch,lambda _:(True,''),stats=stats)
            self.assertFalse(stats['item_coverage']['complete'])
            self.assertEqual(stats['item_coverage']['unseen'],'retain_without_refresh')


if __name__=='__main__': unittest.main()
