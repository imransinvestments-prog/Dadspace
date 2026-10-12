"""Published date sections for reviewed council detail pages; no recurrence expansion."""
import datetime as dt
import json
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

HOSTS = {'www.oxfordshire.gov.uk', 'www.coventry.gov.uk', 'haysouthcambs.co.uk', 'haycambridge.co.uk', 'hoop.co.uk', 'www.redbridge.gov.uk'}
RECURRENCE = re.compile(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|weekly|fortnightly|every other|each month|every month)\b', re.I)
CLOCK = re.compile(r'\b(?:\d{1,2}:\d{2}|\d{1,2}(?:\.\d{2})?\s*[ap]m)\b', re.I)
DATE = re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b', re.I)

def date_values(text):
    values=[]
    for match in DATE.finditer(text):
        day,month,year=match.groups()
        fmt='%d %B %Y' if len(month)>3 else '%d %b %Y'
        values.append(dt.datetime.strptime(f'{day} {month} {year}',fmt).date().isoformat())
    return values

def published_date_fields(html,url,title):
    soup=BeautifulSoup(html,'html.parser')
    heading=soup.find('h1')
    normalize=lambda value: re.sub(r'\W+',' ',value.casefold()).strip()
    if not heading or normalize(heading.get_text(' ',strip=True))!=normalize(title):
        raise ValueError('Detail title does not match activity')
    host=urlparse(url).hostname
    if host in {'haysouthcambs.co.uk','haycambridge.co.uk'}:
        candidates=list(dict.fromkeys(p.get_text(' ',strip=True) for p in soup.select('.prose p')
                                     if RECURRENCE.search(p.get_text()) and CLOCK.search(p.get_text())))
        if len(candidates)!=1: raise ValueError('HAY schedule missing or multiple venue/session schedules require review')
        schedule=candidates[0]
        if len(schedule)>300: raise ValueError('HAY schedule exceeds storage limit')
        return dict(start_date=None,end_date=None,occurrence_dates=[],schedule_text=schedule)
    if host=='www.redbridge.gov.uk':
        section=soup.select_one('.location-details-aside-container')
        date=section.select_one('.single-date') if section else None
        if date is None: raise ValueError('Missing Redbridge programme date')
        dates=date_values(date.get_text(' ',strip=True))
        if len(dates)!=1: raise ValueError('Ambiguous Redbridge date')
        time=next((p.get_text(' ',strip=True) for p in section.find_all('p') if CLOCK.search(p.get_text())),None)
        root=soup.find('main') or soup
        schedules=list(dict.fromkeys(p.get_text(' ',strip=True) for p in root.find_all('p') if RECURRENCE.search(p.get_text()) and CLOCK.search(p.get_text())))
        for block in root.select('.govuk-grid-column-two-thirds'):
            for text in block.find_all(string=True,recursive=False):
                schedules.extend(line.strip() for line in str(text).splitlines() if RECURRENCE.search(line) and CLOCK.search(line))
        schedules=list(dict.fromkeys(schedules))
        if len(schedules)>1: raise ValueError('Multiple Redbridge schedules require review')
        schedule=(schedules[0] if schedules else time or '')
        return dict(start_date=dates[0],end_date=dates[0],occurrence_dates=dates,schedule_text=schedule,time_text=time)
    if host=='hoop.co.uk':
        events=[]
        for script in soup.find_all('script',type='application/ld+json'):
            try: value=json.loads(script.get_text())
            except ValueError: continue
            values=value if isinstance(value,list) else value.get('@graph',[value]) if isinstance(value,dict) else []
            events.extend(v for v in values if isinstance(v,dict) and v.get('@type')=='Event' and normalize(v.get('name',''))==normalize(title) and v.get('url')==url)
        if len(events)!=1: raise ValueError('Missing unique matching Hoop event data')
        event=events[0]
        start=dt.datetime.fromisoformat(event['startDate'].replace('Z','+00:00'))
        end=dt.datetime.fromisoformat(event['endDate'].replace('Z','+00:00'))
        if end<=start or end.date()!=start.date(): raise ValueError('Hoop overnight/invalid session requires review')
        for script in soup.find_all('script'): script.decompose()
        visible=soup.get_text(' ',strip=True)
        if not re.search(r'Repeats weekly',visible,re.I): raise ValueError('Hoop regularity needs review')
        times=list(dict.fromkeys(li.get_text(' ',strip=True) for li in soup.find_all('li') if len(CLOCK.findall(li.get_text()))==2))
        if len(times)!=1: raise ValueError('Missing unique visible Hoop session time')
        # Copy the displayed clock; do not silently shift provider UI times
        # using JSON-LD timezone offsets. Date/clock contradictions need review.
        clock=times[0]
        description=soup.find(id='description')
        if description and CLOCK.search(description.get_text()):
            raise ValueError('Hoop description includes additional clock times; session association requires review')
        stamps=[start.strftime('%H:%M'),end.strftime('%H:%M')]
        if CLOCK.findall(clock)!=stamps: raise ValueError('Hoop displayed and structured clocks disagree')
        date=start.date().isoformat()
        return dict(start_date=date,end_date=date,occurrence_dates=[date],schedule_text='Published session: '+date+'; '+clock+'; repeats weekly',time_text=clock)
    if host=='www.oxfordshire.gov.uk':
        section=next((h for h in soup.find_all('h2') if h.get_text(strip=True)=='Dates'),None)
        if section is None: raise ValueError('Missing published Dates section')
        sessions=[];dates=[]
        for p in section.find_next_siblings():
            if p.name.startswith('h'): break
            text=p.get_text(' ',strip=True)
            found=date_values(text)
            if found:
                if len(found)!=1: raise ValueError('Ambiguous session date')
                dates.extend(found);sessions.append(text)
        if not dates: raise ValueError('No explicit session dates')
        return dict(start_date=min(dates),end_date=max(dates),occurrence_dates=sorted(set(dates)),schedule_text='; '.join(sessions))
    if host=='www.coventry.gov.uk':
        section=soup.select_one('.page-meta')
        if section is None: raise ValueError('Missing published event metadata')
        date_row=next((p for p in section.find_all('p') if p.find('strong') and p.find('strong').get_text(strip=True)=='Date:'),None)
        if date_row is None: raise ValueError('Missing published date bounds')
        text=date_row.get_text(' ',strip=True)
        dates=date_values(text)
        if len(dates)!=2 or dates[1]<dates[0]: raise ValueError('Invalid date bounds')
        time_row=next((p for p in section.find_all('p') if p.find('strong') and p.find('strong').get_text(strip=True)=='Time:'),None)
        schedule=text.removeprefix('Date:').strip()
        if time_row: schedule+='; '+time_row.get_text(' ',strip=True)
        # Retain term-time wording as a restriction, without generating sessions.
        editor=soup.select_one('.editor')
        if editor and re.search(r'term time|term-time',editor.get_text(' ',strip=True),re.I): schedule+='; term time only'
        return dict(start_date=dates[0],end_date=dates[1],occurrence_dates=[],schedule_text=schedule)
    raise ValueError('Unreviewed date parser host')

def enrich_dates(raw,source,fetch,robots,stats,limit=4):
    origin=urlparse(source['url'])
    if origin.hostname not in HOSTS: return raw
    output=[];cache={}
    for item in raw:
        if not isinstance(item,dict) or item.get('listing_type')!='activity': output.append(item);continue
        url=urljoin(source['url'],item.get('event_url') or '')
        parsed=urlparse(url)
        path_prefix='/activities/' if origin.hostname in {'haysouthcambs.co.uk','haycambridge.co.uk'} else '/discover/events/' if origin.hostname=='www.redbridge.gov.uk' else '/' if origin.hostname=='hoop.co.uk' else '/events/'
        if parsed.scheme!='https' or parsed.hostname!=origin.hostname or parsed.username or parsed.password or parsed.port not in (None,443) or not parsed.path.startswith(path_prefix):
            output.append(item);continue
        if url not in cache:
            if len(cache)>=limit:
                raise ValueError('Activity date detail budget exceeded; narrower source required')
            allowed,reason=robots(url)
            if not allowed: raise ValueError('Date detail blocked by robots: '+reason)
            cache[url]=fetch(url)
            stats['activity_date_detail_requests']=len(cache)
        fields=published_date_fields(cache[url],url,item['title'])
        output.append(dict(item,**fields))
    return output
