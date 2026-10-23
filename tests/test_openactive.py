import unittest
import openactive
from activity_eligibility import PILOT

NEAR = {'name': 'Acton Pool', 'geo': {'latitude': PILOT[0], 'longitude': PILOT[1]},
        'address': {'postalCode': 'W3 9LN'}}
FAR = {'name': 'Leeds Pool', 'geo': {'latitude': '53.8', 'longitude': '-1.55'}}


class Response:
    def __init__(self, status, payload=None, text=''):
        self.status_code, self.payload, self.text = status, payload, text

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


class Session:
    def __init__(self, responses):
        self.responses, self.headers, self.urls = responses, {}, []

    def get(self, url, timeout):
        self.urls.append(url)
        return self.responses[url].pop(0)


def client(responses):
    return openactive.Client(delay=0, session=Session(responses), sleep=lambda seconds: None)


class OpenActiveTests(unittest.TestCase):
    def test_age_range_overlap_keeps_unknowns(self):
        self.assertEqual(openactive.age_evidence({'minValue': 0, 'maxValue': 4})['state'], 'eligible')
        self.assertEqual(openactive.age_evidence({'maxValue': 3})['state'], 'eligible')
        self.assertEqual(openactive.age_evidence({'minValue': 5, 'maxValue': 11})['state'], 'eligible')
        self.assertEqual(openactive.age_evidence({'minValue': 6})['state'], 'outside')
        self.assertEqual(openactive.age_evidence({'minValue': 16})['state'], 'outside')
        for value in (None, {}, {'minValue': 'adult'}, {'minValue': 8, 'maxValue': 2}):
            self.assertEqual(openactive.age_evidence(value)['state'], 'unknown', value)
        # Adult classes defaulted to "0–110" are not early-years evidence.
        for value in ({'minValue': 0, 'maxValue': 110}, {'minValue': 0}, {'maxValue': 18}):
            self.assertEqual(openactive.age_evidence(value)['state'], 'unbounded', value)

    def test_postcode_centroid_only_fills_missing_coordinates(self):
        place = {'address': {'postalCode': 'TW8 0HJ'}}
        located = openactive.location_evidence(place, {'TW80HJ': (51.490962, -0.284769)})
        self.assertEqual((located['state'], located['method']), ('local', 'postcode_centroid'))
        self.assertEqual(openactive.location_evidence(place, {'TW80HJ': None})['state'], 'unknown')
        self.assertEqual(openactive.location_evidence(FAR, {'W39LN': PILOT})['method'], 'feed_coordinates')

    def test_postcode_cache_resolves_in_batches_and_records_misses(self):
        class Lookup:
            calls = []

            def post(self, url, json, timeout):
                self.calls.append(json['postcodes'])
                result = [{'query': p, 'result': {'latitude': 51.5, 'longitude': -0.2} if p == 'W39LN' else None}
                          for p in json['postcodes']]
                return Response(200, {'result': result})
        cache = openactive.Postcodes(session=Lookup())
        self.assertEqual(cache.resolve({'W39LN', 'ZZ11ZZ'}), {'W39LN': (51.5, -0.2), 'ZZ11ZZ': None})
        cache.resolve({'W39LN'})
        self.assertEqual(len(Lookup.calls), 1)

    def test_provider_subdomains_share_one_pacing_queue(self):
        self.assertEqual(openactive.host_group('https://halo-openactive.legendonlineservices.co.uk/OpenActive'),
                         openactive.host_group('https://gll-openactive.legendonlineservices.co.uk/OpenActive'))
        self.assertEqual(openactive.host_group('https://data.bookwhen.com/'), 'bookwhen.com')

    def test_legacy_events_without_ids_group_by_name_and_place(self):
        event = {'type': 'Event', 'name': 'Swim lessons', 'location': NEAR, 'ageRange': {'minValue': 4, 'maxValue': 8}}
        summary = openactive.summarise([event, dict(event), dict(event, name='HIIT', ageRange={'minValue': 0, 'maxValue': 110})])
        self.assertEqual((summary['series'], summary['pilot_eligible']), (2, 1))

    def test_location_needs_real_coordinates(self):
        self.assertEqual(openactive.location_evidence(NEAR)['state'], 'local')
        self.assertEqual(openactive.location_evidence(FAR)['state'], 'outside')
        missing = openactive.location_evidence({'address': 'Hall, W3 9LN'})
        self.assertEqual((missing['state'], missing['postcode']), ('unknown', 'W39LN'))
        self.assertEqual(openactive.location_evidence({'geo': {'latitude': 0, 'longitude': 0}})['state'], 'unknown')
        self.assertEqual(openactive.location_evidence('W3 9LN')['state'], 'unknown')

    def test_session_inherits_series_and_never_copies_person_contacts(self):
        session = {'@type': 'ScheduledSession', 'startDate': '2026-11-02T10:00:00Z',
                   'superEvent': {'@type': 'SessionSeries', '@id': 'series-1', 'name': 'Toddler splash',
                                  'ageRange': {'minValue': 1, 'maxValue': 4}, 'location': NEAR,
                                  'organizer': {'@type': 'Person', 'name': 'A Coach', 'email': 'coach@example.test'},
                                  'activity': [{'prefLabel': 'Swimming'}]}}
        row = openactive.opportunity(session)
        self.assertEqual((row['series_id'], row['name'], row['age']['state'], row['location']['state']),
                         ('series-1', 'Toddler splash', 'eligible', 'local'))
        self.assertTrue(row['has_schedule'])
        self.assertIsNone(row['organizer'])
        self.assertNotIn('coach@example.test', repr(row))
        series = openactive.opportunity({'@type': 'SessionSeries', '@id': 's2',
                                         'organizer': {'@type': 'Organization', 'name': 'GLL', 'telephone': '0'}})
        self.assertEqual(series['organizer'], 'GLL')
        self.assertFalse(series['has_schedule'])

    def test_summary_counts_each_series_once(self):
        series = {'@type': 'SessionSeries', '@id': 's1', 'name': 'Baby swim', 'location': NEAR,
                  'ageRange': {'maxValue': 2}, 'eventSchedule': [{'byDay': ['Monday']}]}
        sessions = [{'type': 'ScheduledSession', 'superEvent': series} for _ in range(3)]
        far = {'@type': 'SessionSeries', '@id': 's3', 'location': FAR, 'ageRange': {'maxValue': 4}}
        unknown = {'@type': 'SessionSeries', '@id': 's4', 'location': NEAR}
        summary = openactive.summarise([series, *sessions, far, unknown])
        self.assertEqual((summary['series'], summary['local'], summary['pilot_eligible'],
                          summary['pilot_eligible_with_schedule'], summary['local_age_unknown']), (3, 2, 1, 1, 1))
        self.assertEqual(summary['pilot_activity_labels'], {'(no activity label)': 1})

    def test_rpde_walk_applies_deletes_and_stops_at_last_page(self):
        responses = {
            'feed': [Response(200, {'next': 'feed?p=2', 'items': [
                {'state': 'updated', 'id': 1, 'data': {'name': 'old'}},
                {'state': 'updated', 'id': 2, 'data': {'name': 'gone'}}]})],
            'https://x.test/feed?p=2': [Response(200, {'next': '/feed?p=3', 'items': [
                {'state': 'updated', 'id': 1, 'data': {'name': 'new'}}, {'state': 'deleted', 'id': 2}]})],
            'https://x.test/feed?p=3': [Response(200, {'next': 'https://x.test/feed?p=3', 'items': []})],
        }
        responses['https://x.test/feed'] = responses.pop('feed')
        responses['https://x.test/feed'][0].payload['next'] = 'https://x.test/feed?p=2'
        outcome = openactive.walk_feed('https://x.test/feed', client(responses))
        self.assertEqual((outcome['pages'], outcome['complete']), (3, True))
        self.assertEqual(outcome['items'], {1: {'name': 'new'}})

    def test_rpde_walk_retries_rate_limits_and_reports_partial_walks(self):
        responses = {'feed': [Response(403), Response(200, {'next': 'feed?p=2', 'items': [
            {'state': 'updated', 'id': 1, 'data': {}}]})]}
        session_client = client(responses)
        outcome = openactive.walk_feed('feed', session_client, max_pages=1)
        self.assertEqual((outcome['pages'], outcome['complete'], outcome['error']), (1, False, None))
        failing = openactive.Client(delay=0, retries=1, session=Session({'feed': [Response(403), Response(403)]}),
                                    sleep=lambda seconds: None)
        self.assertIn('HTTP 403', openactive.walk_feed('feed', failing)['error'])

    def test_dataset_description_selects_opportunity_feeds(self):
        html = '''<script type="application/ld+json">{"@type":"Dataset","name":"Halo","license":"https://creativecommons.org/licenses/by/4.0/",
          "publisher":{"name":"Halo"},"distribution":[
          {"additionalType":"https://openactive.io/SessionSeries","contentUrl":"series"},
          {"additionalType":"https://openactive.io/ScheduledSession","contentUrl":"sessions"},
          {"additionalType":"https://openactive.io/FacilityUse","contentUrl":"facilities"}]}</script>'''
        description = openactive.dataset_description(html)
        self.assertEqual(description['license'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual([f['url'] for f in openactive.feeds_to_walk(description['feeds'])], ['series'])
        sessions_only = [{'type': 'ScheduledSession', 'url': 'sessions'}, {'type': None, 'url': 'legacy'}]
        self.assertEqual([f['url'] for f in openactive.feeds_to_walk(sessions_only)], ['legacy', 'sessions'])
        self.assertIsNone(openactive.dataset_description('<html></html>'))


if __name__ == '__main__':
    unittest.main()
