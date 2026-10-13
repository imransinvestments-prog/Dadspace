"""Extract public Wix booking cards; reconcile timetables without inventing dates."""
import datetime as dt,re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from session_proposals import proposal,public_link

def text(document):
    s=BeautifulSoup(document,'html.parser')
    return re.sub(r'[\s\u200b]+',' ',(s.select_one('main') or s).get_text(' ',strip=True))

def parse_gkfit(book,daytime,netball,holiday,today):
    day=text(daytime);net=text(netball);hol=text(holiday)
    contexts={
        'Hauxton Centre':(day,r'Hauxton Centre\s+(Church Road, Hauxton,.*?CB22\s*5HS)'),
        'Meadows Community Centre':(day,r'Meadows Community Centre\s+(299 Arbury Road,.*?CB4\s*2JL)'),
        'Royston Leisure Centre':(day,r'Royston Leisure Centre\s+(29 Woodcock Road,.*?SG8\s*7XT)'),
        'Girton Rec':(net,r'Girton Rec,\s*(Cambridge Road, Girton,.*?CB3\s*0FH)'),
        'Netherhall School':(net,r'Netherhall School,\s*(Queen Edith.s Way,.*?CB1\s*8NN)'),
        'Cherry Hinton Leisure Centre':(hol,r'Cherry Hinton Leisure Centre\s+(Colville Road,.*?CB1\s*9EJ)')}
    addresses={k:(m[1] if (m:=re.search(pattern,body)) else '') for k,(body,pattern) in contexts.items()}
    # Full applies to the age-specific class, not to the whole operator/venue.
    full=set()
    for venue,start,end in [('Girton Rec','Netball Mondays at Girton','Netball Wednesdays'),('Netherhall School','Netball Wednesdays at Netherhall','New! Game Night')]:
        section=net.split(start,1)[-1].split(end,1)[0]
        for match in re.finditer(r'school years\s+(\d+-\d+)(.*?)(?=\d{1,2}\.\d{2}-\d{1,2}\.\d{2}:|Class fully booked|$)',section,re.I):
            if re.search(r'\bFull\b',match[2]):full.add((venue,match[1]))
    hauxton=day.split('Hauxton Thursdays',1)[-1].split('Class fully booked',1)[0]
    if re.search(r'Age 5-8\s+Age 9-12\s+Book\s+Full',hauxton):full.add(('Hauxton Centre','9-12'))
    cards=BeautifulSoup(book,'html.parser').select('[data-hook="service-card-default-card"]')
    if not cards:raise ValueError('No recognised GK Fit booking cards; adapter needs review')
    items=[];issues=[];seen=set()
    for card in cards:
        def value(hook):
            e=card.select_one(f'[data-hook="{hook}"]');return e.get_text(' ',strip=True) if e else ''
        name=value('service-info-title-text');tag=value('tag-line-text')
        anchor=card.select_one('[data-hook="service-info-title-link"]')
        if not name or not anchor:raise ValueError('Incomplete booking card')
        url=public_link('https://www.gkfit.co.uk/book',anchor.get('href',''))
        if urlsplit(url).hostname!='www.gkfit.co.uk' or not urlsplit(url).path.startswith('/service-page/'):
            raise ValueError('Foreign or unsupported booking route')
        if url in seen:continue
        seen.add(url)
        if re.search(r'\bEnded\b',value('details-root')):
            issues.append(dict(title=name,url=url,reason='Provider marks this course ended; excluded even if a cached timetable suggests otherwise'));continue
        venue=next((k for k in addresses if k in tag),'')
        if 'Netherhall' in tag:venue='Netherhall School'
        if tag.startswith('Cherry Hinton,'):venue='Cherry Hinton Leisure Centre'
        if not venue or not addresses[venue]:
            issues.append(dict(title=name,url=url,reason='Missing supported venue/address; no location inferred'));continue
        band=re.search(r'(?:age\s+|Y)(\d+-\d+)',name,re.I)
        ages=('School years ' if band and re.search(r'\bY\d',name) else '')+(band[1] if band else '')
        if not name.startswith('Game Night') and (venue,band[1] if band else '') in full:
            issues.append(dict(title=name,url=url,reason='Age-specific timetable class is full; waiting list only'));continue
        if not re.search(r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b',tag):
            issues.append(dict(title=name,url=url,reason='Missing published weekday'));continue
        if not re.search(r'\d[.:]\d{2}|\d\s*[ap]m',tag,re.I):
            issues.append(dict(title=name,url=url,reason='Missing published clock time'));continue
        dates='';notes=['Booking required; live place availability is unconfirmed', 'Published course price: '+value('service-info-sr-only-price')]
        status=value('details-root')
        if status:notes.append('Published course status/start label: '+status+'; not an individual occurrence date')
        schedule=tag
        if name.startswith('Game Night'):
            date_match=re.search(r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) \d{1,2} [A-Za-z]+, \d{4})',net)
            short=re.search(r'(\d{1,2}) ([A-Za-z]{3})',name)
            if not date_match or not short:raise ValueError('Game Night date/year not supported by timetable')
            date=dt.datetime.strptime(date_match[1],'%A %d %B, %Y').date()
            if date.strftime('%d %b').lstrip('0')!=f'{int(short[1])} {short[2]}':
                issues.append(dict(title=name,url=url,reason='No matching fully dated timetable occurrence'));continue
            dates=date.isoformat();notes.append('Recurring Game Night Activity; girls only; understanding of netball required; each occurrence booked separately')
        elif name.startswith('Half-term holiday'):
            date_match=re.search(r'(\d{1,2} [A-Za-z]+ \d{4})',name)
            if not date_match:raise ValueError('Holiday occurrence lacks explicit year')
            dates=dt.datetime.strptime(date_match[1],'%d %b %Y').date().isoformat()
            ages='11-15 years';notes.append('Holiday programme occurrence; classification requires review of regularity, not automatic Event classification')
        else:
            schedule+='; term-time'
            notes.append('Recurring Activity; no individual dates or course end generated from term length')
            if venue in ('Meadows Community Centre','Hauxton Centre','Royston Leisure Centre'):notes.append('Daytime classes for children out of school or home educated; age guidance')
            if venue=='Royston Leisure Centre':notes.append('Nov-Dec booking card supersedes the older September-October timetable; year/end dates not explicit, verify before dated application')
        if dates and dt.date.fromisoformat(dates)<today:
            issues.append(dict(title=name,url=url,reason='Past dated occurrence'));continue
        if not ages:notes.append('Published age band missing; review required')
        items.append(proposal(name,venue,addresses[venue],ages,schedule,'https://www.gkfit.co.uk/book',booking_url=url,dates=dates,notes='; '.join(notes)))
    issues.append(dict(reason='Little Skills, mobile and one-to-one coaching have no published individual venue/timetable; interest-only offerings were not fabricated'))
    return items,issues
