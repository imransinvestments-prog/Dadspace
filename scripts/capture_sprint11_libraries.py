"""Bounded primary-source qualification. Never apply proposals or bypass access controls."""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
DIRECTORIES={
 'Ealing':'https://libraries.ealing.gov.uk/digital-content/find-my-library',
 'Hounslow':'https://www.hounslow.gov.uk/libraries',
 'Brent':'https://www.brent.gov.uk/homelibrary',
 'Westminster':'https://www.westminster.gov.uk/leisure-libraries-and-community/libraries',
 'Camden':'https://www.camden.gov.uk/library-information',
 'Kensington and Chelsea':'https://www.rbkc.gov.uk/libraries-0',
 'Hillingdon':'https://www.hillingdon.gov.uk/libraries',
 'Richmond upon Thames':'https://www.richmond.gov.uk/services/libraries/branch_libraries',
 'Wandsworth':'https://www.wandsworth.gov.uk/our-libraries',
 'Barnet':'https://www.barnet.gov.uk/libraries/find-your-local-library',
 'Harrow':'https://www.harrow.gov.uk/libraries/harrow-library-branches',
 'Kingston upon Thames':'https://libraries.kingston.gov.uk/home',
 'Hammersmith and Fulham':'https://www.lbhf.gov.uk/libraries',
}
EXACT={'ecee5509-dc62-4ffc-a105-f814bd8cbd84':'https://libraries.ealing.gov.uk/digital-content/find-my-library/st-bernard-hospital-library'}
UA='DadspaceSourceReview/1.0'
def fetch(url):
    result={'url':url,'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'state':'unavailable','links':[]}
    try:
        origin=urlsplit(url); robots=requests.get(f'{origin.scheme}://{origin.netloc}/robots.txt',headers={'User-Agent':UA},timeout=15)
        result['robots_status']=robots.status_code
        if robots.status_code==200:
            policy=RobotFileParser();policy.parse(robots.text.splitlines())
            if not policy.can_fetch(UA,url):result['state']='robots_disallowed';return result
        elif robots.status_code not in (404,410):result['state']='robots_unavailable';return result
        response=requests.get(url,headers={'User-Agent':UA},timeout=20)
        result.update(http_status=response.status_code,final_url=response.url)
        if response.status_code!=200:result['state']='http_unavailable';return result
        if 'text/html' not in response.headers.get('Content-Type',''):result['state']='not_html';return result
        soup=BeautifulSoup(response.text,'html.parser')
        anchors=[{'label':a.get_text(' ',strip=True)[:160],'url':urljoin(response.url,a['href'])} for a in soup.select('a[href]') if 'librar' in (a.get_text(' ',strip=True)+' '+a['href']).lower() and urljoin(response.url,a['href']).startswith('https://')][:200]
        for tag in soup(['script','style','nav','header','footer']):tag.decompose()
        text=' '.join(soup.get_text(' ',strip=True).split())
        if re.search(r'pardon our interruption|just a moment|verify you are human',text,re.I):
            result['state']='access_challenge';return result
        result.update(state='fetched_not_fact_approved',content_sha256=hashlib.sha256(response.content).hexdigest(),title=soup.title.get_text(strip=True) if soup.title else '')
        # Links are source-published candidates, not automatic identity matches.
        result['links']=anchors
        result['postcodes']=sorted(set(re.findall(r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',text)))
        # Short factual timetable evidence only, never a full page copy.
        lines=[node.get_text(' ',strip=True) for node in soup.select('tr,li,p')]
        result['hours_evidence']=[line for line in lines if re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',line) and len(line)<100][:7]
        # Only the small relevant primary-source restriction excerpt is retained.
        if 'st-bernard' in url and 'patients only' in text.lower():result['restriction']='patients only'
    except requests.RequestException as exc:result['error_type']=type(exc).__name__
    return result

def main():
    libraries=json.loads((ROOT/'artefacts/data/sprint11-libraries-snapshot.json').read_text())
    ids={r['id'] for r in libraries['rows']}
    provenance=json.loads((ROOT/'artefacts/data/sprint11-library-provenance.json').read_text())
    provenance['rows']=[r for r in provenance['rows'] if r['venue_id'] in ids]
    (ROOT/'artefacts/data/sprint11-library-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    urls=list(dict.fromkeys([*DIRECTORIES.values(),*EXACT.values()]))
    with cf.ThreadPoolExecutor(max_workers=3) as pool:sources=dict(zip(urls,pool.map(fetch,urls)))
    # Follow only directory links published by the official operator, at most one level.
    next_urls=list(dict.fromkeys(link['url'] for source in sources.values() for link in source['links'] if link['label'].lower() in ('local community hub and libraries','your local library','library branches','our libraries','find a library')))
    with cf.ThreadPoolExecutor(max_workers=3) as pool:sources.update(zip(next_urls,pool.map(fetch,next_urls)))
    def normalized(name):return ' '.join(re.sub(r'\b(public|library|libraries|community|hub|and)\b','',re.sub(r'[^a-z0-9 ]','',str(name).lower())).split())
    branches={}
    for venue in libraries['rows']:
        p=next((r for r in provenance['rows'] if r['venue_id']==venue['id']),{})
        root=DIRECTORIES.get(p.get('authority'))
        root_source=sources.get(root,{})
        operator_pages=[root_source]+[sources.get(link['url'],{}) for link in root_source.get('links',[])]
        matches=list(dict.fromkeys(link['url'] for source in operator_pages for link in source.get('links',[]) if normalized(link['label'])==normalized(venue.get('venue_name')) and normalized(venue.get('venue_name'))))
        if len(matches)==1:branches[venue['id']]=matches[0]
    branch_urls=list(dict.fromkeys([*branches.values()]))
    with cf.ThreadPoolExecutor(max_workers=3) as pool:sources.update(zip(branch_urls,pool.map(fetch,branch_urls)))
    rows=[]
    for venue in libraries['rows']:
        p=next((r for r in provenance['rows'] if r['venue_id']==venue['id']),{})
        url=EXACT.get(venue['id']) or branches.get(venue['id']) or DIRECTORIES.get(p.get('authority'))
        source=sources.get(url,{})
        restricted=p.get('reference_type')=='Prison Library' or source.get('restriction')=='patients only'
        branch=venue['id'] in branches or venue['id'] in EXACT
        postcode_match=bool(venue.get('postcode')) and venue['postcode'].replace(' ','').upper() in [pc.replace(' ','').upper() for pc in source.get('postcodes',[])]
        changes={'website':url} if source.get('state')=='fetched_not_fact_approved' else {}
        if branch and postcode_match and source.get('hours_evidence'):changes['opening_hours']='; '.join(source['hours_evidence'])[:1000]
        rows.append({'id':venue['id'],'name':venue.get('venue_name'),'postcode':venue.get('postcode'),'distance_km':venue.get('distance_km'),'before_fingerprint':venue.get('fingerprint'),'authority':p.get('authority'),'reference_type':p.get('reference_type'),'official_source_candidate':url,'source_kind':'branch_candidate' if branch else 'operator_directory','postcode_in_source':postcode_match,'source_state':source.get('state','not_qualified'),'checked_at':source.get('checked_at'),'proposed_changes':changes,'opening_hours':changes.get('opening_hours'),'fee':None,'access':source.get('restriction'),'review_state':'restricted_access_review' if restricted else 'branch_identity_and_visitor_facts_review','unknowns':['Current branch identity/address requires comparison','Current hours and holiday exceptions','Entry/service charges','Step-free access and visitor restrictions','Image rights'], 'applied':False})
    result={'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'All 105 published library-category candidates within 10 km of W3 9LN; Hounslow regression included. Not all are publicly accessible libraries.','production_writes':0,'rows':rows,'sources':list(sources.values())}
    (ROOT/'artefacts/data/sprint11-library-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'sources':{u:r['state'] for u,r in sources.items()},'authorities_remaining':sorted({r['authority'] for r in rows if not r['official_source_candidate']})}))
if __name__=='__main__':main()
