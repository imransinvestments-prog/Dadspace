"""Parse council Rhymetime snapshots; unattended crawling remains disabled."""
import re
from urllib.parse import urlsplit,parse_qs
from session_proposals import proposal

HOST='info.cambridgeshire.gov.uk'
def parse_snapshots(snapshot, programme='rhymetime'):
    if programme not in ('rhymetime','storytime') or snapshot.get('capture_method')!='public-browser-review' or snapshot.get('programme')!=programme:
        raise ValueError('Unqualified snapshot origin/programme')
    observed=set(snapshot['observed_detail_urls']);seen=set();items=[];issues=[]
    clock=re.compile(r'\b(?:\d{1,2}[:.]\d{2}(?:\s*[ap]m)?|\d{1,2}\s*[ap]m)\b',re.I)
    for record in snapshot['records']:
        url=record['url'];p=urlsplit(url);ids=parse_qs(p.query).get('id',[])
        if url not in observed or p.hostname!=HOST or p.scheme!='https' or p.username or p.password or p.port not in (None,443) or not p.path.endswith('/directory/service.page') or len(ids)!=1:
            raise ValueError('Unobserved/foreign detail URL')
        if ids[0] in seen:raise ValueError('Duplicate service snapshot')
        seen.add(ids[0]);fields=record['fields'];name=record['title']
        if record.get('relocation'):
            issues.append(dict(title=name,url=url,reason='Temporary relocation: resolve each published date/location before using the usual branch address'))
            continue
        venue=fields.get('Name') or fields.get('Parent Organisation') or ''
        if not venue:
            match=re.search(r'\bat (.+ Library)\s*$',name)
            venue=match[1] if match else ''
        address=fields.get('Address','');postcode=fields.get('Postcode','')
        note=fields.get('Time/date notes','');hours=fields.get('Opening Hours','')
        if not re.search(r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday',note,re.I):
            issues.append(dict(title=name,url=url,reason='Missing programme weekday'));continue
        if not hours and len(clock.findall(note))<2:
            issues.append(dict(title=name,url=url,reason='Missing published session clock range'));continue
        ages=fields.get('Age Ranges','')
        if not ages:
            band=re.search(r'\b(?:aged|ages?|for)\s+((?:birth|\d+)\s*(?:to|[-–])\s*\d+\s*(?:years?|months?))',record.get('description',''),re.I)
            ages=band[1] if band else ''
        flags=list(record.get('restrictions',[]))
        for flag in record.get('review_flags',[]):
            flags.append(flag)
            issues.append(dict(title=name,url=url,reason=flag))
        if not address or not postcode:flags.append('Street address/postcode missing on source; match the named branch before application')
        if not ages:flags.append('Published age band missing; needs review')
        schedule=note+('; '+hours if hours else '')
        if len(schedule)>300:raise ValueError('Schedule exceeds storage limit; no silent truncation')
        notes='; '.join([fields.get('Details',''),*flags,'Recurring Activity; dates are not generated from the weekday','Snapshot-derived proposal; unattended source access not qualified'])
        item=proposal(name,venue,', '.join(x for x in [address.replace('\n',', '),postcode] if x) or venue,ages,schedule,url,dates='',notes=notes)
        if record.get('booking_url'):
            from session_proposals import public_link
            link=public_link(url,record['booking_url'])
            if not link:raise ValueError('Invalid published booking/date link')
            item['booking_url']=link
        items.append(item)
        if not address or not postcode or not ages:issues.append(dict(title=name,url=url,reason='Missing branch address/postcode or published age band; proposal retained for review'))
    if seen!=set(parse_qs(urlsplit(u).query)['id'][0] for u in observed):
        raise ValueError('Observed detail coverage is incomplete')
    if not snapshot.get('index_capture_complete'):issues.append(dict(reason='Directory pagination not proven complete'))
    return items,issues
