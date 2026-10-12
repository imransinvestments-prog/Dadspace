"""Bounded read-only proposal collection for the 11 selected aggregate records."""
import argparse,datetime as dt,hashlib,json,sys,re
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import requests
from bs4 import BeautifulSoup
from session_proposals import parse_spydus,parse_mini_athletics,parse_stay_and_play,public_link
from cambridgeshire_rhymetime import parse_snapshots
from gkfit_sessions import parse_gkfit
from scout_sessions import collect_scouts
from shredder_sessions import parse_shredder,VENUES
from salford_baby_gym import parse_baby_gym,URL as BABY_GYM_URL

def run(today,max_pages=2,record_id=None):
    cohort=json.loads((ROOT/'artefacts/data/ds10-action-console-19-2026-10-12.json').read_text(encoding='utf8'))
    records=[r for r in cohort['records'] if r['group']=='split' or record_id=='07f3ec2b-87cf-4ee0-95a1-5fd36d769afc' and r['id']==record_id]
    if record_id:
        records=[r for r in records if r['id']==record_id]
        if not records:raise ValueError('Unknown split-programme record ID')
    documents={};robots={};checks=[];attempts=0;ua='Dadspace session proposal review (+https://dad-space.co.uk)'
    def get(u):
        nonlocal attempts
        if attempts>=50:raise ValueError('Global network request budget reached')
        attempts+=1
        return requests.get(u,timeout=20,headers={'User-Agent':ua})
    def fetch(u):
        public_link(u,u)
        if u in documents:return documents[u]
        if len(checks)>=36:raise ValueError('Global request budget reached')
        host=urlsplit(u).netloc
        if host not in robots:
            rr=get('https://'+host+'/robots.txt');p=RobotFileParser()
            if rr.status_code==200:p.parse(rr.text.splitlines())
            elif rr.status_code==404:p.parse([])
            else:raise ValueError('Robots access unresolved: '+str(rr.status_code))
            robots[host]=p
        if not robots[host].can_fetch(ua,u):raise ValueError('Robots disallows requested route')
        response=get(u);response.raise_for_status()
        final=response.url;public_link(final,final)
        # Recheck redirects against the actual target host's public rules.
        final_host=urlsplit(final).netloc
        if final_host!=host and final_host not in robots:
            rr=get('https://'+final_host+'/robots.txt');p=RobotFileParser()
            if rr.status_code==200:p.parse(rr.text.splitlines())
            elif rr.status_code==404:p.parse([])
            else:raise ValueError('Redirect robots access unresolved')
            robots[final_host]=p
        if not robots[final_host].can_fetch(ua,final):raise ValueError('Redirect route disallowed by robots')
        documents[u]=(response.text,final)
        checks.append(dict(url=u,final_url=final,sha256=hashlib.sha256(response.content).hexdigest(),checked_at=dt.datetime.now(dt.timezone.utc).isoformat()))
        return documents[u]
    report=[];global_proposals={}
    for record in records:
        proposals=[];issues=[];complete=False
        try:
            if record['id']=='07f3ec2b-87cf-4ee0-95a1-5fd36d769afc':
                page,actual=fetch(BABY_GYM_URL);proposals=parse_baby_gym(page,actual)
                local={p['proposal_key']:p for p in proposals}
                for key,p in local.items():global_proposals[key]=dict(session=p,parent_record_ids=[record['id']])
                record['seed_sessions']=list(local.values());issues=['Recovered programme table; venue addresses and price discrepancy need review. Not live accepted supply.']
                record['automation']=dict(proposals=len(local),coverage_complete=True,issues=issues)
                report.append(dict(record_id=record['id'],title=record['title'],proposal_count=len(local),coverage_complete=True,issues=issues))
                continue
            if record['id']=='194fa725-deae-4074-bc85-0c62923cf618':
                home,base=fetch('https://www.shredderskateschool.co.uk/')
                soup=BeautifulSoup(home,'html.parser')
                route=next((public_link(base,a['href']) for a in soup.select('a[href]') if urlsplit(urljoin(base,a['href'])).path=='/choose-a-region'),None)
                if not route:raise ValueError('Region selector not observed')
                body,index=fetch(route)
                region=next((public_link(index,a['href']) for a in BeautifulSoup(body,'html.parser').select('a[href]') if a.get_text(' ',strip=True)=='CAMBRIDGESHIRE'),None)
                if not region:raise ValueError('Cambridgeshire region link missing')
                body,index=fetch(region)
                links=list(dict.fromkeys(public_link(index,a['href']) for a in BeautifulSoup(body,'html.parser').select('a[href]') if urlsplit(urljoin(index,a['href'])).hostname=='www.shredderskateschool.co.uk' and urlsplit(urljoin(index,a['href'])).path.lstrip('/') in VENUES))
                for link in links:
                    route=urlsplit(link).path.lstrip('/');venue,town=VENUES[route]
                    page,actual=fetch(link);items,flags=parse_shredder(page,actual,venue,town,home)
                    proposals.extend(items);issues.extend(venue+': '+flag for flag in flags)
                if len(links)!=len(VENUES):issues.append('Venue selector changed; reviewed routes are incomplete')
                local={p['proposal_key']:p for p in proposals}
                for key,p in local.items():global_proposals[key]=dict(session=p,parent_record_ids=[record['id']])
                record['seed_sessions']=list(local.values()) or record['seed_sessions']
                record['automation']=dict(proposals=len(local),coverage_complete=False,mode='coach/day review drafts; exact times unpublished',issues=issues)
                report.append(dict(record_id=record['id'],title=record['title'],proposal_count=len(local),coverage_complete=False,issues=issues))
                (ROOT/'artefacts/data/ds10-shredder-extraction-2026-10-12.json').write_text(json.dumps(dict(checked_on=today.isoformat(),sessions=proposals,issues=issues,reviewed_venue_routes=links,database_writes=0,coverage_complete=False),ensure_ascii=False,indent=2),encoding='utf8')
                continue
            if record['id']=='dd4e8663-1d52-49ba-a7c1-edd1f1d93c65':
                manifest=json.loads((ROOT/'artefacts/data/ds10-scout-group-routes-2026-10-12.json').read_text(encoding='utf8'))
                proposals,issues,statuses=collect_scouts(fetch,manifest)
                evidence=dict(checked_on=today.isoformat(),parent_record_id=record['id'],database_writes=0,groups=statuses,sessions=proposals,issues=issues,coverage_complete=False)
                (ROOT/'artefacts/data/ds10-scout-session-extraction-2026-10-12.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
                local={p['proposal_key']:p for p in proposals}
                for key,p in local.items():global_proposals[key]=dict(session=p,parent_record_ids=[record['id']])
                record['seed_sessions']=list(local.values()) or record['seed_sessions']
                record['automation']=dict(proposals=len(local),coverage_complete=False,issues=issues)
                report.append(dict(record_id=record['id'],title=record['title'],proposal_count=len(local),coverage_complete=False,issues=issues))
                continue
            snapshot_programmes={'368a7430-a54b-4c02-9af7-0d4702d740dc':'rhymetime','bbc6d669-367b-4eb4-9cde-18372c8afe77':'storytime'}
            if record['id'] in snapshot_programmes:
                programme=snapshot_programmes[record['id']]
                snap_path=ROOT/f'artefacts/data/ds10-cambridgeshire-{programme}-snapshot-2026-10-12.json'
                snap=json.loads(snap_path.read_text(encoding='utf8'))
                proposals,exceptions=parse_snapshots(snap,programme)
                issues=['Snapshot parsing available; unattended crawling blocked by provider robots. Snapshot checked '+snap['checked_on']+'.']+[x.get('title','Directory')+': '+x['reason'] for x in exceptions]
                local={p['proposal_key']:p for p in proposals}
                for k,p in local.items():
                    if k in global_proposals:global_proposals[k]['parent_record_ids'].append(record['id'])
                    else:global_proposals[k]=dict(session=p,parent_record_ids=[record['id']])
                record['seed_sessions']=list(local.values())
                record['automation']=dict(proposals=len(local),coverage_complete=False,index_capture_complete=snap['index_capture_complete'],mode='offline snapshot extraction',unattended_access='blocked by robots',issues=issues)
                report.append(dict(record_id=record['id'],title=record['title'],proposal_count=len(local),coverage_complete=False,mode='offline snapshot extraction',issues=issues))
                continue
            source=record['current']['event_url'];document,final=fetch(source)
            if 'herts.spydus.co.uk'==urlsplit(final).hostname:
                page=final;visited=set()
                for _ in range(max_pages):
                    if page in visited:raise ValueError('Repeated pagination URL')
                    visited.add(page)
                    body,actual=(document,final) if page==final else fetch(page)
                    items,next_pages=parse_spydus(body,actual,today);proposals.extend(items)
                    if not next_pages:complete=True;break
                    if len(next_pages)!=1:raise ValueError('Ambiguous next-page route')
                    if urlsplit(next_pages[0]).hostname!=urlsplit(actual).hostname:raise ValueError('Foreign pagination route')
                    page=next_pages[0]
                if not complete:issues.append('Further catalogue pages remain; this bounded batch is partial.')
            elif record['title']=='Child & Family Centres - Stay and Play':
                proposals=parse_stay_and_play(document,final);complete=True
                for proposed in proposals:
                    # Preserve reviewed address scaffolding only when the same
                    # centre and its postcode still appear on this source page.
                    previous=next((s for s in record['seed_sessions'] if s['venue']==proposed['venue']),None)
                    if previous and previous.get('postcode') and previous['postcode'] in BeautifulSoup(document,'html.parser').get_text(' ',strip=True):
                        proposed['location']=previous['location'];proposed['postcode']=previous['postcode']
            else:
                soup=BeautifulSoup(document,'html.parser')
                candidates=[public_link(final,a['href']) for a in soup.select('a[href]') if any(w in a.get_text(' ',strip=True).lower() for w in ['website','find a','www.shredderskateschool'])]
                if record['id']=='d439f22f-6a3a-4bb2-ac1e-1bb941d1cbef':
                    target=next((u for u in candidates if urlsplit(u).hostname=='www.gkfit.co.uk'),None)
                    if not target:raise ValueError('No observed GK Fit primary route')
                    home,actual=fetch(target)
                    links=[]
                    for anchor in BeautifulSoup(home,'html.parser').select('a[href]'):
                        if urlsplit(urljoin(actual,anchor['href'])).scheme=='https':links.append(public_link(actual,anchor['href']))
                    pages={}
                    for route in ['/book','/daytime','/netball','/netball/holiday']:
                        link=next((u for u in links if urlsplit(u).hostname=='www.gkfit.co.uk' and urlsplit(u).path==route),None)
                        if not link:raise ValueError('Missing observed timetable route: '+route)
                        pages[route]=fetch(link)[0]
                    proposals,exceptions=parse_gkfit(pages['/book'],pages['/daytime'],pages['/netball'],pages['/netball/holiday'],today)
                    complete=True
                    issues.extend(x.get('title','Programme')+': '+x['reason'] for x in exceptions)
                elif record['title']=='Mini Athletics':
                    target=next((u for u in candidates if urlsplit(u).hostname=='www.miniathletics.com' and urlsplit(u).path.startswith('/mini-athletics-cambridge-and-saffron-walden-summary/')),None)
                    if not target:raise ValueError('No observed primary timetable link')
                    body,actual=fetch(target);proposals,excluded=parse_mini_athletics(body,actual,today);complete=True
                    issues.extend(x['reason']+' — '+x.get('name',x['venue']) for x in excluded)
                else:
                    issues.append('Current page needs an additional supported programme/detail adapter; no session details inferred.')
                    issues.extend('Observed route: '+u for u in list(dict.fromkeys(candidates))[:3])
        except Exception as e:issues.append(str(e))
        local={p['proposal_key']:p for p in proposals}
        for k,p in local.items():
            item=global_proposals.setdefault(k,dict(session=p,parent_record_ids=[]))
            if record['id'] not in item['parent_record_ids']:item['parent_record_ids'].append(record['id'])
        record['seed_sessions']=list(local.values()) or record['seed_sessions']
        record['automation']={'proposals':len(local),'coverage_complete':complete,'issues':issues}
        report.append(dict(record_id=record['id'],title=record['title'],proposal_count=len(local),coverage_complete=complete,issues=issues))
    result=dict(as_of=today.isoformat(),database_writes=0,model_calls=0,network_request_attempts=attempts,records=report,distinct_session_proposals=list(global_proposals.values()),source_checks=checks,robots_hosts_checked=list(robots),notes='Proposals are unapproved. Catalogue pagination budgets and unknown age/address fields remain review tasks. No aggregate listing is withdrawn by this collector.')
    path=ROOT/'artefacts/data/ds10-automated-session-proposals-2026-10-12.json'
    if record_id and path.exists():
        previous=json.loads(path.read_text(encoding='utf8'))
        result['records']=[r for r in previous['records'] if r['record_id']!=record_id]+report
        retained=[]
        for item in previous['distinct_session_proposals']:
            item['parent_record_ids']=[id for id in item['parent_record_ids'] if id!=record_id]
            if item['parent_record_ids']:retained.append(item)
        merged={x['session']['proposal_key']:x for x in retained}
        for key,item in global_proposals.items():
            if key in merged:merged[key]['parent_record_ids']=list(dict.fromkeys(merged[key]['parent_record_ids']+item['parent_record_ids']))
            else:merged[key]=item
        result['distinct_session_proposals']=list(merged.values())
        result['source_checks']=previous['source_checks']+checks
        result['robots_hosts_checked']=list(dict.fromkeys(previous['robots_hosts_checked']+list(robots)))
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'artefacts/data/ds10-action-console-19-2026-10-12.json').write_text(json.dumps(cohort,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'distinct_proposals':len(global_proposals),'records':report,'public_page_requests':len(checks)},ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--as-of',type=dt.date.fromisoformat,default=dt.date.today());parser.add_argument('--max-pages',type=int,default=2);parser.add_argument('--record-id',help='Run one split-programme record; preserve other proposals')
    args=parser.parse_args()
    if not 1<=args.max_pages<=3:parser.error('max-pages must be 1–3')
    run(args.as_of,args.max_pages,args.record_id)
