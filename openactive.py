"""Read-only OpenActive survey helpers. No Gemini calls or database writes.

OpenActive publishes CC-BY session feeds (RPDE) for leisure operators and booking
platforms. This module walks the public catalogue and measures pilot supply; it never
stores organiser contact details and never invents ages or locations.
"""
import datetime as dt
import json
import re
import threading
import time
from urllib.parse import urljoin, urlsplit

import requests

from activity_eligibility import PILOT, distance_km, full_postcode, valid_point

CATALOGUE = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'
# ONS-derived open postcode centroids; only public venue postcodes are sent.
POSTCODES_API = 'https://api.postcodes.io/postcodes'
USER_AGENT = 'Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)'
# Opportunity feeds only; FacilityUse and Slot describe bookable space, not sessions.
SERIES_TYPES = {'SessionSeries', 'CourseInstance', 'Course', 'Event', 'HeadlineEvent', 'OnDemandEvent'}
JSON_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)


def kind(value):
    if not isinstance(value, dict):
        return ''
    name = value.get('@type') or value.get('type') or ''
    return name.rsplit('/', 1)[-1].rsplit('#', 1)[-1]


def ident(value):
    if isinstance(value, str):
        return value
    return (value or {}).get('@id') or (value or {}).get('id')


class Client:
    """Sequential polite fetcher; some hosts answer bursts with 403 or 429."""

    def __init__(self, delay=1.0, retries=4, session=None, sleep=time.sleep):
        self.delay, self.retries, self.sleep = delay, retries, sleep
        self.session = session or requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT

    def get(self, url):
        for attempt in range(self.retries + 1):
            # Rate-limit 403s (e.g. Legend) clear after a pause, so retries back off harder.
            self.sleep(self.delay if attempt == 0 else max(self.delay, 2) * 2 ** attempt)
            response = self.session.get(url, timeout=60)
            if response.status_code not in (403, 429, 502, 503, 504) or attempt == self.retries:
                response.raise_for_status()
                return response


def host_group(url):
    """Group subdomains of one provider (e.g. *.legendonlineservices.co.uk) under one pacing queue."""
    labels = urlsplit(url).netloc.lower().split(':')[0].split('.')
    size = 3 if len(labels) > 2 and labels[-2] in ('co', 'org', 'ac', 'gov', 'ltd', 'me') else 2
    return '.'.join(labels[-size:])


class Postcodes:
    """Thread-safe postcode centroid cache, filled in bulk batches of 100."""

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.points, self.lock = {}, threading.Lock()

    def resolve(self, postcodes):
        with self.lock:
            missing = sorted({p for p in postcodes if p and p not in self.points})
        for start in range(0, len(missing), 100):
            batch = missing[start:start + 100]
            try:
                response = self.session.post(POSTCODES_API, json={'postcodes': batch}, timeout=60)
                response.raise_for_status()
                results = response.json().get('result') or []
            except Exception:
                continue
            found = {}
            for row in results:
                result = row.get('result') or {}
                point = (result.get('latitude'), result.get('longitude'))
                found[re.sub(r'\s', '', (row.get('query') or '').upper())] = point if None not in point else None
            with self.lock:
                self.points.update({p: found.get(p) for p in batch})
        with self.lock:
            return {p: self.points.get(p) for p in postcodes if p}


def dataset_urls(catalogue_collection, client):
    urls = []
    for catalogue_url in catalogue_collection.get('hasPart', []):
        try:
            catalogue = client.get(catalogue_url).json()
        except Exception as exc:
            urls.append({'catalogue': catalogue_url, 'error': str(exc)[:300]})
            continue
        urls.extend({'catalogue': catalogue_url, 'url': url} for url in catalogue.get('dataset', []))
    return urls


def dataset_description(html):
    for block in JSON_LD.findall(html or ''):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if kind(data) == 'Dataset':
            publisher = data.get('publisher') or {}
            feeds = [{'type': (d.get('additionalType') or '').rsplit('/', 1)[-1] or None,
                      'url': d.get('contentUrl')} for d in data.get('distribution', []) if d.get('contentUrl')]
            return {'name': data.get('name'), 'publisher': publisher.get('name'),
                    'license': data.get('license'), 'feeds': feeds}
    return None


def feeds_to_walk(feeds):
    # A SessionSeries feed already names every series; walk sessions only without one.
    series = [f for f in feeds if f['type'] in SERIES_TYPES or f['type'] is None]
    sessions = [f for f in feeds if f['type'] == 'ScheduledSession']
    return series + ([] if any(f['type'] == 'SessionSeries' for f in series) else sessions)


class SeriesIndex:
    """Live RPDE state with one row per series: item ids only hold a series key.

    Better's legacy feed holds ~140k dated items for a few thousand series, so keeping
    full JSON-LD per item exhausted memory. Counts keep RPDE deletes exact.
    """

    def __init__(self):
        self.keys, self.rows = {}, {}

    def update(self, item_id, row):
        self.delete(item_id)
        key = row['series_id'] or ('item', item_id)
        self.keys[item_id] = key
        count = self.rows.get(key, (None, 0))[1]
        self.rows[key] = (row, count + 1)

    def delete(self, item_id):
        key = self.keys.pop(item_id, None)
        if key is None:
            return
        row, count = self.rows[key]
        if count > 1:
            self.rows[key] = (row, count - 1)
        else:
            del self.rows[key]

    def series(self):
        return {key: row for key, (row, _) in self.rows.items()}


def walk_feed(url, client, max_pages=2000, deadline=None, transform=None):
    """Return the live RPDE items; later pages supersede earlier ones.

    Without `transform`, items are full data keyed by item id. With it, each item is
    reduced on arrival and the result is one compact row per series key.
    """
    live = SeriesIndex() if transform else {}
    pages, complete, error = 0, False, None
    while pages < max_pages and (deadline is None or time.monotonic() < deadline):
        try:
            page = client.get(url).json()
        except Exception as exc:
            error = str(exc)[:300]
            break
        pages += 1
        for item in page.get('items', []):
            item_id = item.get('id')
            if item.get('state') == 'updated' and item.get('data'):
                if transform:
                    live.update(item_id, transform(item['data']))
                else:
                    live[item_id] = item['data']
            elif transform:
                live.delete(item_id)
            else:
                live.pop(item_id, None)
        following = urljoin(url, page['next']) if page.get('next') else None
        if not page.get('items') or not following or following == url:
            complete = True
            break
        url = following
    return {'pages': pages, 'complete': complete, 'error': error,
            'items': live.series() if transform else live}


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def age_evidence(age_range):
    if not isinstance(age_range, dict):
        return {'state': 'unknown', 'reason': 'missing ageRange'}
    lower, upper = _number(age_range.get('minValue')), _number(age_range.get('maxValue'))
    if lower is None and upper is None:
        return {'state': 'unknown', 'reason': 'empty ageRange'}
    if lower is not None and upper is not None and upper < lower:
        return {'state': 'unknown', 'reason': 'contradictory ageRange'}
    # An absent minValue is an open lower bound in the OpenActive model.
    lower = lower or 0
    evidence = {'minimum_years': lower, 'maximum_years': upper}
    if lower >= 6:
        return dict(evidence, state='outside')
    # Operators default adult classes to "0–110"; an open or adult upper bound is
    # no evidence of early-years suitability, so it stays a separate review state.
    if upper is None or upper >= 18:
        return dict(evidence, state='unbounded', reason='all-ages or adult-inclusive range')
    return dict(evidence, state='eligible')


def place_postcode(place):
    if not isinstance(place, dict):
        return None
    address = place.get('address')
    return full_postcode(address.get('postalCode') if isinstance(address, dict) else address)


def location_evidence(place, postcodes=None):
    if not isinstance(place, dict):
        return {'state': 'unknown', 'reason': 'missing location'}
    geo = place.get('geo') or {}
    lat, lng = _number(geo.get('latitude')), _number(geo.get('longitude'))
    postcode, method = place_postcode(place), 'feed_coordinates'
    if (lat is None or lng is None or (lat, lng) == (0, 0)) and (postcodes or {}).get(postcode):
        (lat, lng), method = postcodes[postcode], 'postcode_centroid'
    if lat is not None and lng is not None and valid_point(lat, lng) and (lat, lng) != (0, 0):
        km = distance_km((lat, lng))
        return {'state': 'local' if km <= 10 else 'outside', 'distance_km': round(km, 2),
                'postcode': postcode, 'method': method}
    return {'state': 'unknown', 'reason': 'missing coordinates', 'postcode': postcode}


def opportunity(data, postcodes=None):
    """Flatten one feed item, inheriting series fields that sessions often omit."""
    parent = data.get('superEvent') if isinstance(data.get('superEvent'), dict) else {}
    pick = lambda key: data.get(key) or parent.get(key)
    organizer = pick('organizer') or {}
    activities = [a.get('prefLabel') for a in (pick('activity') or []) if isinstance(a, dict) and a.get('prefLabel')]
    place = pick('location')
    session = kind(data) == 'ScheduledSession'
    series_id = ident(data.get('superEvent')) if session else ident(data)
    if not series_id and pick('name'):
        # Legacy feeds (Better) emit each dated Event without an id; name + place is the series.
        series_id = ('untitled-series', pick('name'), place.get('name') if isinstance(place, dict) else None)
    return {
        'series_id': series_id,
        'type': kind(data),
        'name': pick('name'),
        'url': pick('url'),
        'activities': activities,
        # Organisation names are public trading names; Person organisers are never copied.
        'organizer': organizer.get('name') if kind(organizer) == 'Organization' else None,
        'place': place.get('name') if isinstance(place, dict) else None,
        'has_schedule': bool(pick('eventSchedule')) or session,
        'age': age_evidence(pick('ageRange')),
        'location': location_evidence(place, postcodes),
    }


def relocate(row, postcodes):
    """Place a row that had no feed coordinates, using a resolved postcode centroid."""
    postcode = row['location'].get('postcode')
    if row['location']['state'] != 'unknown' or not (postcodes or {}).get(postcode):
        return row
    return dict(row, location=location_evidence({'address': {'postalCode': postcode}}, postcodes))


def summarise(opportunities, sample_size=10, postcodes=None):
    """Summarise compact rows from `opportunity`, counting each series once."""
    rows, seen = [], set()
    for index, row in enumerate(opportunities):
        key = row['series_id'] or ('item', index)
        if key in seen:
            continue
        seen.add(key)
        rows.append(relocate(row, postcodes))
    local = [r for r in rows if r['location']['state'] == 'local']
    pilot = [r for r in local if r['age']['state'] == 'eligible']
    labels = {}
    for row in pilot:
        for label in row['activities'] or ['(no activity label)']:
            labels[label] = labels.get(label, 0) + 1
    count = lambda rs, key, state: sum(r[key]['state'] == state for r in rs)
    return {
        'series': len(rows),
        'age_eligible': count(rows, 'age', 'eligible'),
        'age_unknown': count(rows, 'age', 'unknown'),
        'location_unknown': count(rows, 'location', 'unknown'),
        'local': len(local),
        'local_via_postcode': sum(r['location'].get('method') == 'postcode_centroid' for r in local),
        'local_age_unknown': count(local, 'age', 'unknown'),
        'local_age_unbounded': count(local, 'age', 'unbounded'),
        'pilot_eligible': len(pilot),
        'pilot_eligible_with_schedule': sum(r['has_schedule'] for r in pilot),
        'pilot_activity_labels': dict(sorted(labels.items(), key=lambda kv: -kv[1])[:15]),
        'pilot_sample': sorted(pilot, key=lambda r: r['location']['distance_km'])[:sample_size],
    }


def survey_dataset(entry, client, max_pages=2000, seconds=900, postcodes=None):
    result = dict(entry, checked_at=dt.datetime.now(dt.timezone.utc).isoformat())
    if entry.get('error'):
        return result
    try:
        description = dataset_description(client.get(entry['url']).text)
    except Exception as exc:
        return dict(result, error=str(exc)[:300])
    if not description:
        return dict(result, error='no Dataset JSON-LD')
    result.update(description)
    deadline = time.monotonic() + seconds
    walked, rows = [], []
    for feed in feeds_to_walk(description['feeds']):
        outcome = walk_feed(feed['url'], client, max_pages, deadline, transform=opportunity)
        rows.extend(outcome.pop('items').values())
        walked.append(dict(feed, **outcome))
    result['walked'] = walked
    points = None
    if postcodes:
        points = postcodes.resolve({r['location'].get('postcode') for r in rows
                                    if r['location']['state'] == 'unknown'} - {None})
    result['summary'] = summarise(rows, postcodes=points)
    return result


def totals(datasets):
    keys = ('series', 'age_eligible', 'local', 'local_via_postcode', 'local_age_unknown',
            'local_age_unbounded', 'pilot_eligible', 'pilot_eligible_with_schedule')
    surveyed = [d for d in datasets if d.get('summary')]
    return {
        'datasets': len(datasets),
        'datasets_surveyed': len(surveyed),
        'datasets_failed': sum(bool(d.get('error')) for d in datasets),
        'datasets_incomplete': sum(any(not w['complete'] for w in d.get('walked', [])) for d in surveyed),
        'datasets_with_pilot_supply': sum(d['summary']['pilot_eligible'] > 0 for d in surveyed),
        'licenses': sorted({d.get('license') or 'unknown' for d in surveyed}),
        **{key: sum(d['summary'][key] for d in surveyed) for key in keys},
        'pilot': {'postcode': 'W3 9LN', 'latitude': PILOT[0], 'longitude': PILOT[1], 'radius_km': 10,
                  'ages': '0–5 inclusive; ageRange overlap before sixth birthday'},
    }
