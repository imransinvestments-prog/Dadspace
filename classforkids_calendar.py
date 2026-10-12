"""Opt-in public ClassForKids timetable/details; never enumerate guessed IDs."""
import datetime as dt
import hashlib
import re
from urllib.parse import urlparse,urljoin
from bs4 import BeautifulSoup

def public_url(url,origin):
    value=urlparse(url);host=urlparse(origin).hostname or ''
    if (value.scheme!='https' or value.hostname!=host or not host.endswith('.classforkids.io')
            or value.username or value.password or value.port not in (None,443)):
        raise ValueError('Unreviewed ClassForKids URL')
    return url

def parse_detail(html,url,today):
    soup=BeautifulSoup(html,'html.parser')
    label=next((s for s in soup.select('span.label') if s.get_text(' ',strip=True)=='Class details'),None)
    root=label.parent if label else None
    title=root.find('h4') if root else None
    if title is None: raise ValueError('Missing ClassForKids class detail')
    age=title.find('span')
    if age is None: raise ValueError('Class age needs human review')
    age_text=age.get_text(' ',strip=True).strip('() ')
    minimum=re.search(r'\b(\d+)\s*(yrs?|years?)\b',age_text,re.I)
    if not re.search(r'mth|month',age_text,re.I) and minimum and int(minimum.group(1))>=13:
        raise ValueError('Teen/adult-only class requires separate audience review')
    age.decompose();name=title.get_text(' ',strip=True)
    schedule=root.find('p').get_text(' ',strip=True)
    if not re.search(r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday',schedule):
        raise ValueError('Missing weekday schedule')
    labels=soup.select('p.label-list span.reverse')
    if not labels: raise ValueError('Missing published session dates')
    count=soup.select_one('p.label-list span.info strong')
    if count is None or not count.get_text(strip=True).isdigit() or int(count.get_text(strip=True))!=len(labels):
        raise ValueError('Incomplete published session list')
    dates=[]
    for label in labels:
        date=dt.datetime.strptime(label.get_text(' ',strip=True),'%a %d %b %y').date()
        if date.strftime('%a')!=label.get_text(' ',strip=True).split()[0]:raise ValueError('Published weekday/date conflict')
        if not today.year-1<=date.year<=today.year+2: raise ValueError('Ambiguous short year')
        if date>=today:dates.append(date.isoformat())
    if not dates: raise ValueError('No remaining current sessions')
    dates=sorted(set(dates))
    venue_label=next((s for s in soup.select('span.label') if s.get_text(' ',strip=True)=='Venue details'),None)
    venue=venue_label.parent.find('p') if venue_label else None
    if venue is None or not venue.find('strong'):raise ValueError('Missing venue')
    venue_name=venue.find('strong').get_text(' ',strip=True).rstrip(',')
    postcode=venue.find('small')
    postcode=postcode.find('strong').get_text(strip=True) if postcode and postcode.find('strong') else None
    price_label=next((h for h in soup.find_all('h5') if h.get_text(strip=True)=='Price:'),None)
    price=price_label.find_next('h2').get_text(' ',strip=True) if price_label else None
    if re.search(r'fully booked|sold out|cancelled',root.get_text(' ',strip=True),re.I):raise ValueError('Unavailable class')
    schedule='Published dates: '+', '.join(dates)+'; '+schedule
    if len(schedule)>300:raise ValueError('Schedule exceeds storage limit; narrower session window required')
    return dict(title=name,listing_type='activity',family_relevance=5,family_evidence='Published class age range',audience='families',confidence=.99,
                age_range=age_text,venue_name=venue_name,location=venue_name,postcode=postcode,event_url=url,
                start_date=dates[0],end_date=dates[-1],occurrence_dates=dates,schedule_text=schedule,
                cost_text=(price+' for remaining published sessions') if price else None,description='Regular class with published remaining sessions; check booking page for attendance requirements.')

def collect(source,today,fetch,robots,stats):
    url=public_url(source['url'],source['url']);allowed,reason=robots(url)
    if not allowed:raise ValueError('Robots blocked: '+reason)
    html=fetch(url);stats['requests']=1;documents=[html]
    if re.fullmatch(r'/info/\d+',urlparse(url).path):urls=[url]
    else:
        soup=BeautifulSoup(html,'html.parser')
        urls=list(dict.fromkeys(public_url(urljoin(url,a['href']),url) for a in soup.select('a[data-test="infoAndBooking"][href]')))
        if not urls:raise ValueError('Timetable shell/incomplete rendering; no observed booking links')
        if len(urls)>8:raise ValueError('Detail budget exceeded; narrow venue or class source required')
        if any(not re.fullmatch(r'/info/\d+',urlparse(u).path) for u in urls):raise ValueError('Unreviewed booking link')
    items=[]
    for target in urls:
        if target!=url:
            allowed,reason=robots(target)
            if not allowed:raise ValueError('Robots blocked: '+reason)
            document=fetch(target);documents.append(document);stats['requests']+=1
        else:document=html
        items.append(parse_detail(document,target,today))
    stats.update(gemini_logical_calls=0,extracted=len(items))
    return items,hashlib.sha256('\n'.join(documents).encode()).hexdigest()
