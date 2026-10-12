"""Strict opt-in JSON-LD extraction. Ambiguous pages fall back as a whole."""
import datetime as dt
import re
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup


FAMILY = re.compile(r'\b(?:famil(?:y|ies)|children|kids|toddlers|babies|parent.and.child)\b', re.I)


def complete_events(documents, extract_jsonld):
    """Return raw records only if every event is complete and visibly grounded.

    Sources must explicitly opt in; do not infer completeness from the presence
    of JSON-LD. Unknown recurrence, prices, audience, missing visible titles,
    timezone-less times and ambiguous metadata all fall back to the LLM.
    """
    rows = []
    seen = set()
    for url, html in documents:
        soup = BeautifulSoup(html, 'html.parser')
        events = extract_jsonld(soup)
        for node in soup(['script', 'style', 'nav', 'footer', 'header']):
            node.decompose()
        visible = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))
        if not events:
            return None
        for event in events:
            try:
                title = event['name']
                description = event['description']
                if not isinstance(title, str) or not isinstance(description, str):
                    return None
                if title not in visible or description not in visible or not FAMILY.search(title + ' ' + description):
                    return None
                if event.get('eventSchedule') or event.get('eventStatus') not in (None, 'https://schema.org/EventScheduled'):
                    return None
                start = dt.datetime.fromisoformat(event['startDate'].replace('Z', '+00:00'))
                end = dt.datetime.fromisoformat(event['endDate'].replace('Z', '+00:00'))
                if start.tzinfo is None or end.tzinfo is None or end < start:
                    return None
                # Preserve actual local advertised times; do not guess the zone.
                if start.utcoffset() != end.utcoffset():
                    return None
                start = start.astimezone(ZoneInfo('Europe/London'))
                end = end.astimezone(ZoneInfo('Europe/London'))
                location = event['location']
                address = location['address']
                venue = location['name']
                street = address['streetAddress']
                postcode = address['postalCode']
                if not all(isinstance(x, str) and x.strip() for x in (venue, street, postcode)):
                    return None
                offer = event['offers']
                if not isinstance(offer, dict) or offer.get('priceCurrency') != 'GBP':
                    return None
                price = str(offer['price'])
                if not re.fullmatch(r'\d+(?:\.\d{1,2})?', price):
                    return None
                event_url = urljoin(url, event['url'])
                if urlparse(event_url).scheme not in ('http', 'https'):
                    return None
                if event_url not in [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]:
                    return None
                evidence = FAMILY.search(title + ' ' + description).group()
                row = dict(title=title, description=description, start_date=start.date().isoformat(),
                           end_date=end.date().isoformat(), time_text=f'{start:%H:%M} - {end:%H:%M}',
                           location=venue, venue_name=venue, venue_address=street, postcode=postcode,
                           event_url=event_url, cost_text='Free' if float(price) == 0 else '£' + price,
                           recurrence='one_off', listing_type='event', is_holiday_camp=False,
                           category='other', schedule_text=None, age_range=None,
                           family_relevance=5, confidence=1.0, audience='families', family_evidence=evidence)
                key = (event_url, start.isoformat())
                if key not in seen:
                    rows.append(row)
                    seen.add(key)
            except (KeyError, TypeError, ValueError, AttributeError):
                return None
    return rows or None
