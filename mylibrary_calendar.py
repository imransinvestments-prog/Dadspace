"""Opt-in, bounded MyLibrary collector. No model calls or database access.

Only observed public event/series links are followed. ICS exports are optional:
HTML remains necessary for audience, age, booking and programme regularity.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

HOSTS = {'ealing.events.mylibrary.digital', 'merton.events.mylibrary.digital',
         'events.sutton.gov.uk', 'idea.events.mylibrary.digital'}
FAMILY = re.compile(r'\b(?:babies|baby|toddlers?|children|kids|families|family|nursery rhymes|all ages)\b', re.I)
REGULAR = re.compile(r'\b(?:every (?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|week|month)|weekly|monthly|term[- ]time)\b', re.I)
RARE = re.compile(r'\b(?:festival|annual|one[- ]off|special occasion|celebration)\b',re.I)
REGULAR_PROGRAMME = re.compile(r'\b(?:rhymetimes?|rhyme time|storytimes?|story time|stay\s*(?:and|&)\s*play)\b',re.I)
DATE = re.compile(r'\b(\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4})\b', re.I)
TIME = re.compile(r'\b\d{1,2}:\d{2}\s*[AP]M\b', re.I)
POSTCODE = re.compile(r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b', re.I)
BLOCKED = re.compile(r'verify (?:you are|that you)|checking your browser|access denied|just a moment|captcha|enable javascript and cookies', re.I)


class CalendarError(RuntimeError):
    pass


@dataclass
class Page:
    html: str
    # Index completeness must be established by the renderer, not guessed from
    # navigation/category links elsewhere on the page.
    complete: bool = False


def public_url(url, origin):
    parsed = urlparse(urljoin(origin, url))
    if (parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.port not in (None, 443)
            or parsed.username or parsed.password or parsed.hostname != urlparse(origin).hostname):
        raise CalendarError('Unreviewed calendar host or cross-host hand-off')
    return parsed._replace(fragment='').geturl()


def event_links(root, origin):
    result=[]
    for a in root.select('a[href]'):
        parsed=urlparse(urljoin(origin,a['href']))
        if parsed.path.rstrip('/') != '/event' or not parse_qs(parsed.query).get('id',[''])[0].isdigit():
            continue
        url=public_url(a['href'],origin)
        if url not in result: result.append(url)
    return result


def soup_for(html):
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    if BLOCKED.search(title) or re.search(r'\b(?:404|not found)\b', title, re.I):
        raise CalendarError('Calendar challenge/error shell')
    main=soup.select_one('#main') or soup.find('main')
    if not main: raise CalendarError('Missing calendar main content')
    if BLOCKED.search(main.get_text(' ',strip=True)):
        raise CalendarError('Calendar access challenge')
    return soup,main


def section(main, label):
    heading=next((h for h in main.select('h2,h3') if h.get_text(' ',strip=True)==label),None)
    return heading.find_next_sibling() if heading else None


def html_date(text):
    match=DATE.search(text)
    if not match: raise CalendarError('No explicit occurrence date')
    return dt.datetime.strptime(match[1].title(),'%d %B %Y').date().isoformat()


def parse_detail(html, url):
    _,main=soup_for(html)
    header=main.select_one('.event-page-header')
    if not header or not header.find('h1'): raise CalendarError('Missing event detail header')
    description=section(main,'Event Description')
    when=section(main,'When'); where=section(main,'Where')
    if not when or not where: raise CalendarError('Missing occurrence time or venue')
    where=BeautifulSoup(str(where),'html.parser')
    for a in where.select('.event-map-link'): a.decompose()
    address=where.get_text(', ',strip=True)
    venue=where.find('a')
    if not venue: raise CalendarError('Missing named venue')
    age=cost=None
    for block in header.select('.social-description'):
        values=block.find_all('p')
        if len(values)>=2:
            label=values[-1].get_text(' ',strip=True).lower()
            if label=='ages': age=values[0].get_text(' ',strip=True)
            if label=='cost': cost=values[0].get_text(' ',strip=True)
    text=description.get_text(' ',strip=True) if description else ''
    recurring=next((p.get_text(' ',strip=True) for p in header.select('p.category')
                    if REGULAR.search(p.get_text(' ',strip=True))),None)
    if not recurring:
        match=REGULAR.search(text)
        if match: recurring=match.group(0)
    title=header.h1.get_text(' ',strip=True)
    family=FAMILY.search(title+' '+text)
    # Related events' ages and categories must never leak into this item.
    family_evidence=family.group(0) if family else None
    if not family and age and re.fullmatch(r'\d+\s*[-–]\s*\d+',age):
        if int(re.split('[-–]',age)[0])<13: family_evidence='Detail age restriction: '+age
    times=TIME.findall(when.get_text(' ',strip=True))
    if len(times)!=2: raise CalendarError('Missing/unrecognised explicit start/end clock times')
    start,end=(dt.datetime.strptime(v.upper(),'%I:%M %p') for v in times)
    if end<=start: raise CalendarError('Contradictory or overnight times need review')
    date=html_date(when.get_text(' ',strip=True))
    series=main.select_one('#seriesEventsHeading a[href]')
    ics=when.select_one('a[href*="/ics?"]')
    booking=main.select_one('.button-container')
    booking_text=booking.get_text(' ',strip=True) if booking else None
    notes=section(main,'Notes & Requirements'); bookings=section(main,'Bookings')
    booking_text=' '.join(v.get_text(' ',strip=True) for v in (notes,bookings) if v) or booking_text
    pc=POSTCODE.search(address)
    kind='event' if RARE.search(title+' '+text) else 'activity' if recurring else 'unknown'
    return dict(title=title,description=text,listing_type=kind,
        audience='families' if family_evidence else 'unknown',family_evidence=family_evidence,
        family_relevance=5 if family_evidence else 0,confidence=.99,
        age_range=age,cost_text=cost,venue_name=venue.get_text(' ',strip=True),
        venue_address=address,location=address,postcode=pc.group(0).upper() if pc else None,
        start_date=date,end_date=date,time_text=' - '.join(times),schedule_text=recurring,
        recurrence=recurring,event_url=url,category='story_rhyme' if re.search('rhyme|story',title,re.I) else None,
        booking_text=booking_text,series_url=public_url(series['href'],url) if series else None,
        ics_url=public_url(ics['href'],url) if ics else None,
        occurrence_dates=[date],unavailable=bool(re.search(r'\b(?:fully booked|sold out)\b',booking_text or '',re.I)),cancelled=bool(re.search(r'\bcancelled\b',header.get_text(' ',strip=True),re.I)
            or re.search(r'\b(?:this (?:event|session|activity) (?:has been|is)|event status:) cancelled\b',text,re.I)))


def series_dates(html, origin, item, *, first_date=None, last_date=None, fetch_detail=None):
    _,main=soup_for(html)
    table=main.select_one('table[aria-labelledby="seriesEventsHeading"]')
    # The full-series page uses the same public event table but may omit the ID.
    if table is None:
        tables=[t for t in main.find_all('table') if event_links(t,origin)]
        if len(tables)!=1: raise CalendarError('Unrecognised/incomplete series table')
        table=tables[0]
    if main.select_one('#upcomingEventsLoadMore'):
        raise CalendarError('Incomplete series pagination')
    dates=[]
    for row in table.select('tbody tr') or table.select('tr'):
        cells=row.find_all('td')
        if not cells: continue
        if len(cells)<3 or not event_links(row,origin): raise CalendarError('Malformed series occurrence')
        text=cells[1].get_text(' ',strip=True)
        date=item['start_date'] if not DATE.search(text) and item['event_url'] in event_links(row,origin) else html_date(text)
        if first_date and date<first_date or last_date and date>last_date: continue
        if cells[2].get_text(' ',strip=True).casefold()!=item['venue_name'].casefold():
            raise CalendarError('Series venue conflict')
        title_link=cells[0].find('a')
        if title_link.get_text(' ',strip=True).casefold()!=item['title'].casefold():
            raise CalendarError('Series programme conflict')
        if re.search(r'\bcancelled\b',row.get_text(' ',strip=True),re.I): continue
        if len(cells)>4 and re.search(r'\b(?:full|sold out)\b',cells[4].get_text(' ',strip=True),re.I): continue
        clocks=TIME.findall(cells[1].get_text(' ',strip=True))
        expected=TIME.findall(item['time_text'])[0]
        if clocks and dt.datetime.strptime(clocks[0].upper(),'%I:%M %p')!=dt.datetime.strptime(expected.upper(),'%I:%M %p'):
            raise CalendarError('Series clock-time conflict; fetch individual occurrence details')
        if len(cells)>3 and item['age_range']:
            restriction=cells[3].get_text(' ',strip=True).removeprefix('Ages ').strip()
            if restriction and restriction!=item['age_range']:
                raise CalendarError('Series age restriction conflict')
        if fetch_detail:
            detail_url=event_links(row,origin)[0]
            occurrence=parse_detail(fetch_detail(detail_url).html,detail_url)
            if occurrence['cancelled'] or occurrence['unavailable']: continue
            if occurrence['start_date']!=date: raise CalendarError('Series/detail date conflict')
            for key in ('title','venue_name','time_text','age_range','cost_text'):
                if occurrence[key]!=item[key]: raise CalendarError('Series/detail '+key+' conflict')
        dates.append(date)
    return dates


def parse_ics(text):
    """Single published occurrence only; never expand an unbounded RRULE."""
    text=re.sub(r'\r?\n[ \t]','',text)
    if text.count('BEGIN:VEVENT')!=1 or 'END:VCALENDAR' not in text:
        raise CalendarError('Incomplete or multiple-event ICS export')
    props={}
    inside=False
    for line in text.splitlines():
        if line=='BEGIN:VEVENT': inside=True; continue
        if line=='END:VEVENT': break
        if inside and ':' in line:
            name,value=line.split(':',1); props[name.split(';')[0]]=(name,value)
    if any(k in props for k in ('RRULE','RDATE','EXDATE')):
        raise CalendarError('Recurring ICS requires a full recurrence parser; use published HTML series')
    def stamp(key):
        if key not in props: raise CalendarError('Missing ICS '+key)
        name,value=props[key]
        if 'VALUE=DATE' in name: raise CalendarError('All-day ICS lacks actionable clock time')
        zone=dt.timezone.utc if value.endswith('Z') else ZoneInfo('Europe/London')
        tz=re.search(r'TZID=([^;:]+)',name)
        if tz: zone=ZoneInfo(tz[1])
        value=dt.datetime.strptime(value.rstrip('Z'),'%Y%m%dT%H%M%S').replace(tzinfo=zone)
        return value.astimezone(ZoneInfo('Europe/London'))
    start,end=stamp('DTSTART'),stamp('DTEND')
    if end<=start: raise CalendarError('Contradictory ICS times')
    return dict(date=start.date().isoformat(),end_date=end.date().isoformat(),
                time_text=start.strftime('%I:%M %p').lstrip('0')+' - '+end.strftime('%I:%M %p').lstrip('0'),
                cancelled=props.get('STATUS',('', ''))[1]=='CANCELLED')


def collect(source, today, fetch, robots, *, max_requests=80, max_seconds=300, fetch_ics=None, stats=None):
    """All-or-failure snapshot; partial/empty shells cannot renew freshness."""
    origin=public_url(source['url'],source['url'])
    started=time.monotonic(); cache={}; hashes=[]
    stats=stats if stats is not None else {}
    stats.update(calendar_requests=0,gemini_logical_calls=0)
    def get(url, calendar=False):
        url=public_url(url,origin)
        if url in cache: return cache[url]
        if stats['calendar_requests']>=max_requests or time.monotonic()-started>=max_seconds:
            raise CalendarError('Calendar request/time budget reached; incomplete snapshot')
        allowed,reason=robots(url)
        if not allowed: raise CalendarError('Calendar page blocked by robots: '+reason)
        stats['calendar_requests']+=1
        if calendar and fetch_ics is None: raise CalendarError('ICS fetching was not configured')
        page=(fetch_ics if calendar else fetch)(url)
        if isinstance(page,str): page=Page(page)
        cache[url]=page
        hashes.append((url,page.html))
        return page
    root=get(origin)
    _,main=soup_for(root.html)
    if main.select_one('.event-page-header'):
        links=[origin]
    else:
        index=main.select_one('#upcomingEventsList')
        if index is None: raise CalendarError('Missing rendered upcoming calendar index')
        if not root.complete: raise CalendarError('Index pagination completeness not established')
        links=event_links(index,origin)
        if not links: raise CalendarError('No current calendar supply; retain as unresolved empty source')
    items=[]
    window_days=int(source.get('collection_days',30))
    if not 1<=window_days<=90: raise CalendarError('Collection window must be 1–90 days')
    cutoff=(today+dt.timedelta(days=window_days)).isoformat()
    stats['collection_window_days']=window_days
    for url in links:
        item=parse_detail(get(url).html,url)
        series_checked=False
        if not item['family_evidence']:
            stats['missing_family_evidence']=stats.get('missing_family_evidence',0)+1; continue
        if (item['listing_type']=='unknown' and item['series_url']
                and REGULAR_PROGRAMME.search(item['title'])
                and REGULAR_PROGRAMME.search(item['description'])):
            published=series_dates(get(item['series_url']).html,item['series_url'],item,first_date=today.isoformat(),last_date=cutoff,fetch_detail=get)
            if set(published)-set(item['occurrence_dates']):
                item['listing_type']='activity'
                item['recurrence']='Named regular programme with published series occurrences'
                item['occurrence_dates']+=published
                series_checked=True
        if item['listing_type']=='unknown':
            stats['classification_unresolved']=stats.get('classification_unresolved',0)+1; continue
        if item['cancelled'] or item['unavailable']:
            reason='cancelled' if item['cancelled'] else 'unavailable'
            stats[reason]=stats.get(reason,0)+1; continue
        if fetch_ics and item['ics_url']:
            occurrence=parse_ics(get(item['ics_url'],True).html)
            if occurrence['cancelled']: continue
            if occurrence['date']!=item['start_date'] or occurrence['time_text']!=item['time_text']:
                raise CalendarError('HTML/ICS occurrence conflict')
        if item['listing_type']=='activity' and item['series_url'] and not series_checked:
            item['occurrence_dates']+=series_dates(get(item['series_url']).html,item['series_url'],item,first_date=today.isoformat(),last_date=cutoff,fetch_detail=get)
        item['occurrence_dates']=sorted({d for d in item['occurrence_dates'] if today.isoformat()<=d<=cutoff})
        if not item['occurrence_dates']: continue
        item['description']+=' '+(item['booking_text'] or '')
        if item['listing_type']=='activity':
            item['schedule_text']='Published dates: '+', '.join(item['occurrence_dates'])+'; '+item['time_text']
            # Do not shorten a date list into a continuous weekly promise.
            if len(item['schedule_text'])>300: raise CalendarError('Published schedule exceeds storage limit; review series window')
        items.append(item)
    stats['calendar_documents']=len(cache)
    digest=hashlib.sha256(json.dumps(sorted(hashes),ensure_ascii=False).encode()).hexdigest()
    return items,digest,stats


def render_page(url, *, timeout_ms=30000, settle_ms=2500, max_loads=8):
    """Public UI rendering only; no consent acceptance or challenge bypass."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            page=browser.new_page(user_agent='DadspaceEventsBot/1.0')
            response=page.goto(url,wait_until='domcontentloaded',timeout=timeout_ms)
            if response and response.status>=400: raise CalendarError('http_'+str(response.status))
            if urlparse(page.url).hostname!=urlparse(url).hostname:
                raise CalendarError('Unreviewed calendar redirect')
            page.wait_for_timeout(settle_ms)
            if page.locator('#upcomingEventsList').count():
                # Wait for either a card or the visible empty state, not merely
                # for the initial JS shell to render.
                page.wait_for_function("() => document.querySelector('#upcomingEventsList')?.innerText.trim().length > 0",timeout=timeout_ms)
                button=page.locator('#upcomingEventsLoadMore')
                for _ in range(max_loads):
                    if not button.count() or not button.is_visible(): break
                    count=page.locator('#upcomingEventsList a[href*="event?id="]').count()
                    button.click(timeout=timeout_ms)
                    page.wait_for_function("n => document.querySelectorAll('#upcomingEventsList a[href*=\"event?id=\"]').length > n",arg=count,timeout=timeout_ms)
                if button.count() and button.is_visible(): raise CalendarError('Index pagination budget reached')
                return Page(page.content(),complete=True)
            return Page(page.content())
        finally: browser.close()
