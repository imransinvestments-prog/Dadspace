"""OpenActive session-series adapter: CC-BY feeds to Activities, zero model calls.

A source row's url is a publisher's OpenActive dataset page. Only series with an
evidenced weekly schedule and an ageRange overlapping 0–5 become Activities. Open or
adult-inclusive ranges, schedules without weekdays and ended series are counted, never
guessed. Series sharing a name and centre are one Activity with their slots combined.
"""
import datetime as dt
import hashlib
import json
import re
import time

import openactive

LICENCES = {'https://creativecommons.org/licenses/by/4.0/', 'http://creativecommons.org/licenses/by/4.0/'}
# Bookable opportunities only; FacilityUse/Slot are space hire and ScheduledSession
# occurrences are not needed where the series publishes its own schedule.
FEED_TYPES = ('SessionSeries', 'CourseInstance')
DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
WEEKLY = (None, 'P1W', 'P7D')
CANCELLED = ('EventCancelled', 'EventPostponed')
SCHEDULE_LIMIT = 300
# A party or hire booking is a private occasion, not an opportunity families can join.
PRIVATE_HIRE = re.compile(r'\b(?:part(?:y|ies)|private hire|hire|exclusive use)\b', re.I)
# Some operators name each slot ('Soft Play Mon 12:00'); the schedule already says when.
SLOT_SUFFIX = re.compile(r'\s*[-–,]?\s*\b(?:mon|tues?|wed|thu(?:rs?)?|fri|sat|sun)(?:day)?s?\b'
                         r'(?:\s+\d{1,2}(?:[:.]?\d{2})?(?:\s*[ap]m)?(?:\s*-\s*\d{1,2}(?:[:.]\d{2})?)?)?\s*$', re.I)
NAMED_AGES = re.compile(r'\b(\d{1,2})\s*[-–]\s*\d{1,2}\s*(?:yrs?|years?)?(?:\b|$)', re.I)
EARLY_YEARS = re.compile(r'\b(?:soft play|play|bounce|tots?|toddlers?|bab(?:y|ies)|pre-?school|under ?5s?)\b', re.I)
DESCRIPTION_LIMIT = 1000


def _date(value):
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _weekday(value):
    name = str(value).rsplit('/', 1)[-1].rsplit('#', 1)[-1]
    return name if name in DAYS else None


def schedule_slots(schedules, today):
    """Return (weekly slots, end date) or a skip reason. Never invents a weekday."""
    slots, ends = set(), []
    for schedule in schedules or []:
        if not isinstance(schedule, dict) or schedule.get('repeatFrequency') not in WEEKLY:
            return 'schedule_not_weekly'
        days = [_weekday(day) for day in schedule.get('byDay') or []]
        if not days or None in days or not schedule.get('startTime'):
            return 'schedule_without_weekday'
        end = _date(schedule['endDate']) if schedule.get('endDate') else None
        if schedule.get('endDate') and not end:
            return 'schedule_invalid_date'
        if end and end < today:
            continue
        ends.append(end)
        slots.update((day, schedule['startTime'], schedule.get('endTime')) for day in days)
    if not slots:
        return 'schedule_missing' if not schedules else 'schedule_ended'
    # One open-ended part keeps the whole series open-ended.
    return slots, None if None in ends else max(ends)


def _day_list(days):
    """'Mon–Fri, Sun': runs of three or more consecutive days become a range."""
    runs = []
    for day in sorted(days):
        if runs and day == runs[-1][-1] + 1:
            runs[-1].append(day)
        else:
            runs.append([day])
    name = lambda day: DAYS[day][:3]
    return ', '.join(name(r[0]) + '–' + name(r[-1]) if len(r) > 2 else ', '.join(map(name, r)) for r in runs)


def schedule_text(slots):
    """'Weekly: Mon–Fri 09:00–12:00, 15:00–18:00; Sat 09:00–09:30', days sharing a timetable merged."""
    times = {}
    for day, start, end in slots:
        times.setdefault(DAYS.index(day), set()).add(start + ('–' + end if end else ''))
    groups = {}
    for day, day_times in times.items():
        groups.setdefault(tuple(sorted(day_times)), set()).add(day)
    parts = sorted((min(days), days, day_times) for day_times, days in groups.items())
    return 'Weekly: ' + '; '.join(_day_list(days) + ' ' + ', '.join(day_times) for _, days, day_times in parts)


def _price_text(prices):
    if not prices:
        return None
    low, high = min(prices), max(prices)
    if high == 0:
        return 'Free'
    money = lambda value: '£%.2f' % value
    return money(low) + ('' if low == high else '–' + money(high)) + ' per session; check booking page'


def series_name(value):
    name = ' '.join(str(value).split())
    return SLOT_SUFFIX.sub('', name).strip() or name


def series_row(data, today):
    """Compact one feed item to the fields an Activity needs, or a counted skip."""
    parent = data.get('superEvent') if isinstance(data.get('superEvent'), dict) else {}
    pick = lambda key: data.get(key) or parent.get(key)
    row = {'series_id': openactive.ident(data)}
    if str(pick('eventStatus') or '').rsplit('/', 1)[-1] in CANCELLED:
        return dict(row, skip='cancelled')
    age = openactive.age_evidence(pick('ageRange'))
    if age['state'] != 'eligible':
        return dict(row, skip='age_' + age['state'])
    slots = schedule_slots(pick('eventSchedule'), today)
    if isinstance(slots, str):
        return dict(row, skip=slots)
    place = pick('location') if isinstance(pick('location'), dict) else {}
    address = place.get('address') if isinstance(place.get('address'), dict) else {}
    url = pick('url')
    if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
        return dict(row, skip='missing_url')
    if not place.get('name') or not pick('name'):
        return dict(row, skip='missing_name_or_place')
    if PRIVATE_HIRE.search(str(pick('name'))):
        return dict(row, skip='private_hire')
    # Operators often publish a broad ageRange ('5–15') for a class named '11-15'.
    named = NAMED_AGES.search(series_name(pick('name')))
    if named and int(named[1]) >= 6:
        return dict(row, skip='age_name_outside')
    prices = []
    for offer in pick('offers') or []:
        if not isinstance(offer, dict):
            continue
        label = ' '.join(str(offer.get(k) or '') for k in ('identifier', 'name')).lower()
        # Staff and corporate rates are not prices a visiting parent can pay.
        if 'staff' in label or 'corporate' in label:
            continue
        try:
            prices.append(float(offer['price']))
        except (KeyError, TypeError, ValueError):
            pass
    labels = [a.get('prefLabel') for a in pick('activity') or [] if isinstance(a, dict) and a.get('prefLabel')]
    return dict(
        row, name=series_name(pick('name')), url=url, place=' '.join(place['name'].split()),
        postcode=address.get('postalCode'),
        address=', '.join(str(address[k]).strip() for k in ('streetAddress', 'addressLocality') if address.get(k)) or None,
        minimum=age['minimum_years'], maximum=age['maximum_years'],
        slots=sorted(slots[0]), end=slots[1].isoformat() if slots[1] else None,
        prices=prices, labels=labels,
        description=' '.join(str(pick('description') or '').split()) or None)


def activity_items(rows, publisher):
    """Group compact series rows by name and centre into worker activity items."""
    groups = {}
    for row in rows:
        groups.setdefault((row['name'].lower(), row['place'].lower(), row['postcode']), []).append(row)
    items, too_long = [], 0
    attribution = f'Session data: {publisher or "the operator"} via OpenActive, CC BY 4.0.'
    years = lambda value: '%g' % value
    for group in groups.values():
        first = min(group, key=lambda r: str(r['series_id']))
        text = schedule_text({tuple(slot) for row in group for slot in row['slots']})
        if len(text) > SCHEDULE_LIMIT:
            # The worker truncates long text; a cut schedule would hide real slots.
            too_long += 1
            continue
        low, high = min(r['minimum'] for r in group), max(r['maximum'] for r in group)
        ends = [r['end'] for r in group]
        labels = [label.lower() for row in group for label in row['labels']] + [first['name'].lower()]
        description = (first['description'] or '')[:DESCRIPTION_LIMIT - len(attribution) - 1].strip()
        items.append(dict(
            title=first['name'], listing_type='activity', family_relevance=5, audience='children',
            family_evidence=f'OpenActive ageRange {years(low)}–{years(high)} years', confidence=.99,
            age_range=f'{years(low)}–{years(high)} years' if low else f'Up to {years(high)} years',
            category=('swimming' if any('swim' in label for label in labels)
                      else 'baby_toddler' if any(EARLY_YEARS.search(label) for label in labels) else 'sports'),
            venue_name=first['place'], location=first['place'], venue_address=first['address'],
            postcode=first['postcode'], event_url=first['url'], schedule_text=text,
            end_date=None if None in ends else max(ends),
            cost_text=_price_text([p for row in group for p in row['prices']]),
            description=(description + ' ' + attribution).strip()))
    return items, too_long


def collect(source, today, robots, stats, client=None, max_pages=2000, seconds=1200):
    client = client or openactive.Client()
    allowed, reason = robots(source['url'])
    if not allowed:
        raise ValueError('Robots blocked: ' + reason)
    description = openactive.dataset_description(client.get(source['url']).text)
    stats['requests'] = 1
    if not description:
        raise ValueError('No OpenActive Dataset JSON-LD')
    if description.get('license') not in LICENCES:
        raise ValueError('Unreviewed OpenActive licence: ' + str(description.get('license')))
    feeds = [f for f in description['feeds'] if f['type'] in FEED_TYPES]
    if not feeds:
        raise ValueError('No SessionSeries or CourseInstance feed')
    deadline = time.monotonic() + seconds
    rows = []
    for feed in feeds:
        allowed, reason = robots(feed['url'])
        if not allowed:
            raise ValueError('Robots blocked: ' + reason)
        outcome = openactive.walk_feed(feed['url'], client, max_pages, deadline,
                                       transform=lambda data: series_row(data, today))
        stats['requests'] += outcome['pages']
        if not outcome['complete']:
            # A partial walk cannot tell an ended series from an unread page.
            raise ValueError(f"Incomplete OpenActive {feed['type']} feed after {outcome['pages']} pages: "
                             f"{outcome['error'] or 'page or time budget'}")
        rows.extend(outcome['items'].values())
    for row in rows:
        if row.get('skip'):
            stats['openactive_' + row['skip']] = stats.get('openactive_' + row['skip'], 0) + 1
    kept = [row for row in rows if not row.get('skip')]
    items, too_long = activity_items(kept, description.get('publisher'))
    if too_long:
        stats['activity_schedule_requires_review'] = stats.get('activity_schedule_requires_review', 0) + too_long
    stats.update(gemini_logical_calls=0, openactive_series=len(rows), openactive_series_eligible=len(kept),
                 extracted=len(items))
    digest = hashlib.sha256(json.dumps(sorted(items, key=lambda i: (i['title'], i['venue_name'])),
                                       sort_keys=True).encode()).hexdigest()
    return items, digest
