"""Section-specific Scout timetable extraction from reviewed public routes."""
import re
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
from session_proposals import proposal,public_link

SECTIONS='Squirrels|Beavers|Cubs|Scouts|Explorers'
DAY=r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)(?:s|\x27s)?'
CLOCK=r'\d{1,2}(?:[:.]\d{2})?\s*(?:[ap]m)?'
MEETING=re.compile(r'('+DAY+r'|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+('+CLOCK+r'\s*(?:-|–|to)\s*'+CLOCK+r')',re.I)

def visible_text(document,selector=None):
    soup=BeautifulSoup(document,'html.parser')
    root=soup.select_one(selector) if selector else soup.select_one('main') or soup
    if root is None:raise ValueError('Expected timetable content container missing')
    for e in root.select('script,style,nav,footer,header'):e.decompose()
    return re.sub(r'\s+',' ',root.get_text(' ',strip=True)).replace('Â½','½').replace('Â¾','¾')

def extract_group(document,group,url,standard_ages):
    mode=group['adapter'];body=visible_text(document,'#main' if mode=='crafts-hill' else '.item-page' if mode=='milton' else None)
    rows=[];issues=[]
    if mode=='crafts-hill':
        if 'Sections Available' not in body:raise ValueError('Sections Available block missing')
        section_body=body.split('Sections Available',1)[1].split('Contact Information',1)[0]
        for match in re.finditer(r'\b('+SECTIONS+r')\b(.*?)(?=\b(?:'+SECTIONS+r')\b|$)',section_body):
            section,detail=match.groups()
            if 'Not Currently Available' in detail:
                issues.append(section+': explicitly unavailable');continue
            label={'Squirrels':'Squirrel Drey','Beavers':'Beaver Colony','Cubs':'Cub Pack','Scouts':'Scout Troop'}.get(section,section)
            age=re.search(re.escape(label)+r'\s*\(([^)]+)\)',body)
            meetings=list(MEETING.finditer(detail))
            if not meetings:issues.append(section+': missing published weekday/time');continue
            for meeting in meetings:rows.append((section,age[1] if age else '',meeting[0],[]))
    elif mode=='orchard':
        for match in re.finditer(r'1st Cambridge (Beaver Scouts|Cub Scouts|Scouts)\s+('+DAY+r'\s+'+CLOCK+r'\s*(?:-|–)\s*'+CLOCK+r')',body,re.I):
            section={'Beaver Scouts':'Beavers','Cub Scouts':'Cubs','Scouts':'Scouts'}[match[1]]
            rows.append((section,standard_ages[section],match[2],['Age band from county section reference: '+group['age_evidence_url']]))
    elif mode=='duxford':
        chunk=body.split('Our Group Sections',1)[-1].split('Hiring the Scout Hut',1)[0]
        for match in re.finditer(r'\b('+SECTIONS+r')\s+Ages\s+([^ ]+)\s+(.*?)(?=\b(?:'+SECTIONS+r')\s+Ages|$)',chunk):
            section,age,detail=match.groups()
            if 'waiting lists across other sections' in body and section!='Beavers':
                issues.append(section+': waiting list only');continue
            for named in re.finditer(r'([^()]+)\(('+MEETING.pattern+r')\)',detail):
                rows.append((named[1].strip(),age,named[2],[]))
    elif mode=='milton':
        section=group['section'];meeting=re.search(r'When:\s*(.*?)\s+Subscriptions:',body)
        if not meeting:issues.append(section+': no published meeting time');return [],issues
        age=re.search(r'aged (?:between|from) (.*?)(?:years old|years\.)',body)
        age_value=age[1].strip() if age else ''
        if not age_value:issues.append(section+': published age band missing')
        rows.append((section,age_value,meeting[1],[]))
    elif mode=='fulbourn':
        section=group['section'];meeting=re.search(r'Meeting Time\s+('+DAY+r'\s+'+CLOCK+r'\s*(?:-|–)\s*'+CLOCK+r')',body,re.I)
        age=re.search(r'\(Ages?:?\s*([^)]*)\)',body)
        if not meeting:issues.append(section+': no published meeting time');return [],issues
        flags=[]
        if section=='Beavers' and '7½ to 8½' in body and 'between 6 and 8' in body:
            flags.append('Age heading says 7½ to 8½ but body says 6–8; resolve eligibility before application')
            issues.append('Beavers: conflicting published age ranges')
        rows.append((section,age[1] if age else '',meeting[1],flags))
    else:raise ValueError('Unsupported Scout timetable adapter')
    out=[]
    for section,ages,schedule,flags in rows:
        if not MEETING.search(schedule):issues.append(section+': invalid/missing clock range');continue
        notes=['Recurring Activity; no individual dates generated','Membership enquiry required; remaining places unconfirmed','Venue/address from reviewed HAY directory; confirm section meeting place before application',*flags]
        out.append(proposal(group['title']+' — '+section,group['title'],group['location'],ages,schedule,url,dates='',notes='; '.join(notes)))
    if not out and not issues:issues.append('No supported section timetable found')
    return out,issues

def collect_scouts(fetch,manifest):
    proposals=[];issues=[];statuses=[]
    # A reviewed directory address is not a current, section-specific venue match.
    issues.append('HAY address inventory is a reviewed snapshot; current HTTP route returned 403. Locations require confirmation.')
    for group in manifest['groups']:
        if not group.get('url'):
            statuses.append(dict(title=group['title'],status='needs review',reason=group['reason']))
            issues.append(group['title']+': '+group['reason']);continue
        try:
            document,actual=fetch(group['url']);count=0;flags=[]
            if group['adapter']=='waiting-list':
                if 'Currently all our sections are full' not in visible_text(document):raise ValueError('Waiting-list status changed; timetable needs re-review')
                flags=['All sections full; membership waiting list only']
            elif group['adapter'] in ('milton','fulbourn'):
                soup=BeautifulSoup(document,'html.parser')
                links={a.get_text(' ',strip=True):public_link(actual,urljoin(actual,a['href'])) for a in soup.select('a[href]') if a.get_text(' ',strip=True) in ['Squirrels','Beavers','Cubs','Scouts','Explorers'] and urlsplit(urljoin(actual,a['href'])).hostname==urlsplit(actual).hostname}
                for section,url in links.items():
                    body,route=fetch(url);local=dict(group,section=section)
                    items,problems=extract_group(body,local,route,manifest['standard_age_bands'])
                    proposals.extend(items);count+=len(items);flags.extend(problems)
            else:
                items,flags=extract_group(document,group,actual,manifest['standard_age_bands']);proposals.extend(items);count=len(items)
            statuses.append(dict(title=group['title'],proposals=count,status='extracted' if count else 'needs review',issues=flags))
            issues.extend(group['title']+': '+flag for flag in flags)
        except Exception as error:
            statuses.append(dict(title=group['title'],status='needs review',reason=str(error)));issues.append(group['title']+': '+str(error))
    return proposals,issues,statuses
