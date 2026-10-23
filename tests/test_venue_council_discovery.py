import datetime as dt
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import venue_council_discovery as cd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / 'tests/fixtures/council-discovery/overpass-sample.json').read_text(encoding='utf-8'))
EALING = {'code': 'E09000009', 'name': 'Ealing'}
NO_AREA = {'elements': [e for e in SAMPLE['elements'] if e['type'] != 'area']}


def spots():
    return cd.spots_from_overpass(SAMPLE)[1]


def by_name(items):
    return {s['name']: s for s in items}


def keep_postcodes(items, code):
    for s in items:
        s['postcode'] = cd.norm_postcode(s['tags'].get('addr:postcode')) or None
        s['postcode_source'] = 'osm_tag' if s['postcode'] else None
        s['council_check'] = 'test'
    return items


def discover(index=None, generator=None, fetch=lambda code: SAMPLE):
    return cd.discover_council(EALING, index or cd.VenueIndex([]), generator, fetch=fetch, resolve=keep_postcodes)


class FakeQuery:
    def __init__(self, db, table):
        self.db, self.table, self.filters, self.payload = db, table, [], None

    def __getattr__(self, name):
        def chain(*args, **kwargs):
            self.filters.append((name, args, kwargs))
            if name in ('insert', 'upsert'):
                self.payload = args[0]
            return self
        return chain

    def execute(self):
        self.db.calls.append((self.table, self.filters, self.payload))
        result = self.db.responses.get(self.table, [])
        return type('Result', (), {'data': result(self) if callable(result) else result})()


class FakeDB:
    def __init__(self, responses=None):
        self.responses, self.calls = responses or {}, []

    def table(self, name):
        return FakeQuery(self, name)


class FakeGenerator:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.prompts = reply, error, []

    def generate(self, prompt, schema):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.reply


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out, True)


class OverpassParsingTests(unittest.TestCase):
    def test_boundary_and_named_family_places_only(self):
        boundary, found = cd.spots_from_overpass(SAMPLE)
        names = set(by_name(found))
        self.assertTrue(boundary)
        self.assertIn('Horsenden Hill', names)
        self.assertNotIn('Private Gardens', names)  # access=private

    def test_parks_and_playgrounds_are_never_discovered(self):
        # Owner decision 23 Oct 2026 (#243): they rarely change, so this feed leaves them out.
        found = spots()
        self.assertFalse([s for s in found if s['tags'].get('leisure') in ('park', 'playground')])
        self.assertNotIn('Walpole Park', by_name(found))
        self.assertNotIn('playground', cd.overpass_query('E09000009'))
        self.assertNotIn('|park|', cd.overpass_query('E09000009'))

    def test_new_types_and_their_filters(self):
        found = by_name(spots())
        self.assertEqual({n: found[n]['category'] for n in (
            'Ealing Film Studios Tour', 'Example Castle', 'Questors Arts Centre', 'Hedge Maze',
            'Example Planetarium', 'Treetop Ropes', 'Bounce Ealing', 'Ash Mini Golf')}, {
            'Ealing Film Studios Tour': 'Attraction', 'Example Castle': 'Castle',
            'Questors Arts Centre': 'Arts centre', 'Hedge Maze': 'Maze',  # maze rule wins over attraction
            'Example Planetarium': 'Planetarium', 'Treetop Ropes': 'Adventure / high ropes',
            'Bounce Ealing': 'Trampoline venue', 'Ash Mini Golf': 'Mini golf'})
        self.assertNotIn('Big Dipper', found)  # a single ride is part of another place
        self.assertNotIn('Old Milestone', found)  # attraction with no website or Wikidata
        self.assertNotIn('Motte Earthwork', found)  # castle with no website or opening hours

    def test_libraries_are_never_discovered(self):
        # Owner decision 23 Oct 2026 (#243): the library reference source already covers them.
        self.assertFalse([s for s in spots() if s['tags'].get('amenity') == 'library'])
        self.assertNotIn('library', cd.overpass_query('E09000009'))

    def test_missing_boundary_is_reported(self):
        self.assertFalse(cd.spots_from_overpass(NO_AREA)[0])

    def test_way_centre_comes_from_bounds_and_petting_zoo_is_a_farm(self):
        found = by_name(spots())
        self.assertAlmostEqual(found['Horsenden Hill']['lat'], 51.50915, places=4)
        self.assertEqual(found['Northolt City Farm']['category'], 'Farm')
        self.assertEqual(found['Ash Mini Golf']['category'], 'Mini golf')

    def test_query_scopes_to_the_council_boundary(self):
        query = cd.overpass_query('E09000009')
        self.assertIn('area["ref:gss"="E09000009"]', query)
        self.assertIn('.a out ids;', query)


class RankingTests(unittest.TestCase):
    def test_order_and_no_cap(self):
        # Owner decision 23 Oct 2026 (#243): every new place is kept; the rank only orders them.
        ranked = cd.rank(spots())
        self.assertEqual(ranked[0]['name'], 'Pitzhanger Manor House and Gallery')
        self.assertEqual(len(ranked), len(spots()))
        self.assertGreater(len(ranked), cd.NOTES_TOP_N)
        self.assertEqual([s['rank'] for s in ranked], list(range(1, len(ranked) + 1)))

    def test_notes_are_drafted_for_the_top_ten_only(self):
        generator = FakeGenerator(reply=[])
        stats, records = discover(generator=generator)
        self.assertGreater(len(records), cd.NOTES_TOP_N)
        self.assertEqual(len(generator.prompts), 1)
        top = [r['name'] for r, _ in records[:cd.NOTES_TOP_N]]
        rest = [r['name'] for r, _ in records[cd.NOTES_TOP_N:]]
        self.assertTrue(all(name in generator.prompts[0] for name in top))
        self.assertFalse(any(name in generator.prompts[0] for name in rest))

    def test_ranking_is_reproducible(self):
        self.assertEqual([s['osm_id'] for s in cd.rank(spots())],
                         [s['osm_id'] for s in cd.rank(list(reversed(spots())))])


class DedupTests(unittest.TestCase):
    def setUp(self):
        self.found = by_name(spots())

    def test_existing_osm_element_is_skipped(self):
        index = cd.VenueIndex([{'id': 'v1', 'venue_name': 'Pitzhanger Manor',
                                'source_url': 'https://www.openstreetmap.org/node/27408513'}])
        self.assertEqual(cd.match_existing(self.found['Pitzhanger Manor House and Gallery'], index)[0], 'existing')

    def test_same_name_and_postcode_is_skipped(self):
        index = cd.VenueIndex([{'id': 'v2', 'venue_name': 'Pitzhanger Manor House & Gallery', 'postcode': 'W55EQ',
                                'latitude': 51.52, 'longitude': -0.31, 'source_url': 'reference:Some Source:1'}])
        self.assertEqual(cd.match_existing(self.found['Pitzhanger Manor House and Gallery'], index)[0], 'existing')

    def test_close_and_similar_is_skipped(self):
        park = self.found['Horsenden Hill']
        index = cd.VenueIndex([{'id': 'v3', 'venue_name': 'Horsenden Hill Ealing',
                                'latitude': park['lat'] + 0.0003, 'longitude': park['lng']}])
        self.assertEqual(cd.match_existing(park, index)[0], 'existing')

    def test_near_miss_is_flagged_not_dropped(self):
        museum = self.found['Pitzhanger Manor House and Gallery']
        index = cd.VenueIndex([{'id': 'v4', 'venue_name': 'Pitzhanger Manor', 'postcode': 'W5 5XX',
                                'latitude': museum['lat'] + 0.001, 'longitude': museum['lng']}])  # ~110 m
        outcome, venue = cd.match_existing(museum, index)
        self.assertEqual((outcome, venue['id']), ('possible', 'v4'))

    def test_direct_database_check_catches_what_the_index_missed(self):
        # 22 Oct dry run: Hanwell Zoo (way/221351281) was stored but offered as new.
        zoo_url = 'https://www.openstreetmap.org/way/4251186'  # Horsenden Hill in the fixture
        asked = []

        def known(urls):
            asked.extend(urls)
            return {zoo_url}
        stats, records = cd.discover_council(EALING, cd.VenueIndex([]), None, fetch=lambda code: SAMPLE,
                                             resolve=keep_postcodes, known=known)
        self.assertIn(zoo_url, asked)
        self.assertNotIn(zoo_url, [r['source_url'] for r, _ in records])
        self.assertGreaterEqual(stats['existing'], 1)

    def test_venue_load_pages_in_a_fixed_order(self):
        pages = [[{'id': str(i)} for i in range(1000)], [{'id': 'last'}]]
        db = FakeDB({'venues': lambda q: pages[len([c for c in db.calls if c[0] == 'venues']) - 1]})
        self.assertEqual(len(cd.load_venue_rows(db)), 1001)
        for _, filters, _ in db.calls:
            self.assertIn(('order', ('id',), {}), filters)

    def test_stored_osm_urls_checks_both_url_columns(self):
        url = 'https://www.openstreetmap.org/way/221351281'
        db = FakeDB({'venues': lambda q: [{'source_url': url}] if q.filters[1][1][0] == 'source_url' else []})
        self.assertEqual(cd.stored_osm_urls(db, [url]), {url})
        self.assertEqual([f[1][0] for _, f, _ in db.calls for f in f if f[0] == 'in_'],
                         ['source_url', 'discovered_source_url'])
        self.assertEqual(cd.stored_osm_urls(db, []), set())

    def test_unrelated_neighbour_is_new(self):
        park = self.found['Horsenden Hill']
        index = cd.VenueIndex([{'id': 'v5', 'venue_name': 'Walpole Sandpit Play Area',
                                'latitude': park['lat'], 'longitude': park['lng'] + 0.004}])
        self.assertEqual(cd.match_existing(park, index), (None, None))

    def test_similar_name_inside_a_park_outline_is_skipped(self):
        park = self.found['Horsenden Hill']  # outline about 380 m wide; the existing point is 150 m from its centre
        index = cd.VenueIndex([{'id': 'v6', 'venue_name': 'Horsenden Hill', 'postcode': 'W5 5EN',
                                'latitude': park['lat'], 'longitude': park['lng'] + 0.0022}])
        self.assertEqual(cd.match_existing(park, index)[0], 'existing')

    def test_resolved_postcode_finds_an_existing_venue(self):
        nature = self.found['Gunnersbury Triangle Local Nature Reserve']
        existing = {'id': 'v7', 'venue_name': 'Gunnersbury Triangle Nature Reserve', 'postcode': 'W4 5HA',
                    'latitude': nature['lat'] + 0.004, 'longitude': nature['lng']}  # ~450 m away
        index = cd.VenueIndex([existing])
        self.assertNotEqual(cd.match_existing(nature, index)[0], 'existing')

        def resolve(items, code):
            keep_postcodes(items, code)
            for s in items:
                if s['name'] == nature['name']:
                    s['postcode'], s['postcode_source'] = 'W4 5HA', 'reverse_nearest'
            return items
        stats, records = cd.discover_council(EALING, index, None, fetch=lambda code: SAMPLE, resolve=resolve)
        self.assertNotIn(nature['name'], [r['name'] for r, _ in records])
        self.assertGreaterEqual(stats['existing'], 1)

    def test_within_run_duplicates_are_skipped(self):
        index = cd.VenueIndex([])
        stats, _ = discover(index)
        self.assertGreater(stats['new'], 0)
        again, repeat = discover(index)
        self.assertEqual((again['new'], repeat), (0, []))


class PostcodeTests(unittest.TestCase):
    def test_edge_of_council_spot_is_kept_and_flagged(self):
        found = by_name(spots())
        items = [found['Horsenden Hill'], found['Pitzhanger Manor House and Gallery']]
        forward = {'W55EQ': {'postcode': 'W5 5EQ', 'admin_district': 'Ealing', 'codes': {'admin_district': 'E09000009'}}}
        reverse = [{'postcode': 'TW8 0AA', 'admin_district': 'Hounslow', 'codes': {'admin_district': 'E09000018'}}]
        with patch.object(cd, 'lookup_postcodes', return_value=forward), \
                patch.object(cd, 'reverse_postcodes', return_value=reverse):
            kept = by_name(cd.resolve_postcodes(items, 'E09000009'))
        park, museum = kept['Horsenden Hill'], kept['Pitzhanger Manor House and Gallery']
        self.assertEqual((park['council_check'], park['postcode_source']), ('postcode_other_council', 'reverse_nearest'))
        self.assertEqual((museum['council_check'], museum['postcode_source']), ('postcode_in_council', 'osm_tag'))

    def test_outline_crossing_into_the_council_is_left_to_its_own_council(self):
        def resolve(items, code):
            keep_postcodes(items, code)
            for s in items:
                if s['name'] in ('Horsenden Hill', 'Ash Mini Golf'):
                    s['council_check'] = 'postcode_other_council'
            return items
        stats, records = cd.discover_council(EALING, cd.VenueIndex([]), None, fetch=lambda code: SAMPLE,
                                             resolve=resolve)
        names = [r['name'] for r, _ in records]
        self.assertNotIn('Horsenden Hill', names)  # way: belongs to the neighbouring council's run
        self.assertIn('Ash Mini Golf', names)  # node: genuinely inside, kept and flagged
        self.assertEqual(stats['other_council'], 1)

    def test_inferred_postcode_is_never_stored_on_the_venue(self):
        park = by_name(spots())['Horsenden Hill']
        reverse = [{'postcode': 'W5 5EQ', 'admin_district': 'Ealing', 'codes': {'admin_district': 'E09000009'}}]
        with patch.object(cd, 'reverse_postcodes', return_value=reverse):
            cd.resolve_postcodes([park], 'E09000009')
        park['rank'] = 1
        record = cd.output_record(park, EALING, {}, None)
        row = cd.venue_row(record)
        self.assertEqual(record['postcode'], 'W5 5EQ')
        self.assertIsNone(row['postcode'])
        self.assertNotIn('W5 5EQ', row['address'])
        # A clear-cut type is published; an inferred postcode alone doesn't need review, but any
        # review reason still says the postcode was inferred.
        self.assertTrue(row['public_visible'])
        self.assertIn('nearest postcode W5 5EQ inferred, not stored', cd.review_reason(record))

    def test_lookup_failure_keeps_the_spot_unchecked(self):
        park = by_name(spots())['Horsenden Hill']
        with patch.object(cd, 'lookup_postcodes', return_value={}), \
                patch.object(cd, 'reverse_postcodes', return_value=[None]):
            kept = cd.resolve_postcodes([park], 'E09000009')
        self.assertEqual(kept[0]['council_check'], 'unavailable')

    def test_northern_ireland_skips_postcode_geography(self):
        park = by_name(spots())['Horsenden Hill']
        with patch.object(cd, 'reverse_postcodes') as reverse:
            kept = cd.resolve_postcodes([park], 'N09000003')
        reverse.assert_not_called()
        self.assertEqual(kept[0]['council_check'], 'not_applicable_ni')


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.found = by_name(spots())

    def test_facility_claim_without_a_tag_is_rejected(self):
        note = cd.check_note(self.found['Horsenden Hill'], {
            'description': 'A big green space. Handy baby changing by the gate.', 'peak_busy_times': 'Weekends',
            'evidence_tags': ['opening_hours=07:30-dusk', 'invented=yes']})
        self.assertIsNone(note['description'])
        self.assertEqual(note['note_rejected'], 'unsupported_facility_claim')
        self.assertEqual(note['evidence_tags'], ['opening_hours=07:30-dusk'])

    def test_tag_set_to_no_does_not_support_a_claim(self):
        note = cd.check_note(self.found['Northolt City Farm'], {
            'description': 'Animals to meet. Toilets on site.', 'peak_busy_times': 'Weekends', 'evidence_tags': []})
        self.assertIsNone(note['description'])

    def test_endorsement_and_untagged_age_or_price_claims_are_rejected(self):
        museum = self.found['Pitzhanger Manor House and Gallery']
        for text, reason in [('A safe place to explore. Great gardens.', 'endorsement_claim'),
                             ('Perfect for toddlers. Lovely gardens.', 'unsupported_facility_claim'),
                             ('Free entry all year. Lovely gardens.', 'unsupported_facility_claim')]:
            with self.subTest(text=text):
                note = cd.check_note(museum, {'description': text, 'peak_busy_times': 'Weekends', 'evidence_tags': []})
                self.assertEqual((note['description'], note['note_rejected']), (None, reason))

    def test_supported_facility_claim_is_kept(self):
        note = cd.check_note(self.found['Pitzhanger Manor House and Gallery'], {
            'description': 'A grand house to explore. There are baby changing facilities and toilets.',
            'peak_busy_times': 'Weekend afternoons', 'evidence_tags': ['changing_table=yes']})
        self.assertIsNotNone(note['description'])

    def test_prompt_limits_claims_to_listed_tags(self):
        prompt = cd.notes_prompt('Ealing', [self.found['Horsenden Hill']])
        self.assertIn('ONLY if a matching tag is listed', prompt)
        self.assertIn('way/4251186', prompt)


class DiscoverCouncilTests(TempDirTest):
    def test_llm_failure_keeps_places_with_empty_notes(self):
        stats, records = discover(generator=FakeGenerator(error=ValueError('bad')))
        self.assertEqual(stats['notes_error'], 'ValueError')
        self.assertTrue(records)
        self.assertTrue(all(r['description'] is None for r, _ in records))

    def test_notes_are_attached_and_stay_unverified(self):
        reply = [{'key': 'node/27408513', 'description': 'A grand house. Lovely gardens next door.',
                  'peak_busy_times': 'Weekend afternoons', 'evidence_tags': ['wikidata=Q7199018']}]
        _, records = discover(generator=FakeGenerator(reply))
        record = next(r for r, _ in records if r['osm_id'] == 27408513)
        self.assertEqual(record['description'], 'A grand house. Lovely gardens next door.')
        self.assertTrue(all(r['claims_status'] == 'unverified' for r, _ in records))
        self.assertEqual(list(record), cd.OUTPUT_FIELDS)

    def test_no_boundary_status(self):
        stats, records = discover(fetch=lambda code: NO_AREA)
        self.assertEqual((stats['status'], records), ('no_boundary', []))

    def test_output_is_a_strict_json_array(self):
        _, records = discover()
        path = cd.write_artifact([r for r, _ in records], self.out, 'run')
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        self.assertIsInstance(data, list)
        for item in data:
            cd.validate_record(item)


class DatabaseTests(TempDirTest):
    def test_councils_come_from_the_latest_release(self):
        db = FakeDB({'geography_releases': [{'id': 'release-2'}],
                     'geography_areas': [{'code': 'E09000009', 'name': 'Ealing'}]})
        release, councils = cd.load_councils(db)
        self.assertEqual((release, councils), ('release-2', [EALING]))
        self.assertIn(('order', ('imported_at',), {'desc': True}), db.calls[0][1])
        self.assertIn(('eq', ('release_id', 'release-2'), {}), db.calls[1][1])
        self.assertIn(('eq', ('kind', 'council'), {}), db.calls[1][1])

    def test_due_councils_skip_recent_successes_only(self):
        now = dt.datetime.now(dt.timezone.utc)
        db = FakeDB({'venue_council_discovery_runs': [
            {'council_code': 'A', 'ran_at': now.isoformat(), 'status': 'ok'},
            {'council_code': 'B', 'ran_at': now.isoformat(), 'status': 'failed'},
            {'council_code': 'C', 'ran_at': (now - dt.timedelta(days=400)).isoformat(), 'status': 'ok'},
            {'council_code': 'D', 'ran_at': now.isoformat(), 'status': 'no_boundary'},
            {'council_code': 'F', 'ran_at': (now - dt.timedelta(days=10)).isoformat(), 'status': 'no_boundary'},
            {'council_code': 'N09000003', 'ran_at': (now - dt.timedelta(days=10)).isoformat(),
             'status': 'no_boundary'}]})
        councils = [{'code': c, 'name': c} for c in ['A', 'B', 'C', 'D', 'E', 'F', 'N09000003']]
        # A GB council with a missing boundary is retried after a week; Northern Ireland waits the full refresh.
        self.assertEqual([c['code'] for c in cd.due_councils(db, councils, 10)], ['B', 'C', 'E', 'F'])

    def test_every_type_is_published_and_flagged_places_are_hidden_for_review(self):
        # Owner decisions 23 Oct 2026 (#243): attractions, castles and arts centres go live too.
        _, records = discover()
        farm = next(r for r, _ in records if r['name'] == 'Northolt City Farm')
        farm['possible_duplicate_of'] = {'venue_id': 'v9', 'venue_name': 'Something'}
        db = FakeDB({'venues': lambda q: [{'source_url': row['source_url'], 'id': f'id-{i}'}
                                          for i, row in enumerate(q.payload)]})
        inserted = cd.insert_records(db, records)
        venue_rows = {row['venue_name']: row for row in next(p for table, _, p in db.calls if table == 'venues')}
        self.assertEqual(inserted, len(records))
        for name in ('Pitzhanger Manor House and Gallery', 'Horsenden Hill', 'Ash Mini Golf', 'Hedge Maze',
                     'Ealing Film Studios Tour', 'Example Castle', 'Questors Arts Centre'):
            row = venue_rows[name]
            self.assertEqual((row['public_visible'], row['discovery_status'], row['review_reason']),
                             (True, 'existing', None), name)
        farm_row = venue_rows['Northolt City Farm']
        self.assertEqual((farm_row['public_visible'], farm_row['discovery_status']), (False, 'discovered'))
        self.assertIn('possible duplicate of Something (v9)', farm_row['review_reason'])
        self.assertTrue(all('description' not in row for row in venue_rows.values()))  # AI notes never published
        provenance = next(p for table, _, p in db.calls if table == 'venue_sources')
        self.assertEqual(provenance[0]['source_payload']['draft']['claims_status'], 'unverified')
        self.assertIn('postcode_source', provenance[0]['source_payload'])

    def test_northern_ireland_is_left_out(self):
        belfast = {'code': 'N09000003', 'name': 'Belfast'}
        with patch.object(cd, 'fetch_overpass', return_value=SAMPLE) as fetch, \
                patch.object(cd, 'resolve_postcodes', side_effect=keep_postcodes):
            summary = cd.run(None, dry_run=True, llm=False, venue_rows=[], councils=[belfast, EALING],
                             out_dir=self.out)
            single = cd.run(None, dry_run=True, llm=False, venue_rows=[], councils=[belfast, EALING],
                            council='N09000003', out_dir=self.out)
        self.assertEqual([c['code'] for c in summary['councils']], ['E09000009'])
        self.assertEqual(single['councils'], [])
        self.assertNotIn(('N09000003',), [call.args for call in fetch.call_args_list])

    def test_dry_run_writes_nothing(self):
        db = FakeDB()
        with patch.object(cd, 'fetch_overpass', return_value=SAMPLE), \
                patch.object(cd, 'resolve_postcodes', side_effect=keep_postcodes):
            summary = cd.run(db, dry_run=True, llm=False, venue_rows=[], councils=[EALING], out_dir=self.out)
        self.assertEqual(summary['councils'][0]['status'], 'ok')
        self.assertEqual([c for c in db.calls if c[2] is not None], [])


if __name__ == '__main__':
    unittest.main()
