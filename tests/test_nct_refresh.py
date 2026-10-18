import datetime as dt
import unittest
from unittest.mock import patch
import nct_activity_loader as n
from collection_evidence import CollectionEvidence


class NCTRefreshTests(unittest.TestCase):
    def test_dry_run_does_not_count_writes_or_need_database(self):
        with patch.object(n,'DRY_RUN',True):
            self.assertEqual(n.flush(None,[{'dedupe_key':'a'}]),0)

    def test_partial_branch_failure_does_not_flush_or_renew_but_other_branch_runs(self):
        row={'dedupe_key':'a','start_date':'2026-10-19'}
        evidence=CollectionEvidence([{'id':'one'},{'id':'two'}],dry_run=True)
        with patch.object(n,'DRY_RUN',True), patch.object(n,'collect_branch',side_effect=[ValueError('partial'),[row]]), patch.object(n,'flush',return_value=0) as flush:
            self.assertEqual(n.run_refresh(None,{'id':'test'},['one','two'],evidence),1)
        self.assertEqual(flush.call_count,1)
        self.assertTrue(evidence.outcomes[0]['failed'])
        self.assertEqual(evidence.outcomes[1]['validated'],1)
        self.assertIsNone(evidence.outcomes[1]['saved_count'])

    def test_empty_yield_and_exhausted_or_repeated_pages_are_not_success(self):
        e=CollectionEvidence([{'id':'one'}],dry_run=True)
        with patch.object(n,'collect_branch',return_value=[]):
            self.assertEqual(n.run_refresh(None,{'id':'test'},['one'],e),1)
        row={'dedupe_key':'a','start_date':n.TODAY.isoformat()}
        with patch.object(n,'PAGE_LIMIT',1),patch.object(n,'page_events',return_value=n.EventPage([('1',row)],True)):
            with self.assertRaisesRegex(ValueError,'budget'): n.collect_branch('one')
        with patch.object(n,'page_events',return_value=n.EventPage([('1',row)],True)),patch.object(n.time,'sleep'):
            with self.assertRaisesRegex(ValueError,'Repeated'): n.collect_branch('one')
        with patch.object(n,'page_events',return_value=n.EventPage([],True)):
            with self.assertRaisesRegex(ValueError,'Empty'): n.collect_branch('one')

    def test_explicit_year_is_required_and_never_rolled_forward(self):
        import worker
        url=n.BASE+'/events/test/item'
        html='<script type="application/ld+json">{"@type":"Event","url":"'+url+'","startDate":"2025-10-19T10:00:00+01:00"}</script>'
        with patch.object(worker,'robots_allows',return_value=(True,'')),patch.object(worker,'fetch_html_requests',return_value=html):
            self.assertEqual(n.explicit_date(url),dt.date(2025,10,19))
        html=html.replace('2025-10-19T10:00:00+01:00','Monday 19 October 2026 10-00-00 UTC')
        with patch.object(worker,'robots_allows',return_value=(True,'')),patch.object(worker,'fetch_html_requests',return_value=html):
            self.assertEqual(n.explicit_date(url),dt.date(2026,10,19))
        with patch.object(worker,'robots_allows',return_value=(True,'')),patch.object(worker,'fetch_html_requests',return_value='<html>Oct 19</html>'):
            with self.assertRaisesRegex(ValueError,'year'): n.explicit_date(url)

    def test_disabled_live_refresh_fails_before_database_access(self):
        with patch.object(n,'DRY_RUN',False),patch.dict(n.os.environ,{'NCT_REFRESH_ENABLED':'false'}),patch.object(n,'create_client') as create:
            with self.assertRaisesRegex(ValueError,'activation'): n.main()
            create.assert_not_called()

    def test_window_uses_published_next_url_and_rejects_unordered_dates(self):
        first={'dedupe_key':'a','start_date':n.TODAY.isoformat()}
        later={'dedupe_key':'b','start_date':(n.TODAY+dt.timedelta(days=31)).isoformat()}
        next_url='https://www.nct.org.uk/local-activities-meet-ups/test?block_config_key=public&page=1'
        with patch.object(n,'page_events',side_effect=[n.EventPage([('1',first)],next_url),n.EventPage([('2',later)],None)]) as fetch,patch.object(n.time,'sleep'):
            self.assertEqual(n.collect_branch('branch'),[first])
            self.assertEqual(fetch.call_args_list[1].args,(next_url,0))
        with patch.object(n,'page_events',return_value=n.EventPage([('2',later),('1',first)],None)):
            with self.assertRaisesRegex(ValueError,'order'): n.collect_branch('branch')

    def test_save_failure_is_not_a_successful_health_update(self):
        evidence=CollectionEvidence([{'id':'one'}],dry_run=False)
        with patch.object(n,'DRY_RUN',False),patch.object(n,'collect_branch',return_value=[{'dedupe_key':'a'}]),patch.object(n,'flush',side_effect=RuntimeError('write unavailable')):
            self.assertEqual(n.run_refresh(None,{'id':'test'},['one'],evidence),1)
        self.assertEqual(evidence.outcomes[0]['write_state'],'failed')
        self.assertEqual(evidence.outcomes[0]['health_state'],'failed')
        self.assertIsNone(evidence.outcomes[0]['saved_count'])


if __name__=='__main__': unittest.main()
