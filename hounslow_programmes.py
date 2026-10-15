"""Source-reviewed Hounslow programme details, using normal HTTP and robots.

The council-linked category requires rendering, but this reviewed detail route
contains the complete regular programme. No model, generated dates or activation.
"""
import hashlib
import html as html_escape
import re
from bs4 import BeautifulSoup, NavigableString, Comment

REVIEWED_URLS = {'https://hounslowconnect.com/services/storytime-at-chiswick-community-hub-and-library'}

def _block(soup, heading):
    matches = [h for h in soup.find_all('h2') if h.get_text(' ', strip=True) == heading]
    if len(matches) != 1:
        raise ValueError('Programme heading missing or ambiguous')
    parts=[]
    for node in matches[0].next_elements:
        if getattr(node,'name',None)=='h2':
            break
        if getattr(node,'name',None) in ('h3','h4'):
            parts.append(f'<{node.name}>{html_escape.escape(node.get_text(" ",strip=True))}</{node.name}>')
        elif isinstance(node,NavigableString) and not isinstance(node,Comment) and node.parent.name not in ('h2','h3','h4','script','style'):
            parts.append(html_escape.escape(str(node)))
    return BeautifulSoup('<section>'+' '.join(parts)+'</section>','html.parser')

def parse_programme(html, url):
    if url not in REVIEWED_URLS:
        raise ValueError('Programme route has not been reviewed')
    soup = BeautifulSoup(html, 'html.parser')
    # This operator places its title outside the main content container.
    main = soup
    titles = main.find_all('h1')
    if len(titles) != 1:
        raise ValueError('Programme title missing or ambiguous')
    title = titles[0].get_text(' ',strip=True)
    body = re.sub(r'\s+',' ',_block(main, 'What is this service?').get_text(' ',strip=True))
    key = re.sub(r'\s+',' ',_block(main, 'Key information').get_text(' ',strip=True))
    location = _block(main, 'Location')
    branch = location.find('h3')
    if not branch:
        raise ValueError('Canonical place evidence missing')
    venue = branch.get_text(' ',strip=True)
    local = re.sub(r'\s+',' ',location.get_text(' ',strip=True))
    postcode = re.search(r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',local)
    age = re.search(r'Ages?\s+(\d+)\s*[-–]\s*(\d+)\s*(?:years)?',key,re.I)
    when = re.search(r'When:\s*(.*?)\s*Time:',body,re.I)
    clock = re.search(r'Time:\s*(.*?)(?:Who can attend|How to join|Storytime sessions)',body,re.I)
    exceptions = re.findall(r'(\d{2}/\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{2}/\d{4})',body)
    if not postcode or not age or not when or not clock or not re.search(r'\bEvery\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',when[1],re.I):
        raise ValueError('Complete age, location or regular schedule evidence missing')
    if int(age[1]) > 5 or int(age[2]) < int(age[1]):
        raise ValueError('Programme audience requires separate review')
    if 'term-time' in body.lower() and ('school holidays' not in body.lower() or not exceptions):
        raise ValueError('Term-time exceptions missing; do not publish an incomplete schedule')
    schedule = when[1].strip() + '; ' + clock[1].strip()
    if 'school holidays' in body.lower():
        schedule += '; no school holidays: ' + '; '.join(f'{start}–{end}' for start,end in exceptions)
    if len(schedule) > 300:
        raise ValueError('Complete schedule exceeds normal worker limit; needs review')
    address = local[:postcode.end()]
    address = address.removeprefix('Location').strip()
    return [{'title':title,'description':f'{title}. Booking required.' if 'booking is required' in body.lower() else title,
      'listing_type':'activity','category':'libraries','start_date':None,'end_date':None,'occurrence_dates':[],
      'schedule_text':schedule,'time_text':clock[1].strip(),'venue_name':venue,'venue_address':address,
      'postcode':postcode[0],'location':venue,'event_url':url,'cost_text':'Free' if re.search(r'Cost:\s*Free\b',body,re.I) else None,
      'age_range':f'{age[1]}–{age[2]} years','recurrence':'recurring','audience':'children',
      'family_evidence':f'Published ages {age[1]}–{age[2]}; regular library programme','family_relevance':5,'confidence':0.98}]

def collect(source,today,fetch,robots,stats=None):
    url=source.get('url')
    if url not in REVIEWED_URLS:
        raise ValueError('Programme route has not been reviewed')
    allowed,_=robots(url)
    if not allowed:
        raise ValueError('Programme blocked by robots')
    html=fetch(url)
    rows=parse_programme(html,url)
    stats=stats if stats is not None else {}
    stats.update(extracted=len(rows),structured_events=len(rows),api_attempts=0)
    return rows,hashlib.sha256(repr(rows).encode()).hexdigest(),stats
