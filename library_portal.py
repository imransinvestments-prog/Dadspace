"""Read public library portal records from published React server components.

No JavaScript execution, private endpoints, calendar-host requests or model calls.
The returned index must extend beyond the declared collection window.
"""
import datetime as dt
import hashlib
import json
import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from mylibrary_calendar import CalendarError, FAMILY, REGULAR, REGULAR_PROGRAMME, RARE

PORTALS={'libraries.ealing.gov.uk':'ealing.events.mylibrary.digital',
         'libraries.merton.gov.uk':'merton.events.mylibrary.digital'}

def published_records(html):
    soup=BeautifulSoup(html,'html.parser')
    stream=''
    for script in soup.find_all('script'):
        text=script.get_text().strip()
        prefix='self.__next_f.push('
        if not text.startswith(prefix): continue
        try: args=json.loads(text[len(prefix):].rstrip(';')[:-1])
        except json.JSONDecodeError: raise CalendarError('Malformed public portal data')
        if len(args)>1 and isinstance(args[1],str): stream+=args[1]
    # RSC text frames are length-prefixed UTF-8; the next frame does not need
    # a newline. Respect those boundaries rather than matching JSON in prose.
    data=stream.encode('utf-8'); cursor=0; frames=[]; texts={}
    while cursor<len(data):
        match=re.match(rb'[0-9a-f]+:',data[cursor:])
        if not match:
            newline=data.find(b'\n',cursor)
            if newline<0: break
            cursor=newline+1; continue
        cursor+=match.end()
        text_frame=re.match(rb'T([0-9a-f]+),',data[cursor:])
        if text_frame:
            cursor+=text_frame.end(); length=int(text_frame[1],16)
            if cursor+length>len(data): raise CalendarError('Incomplete public portal text frame')
            texts[match[0][:-1].decode()]=data[cursor:cursor+length].decode('utf-8')
            cursor+=length; continue
        newline=data.find(b'\n',cursor)
        end=len(data) if newline<0 else newline
        record=data[cursor:end];cursor=end+1
        if record[:1] in (b'[',b'{'):
            try: frames.append(json.loads(record))
            except (json.JSONDecodeError,UnicodeDecodeError): raise CalendarError('Malformed public portal frame')
    candidates=[]
    def walk(obj):
        if isinstance(obj,dict):
            if obj.get('isEvents') is True and isinstance(obj.get('source'),list): candidates.append(obj['source'])
            for value in obj.values(): walk(value)
        elif isinstance(obj,list):
            for value in obj: walk(value)
    for frame in frames: walk(frame)
    if len(candidates)!=1 or not candidates[0]: raise CalendarError('Missing/ambiguous complete public event index')
    for record in candidates[0]:
        for key in ('description','description_html','requirements'):
            value=record.get(key)
            if isinstance(value,str) and re.fullmatch(r'\$[0-9a-f]+',value) and value[1:] in texts:
                record[key]=texts[value[1:]]
    return candidates[0]

def collect_portal(source,today,fetch,robots,stats):
    url=source['url'];parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname not in PORTALS or parsed.path!='/events' or parsed.query or parsed.username or parsed.password or parsed.port not in (None,443):
        raise CalendarError('Unreviewed public library portal URL')
    allowed,reason=robots(url)
    if not allowed: raise CalendarError('Portal blocked by robots: '+reason)
    stats.update(calendar_requests=1,gemini_logical_calls=0)
    html=fetch(url)
    if len(html.encode('utf-8'))>8_000_000: raise CalendarError('Portal document budget exceeded')
    records=published_records(html)
    zone=ZoneInfo('Europe/London')
    def stamp(value):
        if type(value) not in (int,float): raise CalendarError('Missing public occurrence timestamp')
        return dt.datetime.fromtimestamp(value,dt.timezone.utc).astimezone(zone)
    starts=[stamp(r.get('start_time')) for r in records]
    if starts!=sorted(starts): raise CalendarError('Portal index order is unqualified')
    days=int(source.get('collection_days',30))
    if not 1<=days<=90: raise CalendarError('Collection window must be 1–90 days')
    cutoff=today+dt.timedelta(days=days)
    # Require a later published record as a completeness witness: an array cap
    # cannot silently omit more events within our selected window.
    if starts[-1].date()<=cutoff: raise CalendarError('Portal index does not cover full collection window')
    stats.update(collection_window_days=days,portal_records=len(records))
    groups={}
    from provider_session_identity import ADAPTER, scope, metadata
    provider_mode=source.get('source_adapter')==ADAPTER
    namespace,selected_sessions=scope(url) if provider_mode else (None,None)
    provider_occurrence_ids=set()
    def reject(reason): stats[reason]=stats.get(reason,0)+1
    for record,start in zip(records,starts):
        if provider_mode and record.get('series_id') not in selected_sessions:
            reject('outside_reviewed_session_scope'); continue
        if provider_mode:
            occurrence_id=record.get('event_id')
            if type(occurrence_id) is not int or occurrence_id<=0 or occurrence_id in provider_occurrence_ids:
                raise CalendarError('Duplicate or contradictory provider occurrence identity')
            provider_occurrence_ids.add(occurrence_id)
        if not today<=start.date()<=cutoff: reject('outside_window'); continue
        if record.get('is_private') is not False or record.get('is_published') is not True: reject('not_public');continue
        if record.get('is_cancelled') or record.get('is_fully_booked'): reject('cancelled_or_full');continue
        if record.get('is_virtual'): reject('virtual_requires_review');continue
        end=stamp(record.get('end_time'))
        if end<=start or end.date()!=start.date(): reject('invalid_or_multiday_clock_requires_review');continue
        title=record.get('name','');description=BeautifulSoup(record.get('description_html') or record.get('description',''),'html.parser').get_text(' ',strip=True)
        if description.startswith('$'): reject('unresolved_description_reference');continue
        if not FAMILY.search(title+' '+description): reject('missing_family_evidence');continue
        recurrence=record.get('recurring_dates_tagline') or ''
        text=title+' '+description
        kind='event' if RARE.search(text) else 'activity' if REGULAR.search(recurrence+' '+description) else 'unknown'
        if kind=='unknown' and (record.get('series_id') or record.get('series_name')) and REGULAR_PROGRAMME.search(title) and REGULAR_PROGRAMME.search(description): kind='activity'
        if kind=='unknown': reject('classification_unresolved');continue
        target=record.get('url','');link=urlparse(target)
        if link.scheme!='https' or link.hostname!=PORTALS[parsed.hostname] or link.path!='/event' or link.username or link.password:
            raise CalendarError('Unreviewed portal booking hand-off')
        venue=record.get('location_name')
        if not venue: reject('missing_activity_location');continue
        minimum,maximum=record.get('age_min'),record.get('age_max')
        # False is the provider's missing minimum; never turn it into a
        # fabricated zero. An explicit maximum remains useful evidence.
        age=f'{minimum}-{maximum}' if type(minimum) in (int,float) and type(maximum) in (int,float) else f'Up to {maximum}' if type(maximum) in (int,float) else f'{minimum}+' if type(minimum) in (int,float) else None
        price=record.get('ticket_cost');low=record.get('min_ticket_cost');high=record.get('max_ticket_cost')
        cost=f'GBP {low}–{high}' if type(low) in (int,float) and type(high) in (int,float) and high!=low else 'FREE' if type(price) in (int,float) and price==0 else f'GBP {price}' if type(price) in (int,float) else None
        requirements=BeautifulSoup(record.get('requirements') or '','html.parser').get_text(' ',strip=True)
        booking='Booking required' if record.get('requires_booking') else 'No booking required'
        time_text=start.strftime('%I:%M %p').lstrip('0')+' - '+end.strftime('%I:%M %p').lstrip('0')
        if provider_mode and kind!='activity': raise CalendarError('Reviewed session no longer has regular activity evidence')
        key=(namespace,str(record['series_id'])) if provider_mode else (title.casefold(),venue.casefold(),kind,record['event_id'] if kind=='event' else '')
        item=groups.setdefault(key,dict(title=title,description=description+' '+requirements+' '+booking,
            listing_type=kind,family_evidence='Public programme description',audience='families',family_relevance=5,confidence=.99,
            venue_name=venue,location=venue,event_url=target,age_range=age,cost_text=cost,
            start_date=start.date().isoformat(),end_date=end.date().isoformat(),time_text=time_text,
            recurrence=recurrence or 'Named regular programme series',category='story_rhyme' if re.search('rhyme|story',title,re.I) else None,
            occurrence_dates=[],schedule_text=None,occurrence_times=[],conditions=set()))
        if provider_mode:
            item.setdefault('provider_occurrences',[]).append({'id':record['event_id'],'url':target,
                'date':start.date().isoformat(),'time':time_text})
            item.update(provider_namespace=namespace,provider_session_id=str(record['series_id']))
        item['occurrence_dates'].append(start.date().isoformat())
        item['occurrence_times'].append((start.date().isoformat(),time_text))
        item['conditions'].add((age,cost,requirements,booking,venue,record.get('location_id')))
        reject('accepted_occurrences')
    items=[]
    for item in groups.values():
        conditions=item.pop('conditions')
        times=sorted(set(item.pop('occurrence_times')))
        if len(conditions)>1:
            reject('programme_conditions_require_review'); continue
        if provider_mode: item.update(metadata(namespace,item['provider_session_id'],item['provider_occurrences']))
        item['occurrence_dates']=sorted(set(item['occurrence_dates']))
        if item['listing_type']=='activity':
            if len({clock for _,clock in times})==1:
                item['schedule_text']='Published dates: '+', '.join(item['occurrence_dates'])+'; '+item['time_text']
            else:
                item['schedule_text']='Published dates: '+'; '.join(date+' '+clock for date,clock in times)
                item['time_text']=None
            if len(item['schedule_text'])>300: raise CalendarError('Published schedule exceeds storage limit')
        items.append(item)
    return items,hashlib.sha256(html.encode('utf-8')).hexdigest(),stats

def fetch_portal(url):
    import requests
    response=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)'},timeout=(5,20))
    response.raise_for_status()
    if response.url!=url: raise CalendarError('Unreviewed portal redirect')
    response.encoding='utf-8'
    return response.text
