import unittest
from activity_dates import published_date_fields, enrich_dates

class PublishedActivityDateTests(unittest.TestCase):
    def test_hay_monthly_exception_is_preserved_without_invented_dates(self):
        html='<h1>Saturdads</h1><div class="prose"><p>First Saturday of each month 9.30am - 11.30am, excluding December.</p></div>'
        fields=published_date_fields(html,'https://haysouthcambs.co.uk/activities/saturdads/','Saturdads')
        self.assertIsNone(fields['start_date'])
        self.assertEqual(fields['occurrence_dates'],[])
        self.assertIn('excluding December',fields['schedule_text'])

    def test_hoop_copies_published_session_not_generated_repeats(self):
        import json
        url='https://hoop.co.uk/e/example/'
        event=dict(name='Little Forts',url=url,startDate='2026-10-14T08:45:00Z',endDate='2026-10-14T10:15:00Z')
        event['@type']='Event'
        html='<h1>Little Forts</h1><li>08:45 - 10:15</li><p>Repeats weekly</p><script type="application/ld+json">'+json.dumps(event)+'</script>'
        fields=published_date_fields(html,url,'Little Forts')
        self.assertEqual(fields['occurrence_dates'],['2026-10-14'])
        with self.assertRaisesRegex(ValueError,'clocks disagree'):
            published_date_fields(html.replace('<li>08:45','<li>09:45'),url,'Little Forts')
    def test_oxfordshire_dates_exclude_related_listing_and_preserve_gap(self):
        html='<h1>Botley: Rhymetime</h1><div><h2>Dates</h2><p>Friday 16 Oct 2026, 10am-10.30am</p><p>Friday 30 Oct 2026, 10am-10.30am</p></div><h2>Related</h2><p>1 Nov 2026</p>'
        fields=published_date_fields(html,'https://www.oxfordshire.gov.uk/events/libraries/botley-rhymetime-0','Botley: Rhymetime')
        self.assertEqual(fields['occurrence_dates'],['2026-10-16','2026-10-30'])
        self.assertNotIn('2026-11-01',str(fields))

    def test_coventry_bounds_do_not_expand_fortnightly_term_time(self):
        html='<h1>Tots Time</h1><div class="editor">Meet during term time.</div><div class="page-meta"><p><strong>Date: </strong>9th July 2026 - 8th January 2027 Recurs every other week on Thursday.</p><p><strong>Time: </strong>10:00 - 11:15</p></div>'
        fields=published_date_fields(html,'https://www.coventry.gov.uk/events/event/8828/tots-time','Tots Time')
        self.assertEqual(fields['start_date'],'2026-07-09')
        self.assertEqual(fields['end_date'],'2027-01-08')
        self.assertEqual(fields['occurrence_dates'],[])
        self.assertIn('term time only',fields['schedule_text'])
        self.assertIn('10:00 - 11:15',fields['schedule_text'])

    def test_title_mismatch_and_robots_failure_cannot_refresh(self):
        with self.assertRaises(ValueError):
            published_date_fields('<h1>Other event</h1>','https://www.oxfordshire.gov.uk/events/x','Botley')
        item=dict(title='Botley',listing_type='activity',event_url='https://www.oxfordshire.gov.uk/events/x')
        with self.assertRaisesRegex(ValueError,'robots'):
            enrich_dates([item],dict(url='https://www.oxfordshire.gov.uk/events'),lambda _:self.fail('must not fetch'),lambda _:(False,'disallowed'),{})

    def test_healthy_other_hosts_get_no_additional_fetch(self):
        item=dict(title='Family club',listing_type='activity')
        self.assertEqual(enrich_dates([item],dict(url='https://other.test/'),lambda _:self.fail(),lambda _:self.fail(),{}),[item])
