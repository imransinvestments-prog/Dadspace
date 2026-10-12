"""Published date sections for reviewed council detail pages; no recurrence expansion."""
import datetime as dt
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

HOSTS = {'www.oxfordshire.gov.uk', 'www.coventry.gov.uk'}
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
        if parsed.scheme!='https' or parsed.hostname!=origin.hostname or parsed.username or parsed.password or parsed.port not in (None,443) or not parsed.path.startswith('/events/'):
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
