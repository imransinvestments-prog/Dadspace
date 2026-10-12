"""Evidence-preserving splits of reviewed public timetables; no database writes."""
import datetime as dt
import hashlib
import re
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup

def public_link(base,target):
    u=urljoin(base,target);p=urlsplit(u)
    if p.scheme!='https' or p.username or p.password or p.port not in (None,443):raise ValueError('Invalid public evidence link')
    return u

def proposal(name,venue,location,ages,schedule,evidence_url,booking_url='',dates='',notes=''):
    postcode=re.search(r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',location)
    # A date-specific library occurrence has its own identity; a rolling class
    # retains its observed booking identity. Dates are never expanded from days.
    route=booking_url or evidence_url
    p=urlsplit(route);irn=re.search(r'/([0-9]+),[0-9]+$',p.path)
    if p.hostname=='herts.spydus.co.uk' and irn:route='herts.spydus:IRN:'+irn[1]
    identity='|'.join((name.casefold(),venue.casefold(),route,dates,schedule.casefold()))
    return dict(name=name,venue=venue,location=location,postcode=postcode.group() if postcode else '',ages=ages,schedule=schedule,evidence_url=evidence_url,booking_url=booking_url,dates=dates,notes=notes,proposal_key=hashlib.sha256(identity.encode()).hexdigest())

def parse_spydus(document,url,today):
    soup=BeautifulSoup(document,'html.parser');out=[]
    for card in soup.select('.card-record-body'):
        title=card.select_one('.card-title a[href]');details=card.select('.recdetails > span')
        if title is None or len(details)<2:continue
        raw=details[0].get_text(' ',strip=True)
        m=re.fullmatch(r'(\d{1,2} \w{3} \d{4}) - (\d{1,2}:\d{2} [AP]M) to (\d{1,2}:\d{2} [AP]M)',raw)
        if not m:raise ValueError('Library occurrence date/time requires review')
        date=dt.datetime.strptime(m[1],'%d %b %Y').date()
        start=dt.datetime.strptime(m[2],'%I:%M %p');end=dt.datetime.strptime(m[3],'%I:%M %p')
        if end<=start:raise ValueError('Library occurrence ends before it starts')
        if date<today:continue
        name=title.get_text(' ',strip=True);venue=details[1].get_text(' ',strip=True)
        summary=card.select_one('.summary');text=summary.get_text(' ',strip=True) if summary else ''
        band=re.search(r'\b(?:ages?|aged)\s+\d+(?:\s*[-–to]+\s*\d+)?(?:\s*(?:years?|months?))?',text,re.I)
        ages=band.group() if band else 'Pre-school children' if re.search(r'pre-school',text,re.I) else 'Babies; numeric age band not stated' if name.casefold()=='baby rhyme time' else ''
        restrictions=[]
        if re.search(r'term time',text,re.I):restrictions.append('Term time only')
        if re.search(r'no booking|don.t have to book',text,re.I):restrictions.append('No advance booking required')
        if re.search(r'free',text,re.I):restrictions.append('Free; check source for donations/entry limits')
        link=public_link(url,title['href'])
        out.append(proposal(name,venue,venue,ages,date.isoformat()+'; '+m[2]+'–'+m[3],link,link,date.isoformat(),'; '.join(restrictions)+('; Exact age band/address need checking' if not ages else '; Check branch address')))
    if not soup.select('.card-record-body'):raise ValueError('Library index is a shell or unsupported layout')
    next_links=[public_link(url,a['href']) for a in soup.select('a[href]') if re.match(r'^next(?:\b|$)',a.get_text(' ',strip=True),re.I) or a.get('aria-label','').lower()=='next' or 'next' in (a.get('rel') or [])]
    return out,list(dict.fromkeys(next_links))

def parse_mini_athletics(document,url,today):
    soup=BeautifulSoup(document,'html.parser');out=[];exceptions=[]
    for section in soup.select('div.contained'):
        heading=section.find('h2',recursive=False);address=section.find('p',recursive=False)
        if heading is None or address is None:continue
        venue=heading.get_text(' ',strip=True);location=address.get_text(' ',strip=True)
        for row in section.select('table tbody tr'):
            cells={c.get('data-title'):c.get_text(' ',strip=True) for c in row.select('td[data-title]')}
            if not all(cells.get(k) for k in ('Class','Time','Dates')):raise ValueError('Incomplete Mini Athletics timetable row')
            link=row.select_one('td[data-title="Book now"] a[href]')
            if link is None:exceptions.append(dict(venue=venue,reason='No booking/availability route'));continue
            booking=public_link(url,link['href']);name=cells['Class'];date_text=cells['Dates']
            if re.search(r'full|waiting list',cells.get('Spaces',''),re.I):
                exceptions.append(dict(venue=venue,name=name,reason='Full / waiting-list class',booking_url=booking));continue
            bounds=re.findall(r'\b\d{2}/\d{2}/\d{4}\b',date_text)
            if len(bounds)==2:
                first,last=[dt.datetime.strptime(d,'%d/%m/%Y').date() for d in bounds]
                if last<first:raise ValueError('Reversed programme bounds')
                if last<today:continue
            elif 'Rolling' not in date_text:raise ValueError('Unrecognised published programme dates')
            age=re.search(r'\b\d+½?(?:\s*[-–]\s*\d+½?)?\s*Years\b',name,re.I)
            notes=[cells.get('Cost',''),'Published term bounds: '+date_text,'No individual occurrence dates inferred']
            if re.search(r'School|Students Only',name,re.I):notes.append('School-specific eligibility; confirm enrolment requirement')
            out.append(proposal('Mini Athletics — '+name,venue,location,age.group() if age else '',cells['Time']+'; '+date_text,url,booking,'','; '.join(notes)))
    if not out and not exceptions:raise ValueError('No supported Mini Athletics timetable')
    return out,exceptions

def parse_stay_and_play(document,url):
    soup=BeautifulSoup(document,'html.parser')
    paragraphs=[p for p in soup.select('.prose p') if p.get_text(' ',strip=True).startswith('Tuesday:')]
    if len(paragraphs)!=1:raise ValueError('Missing unique centre timetable')
    lines=[s.strip() for s in paragraphs[0].get_text('\n',strip=True).splitlines() if s.strip()]
    out=[]
    addresses={}
    for p in soup.select('.not-prose p'):
        parts=p.get_text('\n',strip=True).splitlines()
        if parts and 'Child and Family' in parts[0]:addresses[parts[0]]=p.get_text(' ',strip=True)
    for h in soup.find_all(['h3','h4']):
        name=h.get_text(' ',strip=True)
        if 'Child and Family' in name:addresses[name]=h.find_next('p').get_text(' ',strip=True) if h.find_next('p') else ''
    # Explicit lines keep the published centre/time association. The address
    # spelling discrepancy remains a visible review flag rather than a merge.
    for line in lines:
        m=re.fullmatch(r'(Tuesday|Wednesday|Thursday|Friday):\s*(.+?)\s+(Fawcett|Chesterton|Berwick|North Cambridge|The Fields)(.*)',line)
        if not m:raise ValueError('Centre timetable line requires review: '+line)
        venue=m[3]+m[4];restricted='Term time only' in venue
        venue=re.sub(r'\s*\(Term time only\)','',venue).strip().strip(',')
        if 'Fawcett' in venue:venue='Fawcett Child and Family Zone'
        location=addresses.get(venue,addresses.get(venue.replace('Berwick','Bewick'),venue))
        out.append(proposal('Stay and Play — '+venue,venue,location,'10 months–5 years',m[1]+': '+m[2]+('; term time only' if restricted else ''),url,dates='',notes='Free; booking required by telephone/email. '+('Confirm Berwick/Bewick centre spelling.' if 'Berwick' in venue else 'Confirm branch address.')))
    if len(out)!=5:raise ValueError('Incomplete five-centre timetable')
    return out
