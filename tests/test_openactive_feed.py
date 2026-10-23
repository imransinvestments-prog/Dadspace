import datetime as dt
import json
import unittest
from unittest.mock import patch

import openactive
import openactive_feed

TODAY = dt.date(2026, 10, 23)
DATASET = 'https://leisure.example/OpenActive/'
SERIES_FEED = 'https://feeds.example/session-series'
COURSE_FEED = 'https://feeds.example/course-instance'
LICENCE = 'https://creativecommons.org/licenses/by/4.0/'


def dataset_page(licence=LICENCE, feeds=(('SessionSeries', SERIES_FEED),)):
    data = {'@type': 'Dataset', 'name': 'Example Leisure Sessions', 'license': licence,
            'publisher': {'name': 'Example Leisure'},
            'distribution': [{'additionalType': 'https://openactive.io/' + kind, 'contentUrl': url} for kind, url in feeds]}
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def series(identifier, name='Soft Play', days=('Monday',), start='10:00', end='11:00', age=None,
           place='Acton Centre', **extra):
    parent = {'@type': 'EventSeries', 'name': name, 'description': 'Play  for little ones.',
              'ageRange': age if age is not None else {'minValue': 0, 'maxValue': 5},
              'activity': [{'prefLabel': 'Soft Play'}]}
    data = {'@type': 'SessionSeries', '@id': 'https://leisure.example/series/' + identifier, 'name': name,
            'url': 'https://leisure.example/centres/acton',
            'eventSchedule': [{'@type': 'PartialSchedule', 'byDay': ['https://schema.org/' + d for d in days],
                               'startTime': start, 'endTime': end, 'startDate': '2025-01-06'}],
            'location': {'name': place, 'address': {'streetAddress': '1 High Street', 'addressLocality': 'Acton',
                                                    'postalCode': 'W3 9LN'}},
            'offers': [{'identifier': 'ADULT', 'price': 4.5}, {'identifier': 'STAFF', 'price': 1}],
            'superEvent': parent}
    data.update(extra)
    return data


def page(items, following=None):
    return {'items': [{'id': i.get('@id', str(n)), 'state': 'updated', 'data': i} for n, i in enumerate(items)],
            'next': following}


class Response:
    def __init__(self, payload=None, text=''):
        self.status_code, self.payload, self.text = 200, payload, text

    def json(self):
        return self.payload

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, responses):
        self.responses, self.headers, self.urls = responses, {}, []

    def get(self, url, timeout):
        self.urls.append(url)
        return self.responses[url].pop(0)


def client(responses):
    return openactive.Client(delay=0, retries=0, session=Session(responses), sleep=lambda _: None)


def allow(_):
    return True, ''


class ScheduleTests(unittest.TestCase):
    def test_weekly_slots_merge_days_sharing_a_time(self):
        slots, end = openactive_feed.schedule_slots([
            {'byDay': ['https://schema.org/Wednesday', 'https://schema.org/Monday'], 'startTime': '10:00', 'endTime': '11:00'},
            {'byDay': ['Saturday'], 'startTime': '09:00', 'endTime': '09:30', 'endDate': '2026-12-31'}], TODAY)
        self.assertIsNone(end)
        self.assertEqual(openactive_feed.schedule_text(slots), 'Weekly: Mon, Wed 10:00–11:00; Sat 09:00–09:30')

    def test_days_sharing_a_timetable_compact_to_ranges(self):
        slots = {(day, start, end) for day in openactive_feed.DAYS[:5]
                 for start, end in (('09:00', '12:00'), ('15:00', '18:00'))}
        slots |= {('Sunday', '09:00', '12:00'), ('Saturday', '09:00', '12:00')}
        self.assertEqual(openactive_feed.schedule_text(slots),
                         'Weekly: Mon–Fri 09:00–12:00, 15:00–18:00; Sat, Sun 09:00–12:00')

    def test_missing_weekday_or_other_frequency_is_never_guessed(self):
        self.assertEqual(openactive_feed.schedule_slots([{'startTime': '18:00'}], TODAY), 'schedule_without_weekday')
        self.assertEqual(openactive_feed.schedule_slots(
            [{'byDay': ['Monday'], 'startTime': '18:00', 'repeatFrequency': 'P1M'}], TODAY), 'schedule_not_weekly')
        self.assertEqual(openactive_feed.schedule_slots(None, TODAY), 'schedule_missing')

    def test_ended_parts_drop_and_bounded_series_keep_their_end(self):
        schedules = [{'byDay': ['Monday'], 'startTime': '10:00', 'endDate': '2026-01-01'},
                     {'byDay': ['Friday'], 'startTime': '10:00', 'endDate': '2026-12-18'}]
        slots, end = openactive_feed.schedule_slots(schedules, TODAY)
        self.assertEqual(slots, {('Friday', '10:00', None)})
        self.assertEqual(end, dt.date(2026, 12, 18))
        self.assertEqual(openactive_feed.schedule_slots(schedules[:1], TODAY), 'schedule_ended')


class SeriesTests(unittest.TestCase):
    def test_series_inherits_age_from_its_parent_and_skips_staff_prices(self):
        row = openactive_feed.series_row(series('a'), TODAY)
        self.assertNotIn('skip', row)
        self.assertEqual((row['minimum'], row['maximum'], row['prices']), (0, 5, [4.5]))
        self.assertEqual(row['address'], '1 High Street, Acton')

    def test_slot_names_drop_their_day_and_time_so_slots_group(self):
        for name in ('Soft Play Mon 12:00', 'Athletics 11-15 Wed 1800', 'Tennis 7-11 Thu 7-11', 'Swim Tuesdays'):
            self.assertNotRegex(openactive_feed.series_name(name), r'(?i)mon|wed|thu|tue')
        self.assertEqual(openactive_feed.series_name('Soft Play Mon 12:00'), 'Soft Play')
        self.assertEqual(openactive_feed.series_name('Monday'), 'Monday')
        self.assertEqual(openactive_feed.series_name('Sunday Funday Soft Play'), 'Sunday Funday Soft Play')

    def test_adult_open_and_cancelled_series_are_counted_skips(self):
        self.assertEqual(openactive_feed.series_row(series('a', age={'minValue': 18}), TODAY)['skip'], 'age_outside')
        self.assertEqual(openactive_feed.series_row(series('a', age={'minValue': 0, 'maxValue': 110}), TODAY)['skip'],
                         'age_unbounded')
        self.assertEqual(openactive_feed.series_row(series('a', age={}), TODAY)['skip'], 'age_unknown')
        self.assertEqual(openactive_feed.series_row(
            series('a', eventStatus='https://schema.org/EventCancelled'), TODAY)['skip'], 'cancelled')
        self.assertEqual(openactive_feed.series_row(series('a', name='Soft Play Party'), TODAY)['skip'], 'private_hire')
        broad = {'minValue': 5, 'maxValue': 15}
        self.assertEqual(openactive_feed.series_row(series('a', name='Athletics 11-15 Wed 1800', age=broad), TODAY)['skip'],
                         'age_name_outside')
        self.assertNotIn('skip', openactive_feed.series_row(series('a', name='Tennis 5-7', age=broad), TODAY))

    def test_series_with_one_name_and_centre_become_one_activity(self):
        rows = [openactive_feed.series_row(series('a'), TODAY),
                openactive_feed.series_row(series('b', days=('Thursday',), start='13:00', end='14:00',
                                                  age={'minValue': 1, 'maxValue': 8}), TODAY),
                openactive_feed.series_row(series('c', name='Toddler Swim'), TODAY)]
        items, too_long = openactive_feed.activity_items(rows, 'Example Leisure')
        self.assertEqual(too_long, 0)
        play = next(i for i in items if i['title'] == 'Soft Play')
        self.assertEqual(play['schedule_text'], 'Weekly: Mon 10:00–11:00; Thu 13:00–14:00')
        self.assertEqual(play['age_range'], 'Up to 8 years')
        self.assertEqual(play['cost_text'], '£4.50 per session; check booking page')
        self.assertEqual(play['category'], 'baby_toddler')
        self.assertTrue(play['description'].endswith('Session data: Example Leisure via OpenActive, CC BY 4.0.'))
        self.assertEqual(next(i for i in items if i['title'] == 'Toddler Swim')['category'], 'swimming')

    def test_schedule_too_long_for_storage_needs_review_not_truncation(self):
        rows = [openactive_feed.series_row(series(str(h), days=('Monday',), start=f'{h:02d}:00', end=f'{h:02d}:30'), TODAY)
                for h in range(24)]
        items, too_long = openactive_feed.activity_items(rows, 'Example Leisure')
        self.assertEqual((items, too_long), ([], 1))


class CollectTests(unittest.TestCase):
    def test_collect_walks_series_feeds_and_counts_skips(self):
        responses = {DATASET: [Response(text=dataset_page(feeds=(('SessionSeries', SERIES_FEED),
                                                                 ('CourseInstance', COURSE_FEED),
                                                                 ('FacilityUse', 'https://feeds.example/facility'))))],
                     SERIES_FEED: [Response(page([series('a'), series('adult', name='Badminton', age={'minValue': 18})],
                                                 SERIES_FEED + '?after=2'))],
                     SERIES_FEED + '?after=2': [Response(page([]))],
                     COURSE_FEED: [Response(page([series('c', name='Swim Stage 1')]))]}
        stats = {}
        items, digest = openactive_feed.collect({'url': DATASET}, TODAY, allow, stats, client=client(responses))
        self.assertEqual(sorted(i['title'] for i in items), ['Soft Play', 'Swim Stage 1'])
        self.assertEqual(stats['openactive_age_outside'], 1)
        self.assertEqual((stats['requests'], stats['gemini_logical_calls'], stats['extracted']), (4, 0, 2))
        self.assertEqual(len(digest), 64)

    def test_unreviewed_licence_incomplete_feed_and_robots_refuse(self):
        with self.assertRaisesRegex(ValueError, 'licence'):
            openactive_feed.collect({'url': DATASET}, TODAY, allow, {}, client=client(
                {DATASET: [Response(text=dataset_page(licence='https://example.org/terms'))]}))
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            openactive_feed.collect({'url': DATASET}, TODAY, allow, {}, max_pages=1, client=client(
                {DATASET: [Response(text=dataset_page())],
                 SERIES_FEED: [Response(page([series('a')], SERIES_FEED + '?after=1'))]}))
        with self.assertRaisesRegex(ValueError, 'Robots'):
            openactive_feed.collect({'url': DATASET}, TODAY, lambda url: (url != SERIES_FEED, 'disallowed'), {},
                                    client=client({DATASET: [Response(text=dataset_page())]}))


class WorkerTests(unittest.TestCase):
    def test_worker_stores_feed_items_as_recurring_activities(self):
        import events_worker
        responses = {DATASET: [Response(text=dataset_page())], SERIES_FEED: [Response(page([series('a')]))]}
        source = {'id': 'source-1', 'url': DATASET, 'source_adapter': 'openactive_feed', 'name': 'Example'}
        polite = client(responses)
        with patch.object(openactive, 'Client', lambda: polite), \
                patch.object(events_worker, '_resolve_venue', lambda item, url: None):
            status, rows, digest, message, stats = events_worker.process_source(source, None, TODAY)
        self.assertEqual(status, 'ok', message)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row['listing_type'], row['recurrence'], row['extraction_method']),
                         ('activity', 'recurring', 'openactive_feed'))
        self.assertEqual(row['schedule_text'], 'Weekly: Mon 10:00–11:00')
        self.assertEqual(row['postcode'], 'W3 9LN')
        self.assertIn('zero model calls', message)


if __name__ == '__main__':
    unittest.main()
