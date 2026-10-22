#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, os, re, time
from urllib.parse import urlparse, urljoin
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from supabase import create_client

BASE='https://www.nct.org.uk'
SITEMAP=BASE+'/sitemap.xml'
SOURCE_NAME='NCT Local Activities & Meet-ups'
UA='Mozilla/5.0 (compatible; DadspaceNCTBot/1.0)'
DRY_RUN=os.getenv('DRY_RUN','true').lower()=='true'
MAX_BRANCHES=int(os.getenv('LIMIT','0') or 0)
PAGE_LIMIT=10
REVIEWED_BRANCHES=[BASE+'/local-activities-meet-ups/twickenham-hounslow-and-district']
SOURCE_ID='562f3099-3b66-4719-9782-57e818d15491'
TODAY=dt.datetime.now(ZoneInfo('Europe/London')).date()
GENERIC={'baby-first-aid','feeding-support','nct-baby-bundles','nct-nearly-new-sales','nct-newborn-talks','nct-walk-and-talk','parent-and-baby-groups'}
H={'User-Agent':UA,'Accept-Language':'en-GB,en;q=0.9'}

class EventPage(list):
    def __init__(self, rows, next_url):
        super().__init__(rows)
        self.next_url=next_url
        self.has_next=bool(next_url)

def norm(v): return re.sub(r'\s+',' ',(v or '').lower()).strip()
def key(title,date,location): return hashlib.sha1('|'.join([norm(title),str(date),norm(location)]).encode()).hexdigest()
def postcode(text):
    m=re.search(r'\b(?:GIR\s?0AA|[A-PR-UWYZ][A-HK-Y]?\d[A-Z\d]?\s?\d[ABD-HJLNP-UW-Z]{2})\b',text or '',re.I)
    if not m:return None
    s=re.sub(r'\s+','',m.group(0).upper());return s[:-3]+' '+s[-3:]
def explicit_date(detail_url):
    """A month/day card is not evidence of a year. Never roll old dates forward."""
    import worker
    allowed,reason=worker.robots_allows(detail_url)
    if not allowed: raise ValueError(reason)
    html=worker.fetch_html_requests(detail_url)
    soup=BeautifulSoup(html,'html.parser');dates=set()
    def walk(value):
        if isinstance(value,dict):
            if value.get('@type')=='Event' and value.get('url')==detail_url and value.get('startDate'):
                stamp=value['startDate']
                if re.match(r'^\d{4}-\d{2}-\d{2}(?:T|$)',stamp):
                    dates.add(dt.date.fromisoformat(stamp[:10]))
                else:
                    dates.add(dt.datetime.strptime(stamp,'%A %d %B %Y %H-%M-%S UTC').date())
            for child in value.values(): walk(child)
        elif isinstance(value,list):
            for child in value: walk(child)
    for script in soup.select('script[type="application/ld+json"]'):
        walk(json.loads(script.get_text()))
    if len(dates)!=1: raise ValueError('Explicit occurrence year missing or ambiguous')
    return dates.pop()

def discover_branches():
    r=requests.get(SITEMAP,timeout=45,headers=H);r.raise_for_status()
    urls=re.findall(r'<loc>(.*?)</loc>',r.text,re.I)
    prefix=BASE+'/local-activities-meet-ups/'
    found=[]
    for u in urls:
        if not u.startswith(prefix):continue
        rest=u[len(prefix):].strip('/')
        if not rest or '/' in rest or rest in GENERIC:continue
        found.append(u)
    return sorted(set(found))

def page_events(branch_url,page):
    url=branch_url if page==0 else f'{branch_url}?page={page}'
    import worker
    allowed,reason=worker.robots_allows(url)
    if not allowed: raise ValueError(reason)
    r=requests.get(url,timeout=35,headers=H);r.raise_for_status()
    if r.url!=url: raise ValueError('Unreviewed NCT redirect')
    s=BeautifulSoup(r.text,'html.parser');out=[]
    cards=s.select('article.node--type-event.node--view-mode-list-item')
    if len(cards)>4: raise ValueError('NCT detail request budget changed; review required')
    for art in cards:
        event_id=art.get('data-history-node-id') or art.get('about')
        date_box=art.select_one('div.uppercase.text-lg.text-error.font-bold')
        day_box=art.select_one('div.text-3xl.text-text-base')
        title_link=art.select_one('a.line-clamp-2.text-ellipsis.align-middle')
        if not (event_id and date_box and day_box and title_link): raise ValueError('Incomplete NCT event card')
        title=title_link.get_text(' ',strip=True)
        detail=BASE+art.get('about') if (art.get('about') or '').startswith('/') else (art.get('about') or branch_url)
        if not detail.startswith(BASE+'/events/'): raise ValueError('Unreviewed NCT detail URL')
        start=explicit_date(detail)
        if start.strftime('%b').lower()!=date_box.get_text(' ',strip=True)[:3].lower() or start.day!=int(day_box.get_text(' ',strip=True)):
            raise ValueError('NCT card/detail dates disagree')
        info=art.select('div.text-base.font-normal.text-text-base.line-clamp-2.text-ellipsis')
        time_text=info[0].get_text(' ',strip=True) if len(info)>0 else None
        location=info[1].get_text(' ',strip=True) if len(info)>1 else None
        pc=postcode(location)
        venue=(location.split(',')[0].strip() if location and location.lower()!='online' else location)
        category='parent_baby_group';tl=title.lower()
        if 'first aid' in tl:category='first_aid'
        elif 'nearly new' in tl or 'sale' in tl:category='family_market'
        elif 'walk' in tl:category='walks_outdoors'
        elif 'feeding' in tl or 'breastfeed' in tl:category='feeding_support'
        now=dt.datetime.now(dt.timezone.utc).isoformat()
        row={'title':title,'description':f'NCT local activity from {urlparse(branch_url).path.rsplit("/",1)[-1].replace("-"," ").title()}.','start_date':start.isoformat(),'end_date':start.isoformat(),'time_text':time_text,'location':location,'event_url':detail,'source_url':branch_url,'cost_text':None,'age_range':'Pregnant parents, babies and young children','recurrence':None,'family_relevance':5,'confidence':0.99,'extraction_method':'nct_html_adapter','dedupe_key':key(title,start.isoformat(),location),'listing_type':'activity','is_holiday_camp':False,'schedule_text':time_text,'category':category,'venue_name':venue,'venue_address':location,'postcode':pc,'last_seen_at':now,'last_verified_at':now}
        out.append((str(event_id),row))
    if not s.select('article.node--type-event.node--view-mode-list-item') and not s.find(string=re.compile("can't find events that match",re.I)):
        raise ValueError('NCT list completeness unknown')
    links={urljoin(url,a['href']) for a in s.select('a[rel="next"], li.pager__item--next a, a[title="Go to next page"]')}
    if len(links)>1: raise ValueError('Ambiguous NCT pagination')
    next_url=next(iter(links),None)
    if next_url and (urlparse(next_url).scheme!='https' or urlparse(next_url).netloc!=urlparse(url).netloc or urlparse(next_url).path!=urlparse(url).path):
        raise ValueError('Unreviewed NCT pagination route')
    return EventPage(out,next_url)

def collect_branch(branch_url):
    rows=[];seen=set();previous=None;next_url=branch_url
    cutoff=TODAY+dt.timedelta(days=30)
    for page in range(PAGE_LIMIT):
        events=page_events(next_url,0)
        fresh=[(eid,row) for eid,row in events if eid not in seen]
        if events and not fresh: raise ValueError('Repeated NCT pagination; completeness unknown')
        if not events:
            if events.has_next: raise ValueError('Empty NCT page still advertises more results')
            return rows
        dates=[dt.date.fromisoformat(row['start_date']) for eid,row in fresh]
        if dates!=sorted(dates) or (dates and previous and dates[0]<previous):
            raise ValueError('NCT occurrence order is unqualified')
        if dates: previous=dates[-1]
        rows.extend(row for eid,row in fresh if TODAY<=dt.date.fromisoformat(row['start_date'])<=cutoff);seen.update(eid for eid,row in fresh)
        if dates and dates[-1]>cutoff: return rows
        if not events.has_next: return rows
        next_url=events.next_url
        time.sleep(0.15)
    raise ValueError('NCT page budget exhausted; no partial refresh')

def flush(db,batch):
    if not batch:return 0
    unique={row['dedupe_key']:row for row in batch}
    rows=list(unique.values())
    if DRY_RUN:return 0
    # Current candidates are dated occurrences, while the legacy database key
    # coalesces title/place and would retain only the final occurrence. Keep
    # publication blocked until reviewed programme bindings and a writer that
    # preserves the complete accepted occurrence window are in place.
    raise ValueError('NCT programme bindings and occurrence-preserving publication are not qualified')

def run_refresh(db,source,branches,evidence):
    if not branches:
        evidence.finish(stopped_early=True,fatal=True)
        return 1
    failed=False
    for branch in branches:
        selected={'id':branch}
        try:
            rows=collect_branch(branch)
            if not rows: raise ValueError('Zero yield requires source review')
            for row in rows: row['source_id']=source['id']
            unique=list({row['dedupe_key']:row for row in rows}.values())
            saved=flush(db,unique)
            if not DRY_RUN:
                now=dt.datetime.now(dt.timezone.utc).isoformat()
                health=db.table('sources').update({'last_checked_at':now,'last_success_at':now,
                    'fail_count':0,'last_error':None}).eq('id',source['id']).execute()
                if not isinstance(health.data,list) or len(health.data)!=1 or health.data[0].get('id')!=source['id']:
                    raise ValueError('NCT source health write unconfirmed')
            stats={'extracted':len(rows),'kept':len(unique),'duplicates':len(rows)-len(unique),
                'item_coverage':{'scope':'reviewed_branch_30_day_window','complete':True,'url':branch,
                                 'window_start':TODAY.isoformat(),'window_end':(TODAY+dt.timedelta(days=30)).isoformat(),
                                 'renewal':'accepted_rows_only','unseen':'retain_without_refresh'}}
            evidence.source(selected,'ok',stats,unique,
                write_state='dry_run' if DRY_RUN else 'succeeded',
                health_state='dry_run' if DRY_RUN else 'succeeded')
            print(json.dumps({'branch':branch,'accepted':len(unique),'saved':saved,'dry_run':DRY_RUN}))
        except Exception as exc:
            failed=True
            if not DRY_RUN:
                try:
                    db.table('sources').update({'last_checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
                        'last_error':'Dedicated NCT refresh failed: '+type(exc).__name__,
                        'fail_count':(source.get('fail_count') or 0)+1}).eq('id',source['id']).execute()
                except Exception:
                    pass
            evidence.source(selected,'failed_refresh',{},[],write_state='failed' if not DRY_RUN else 'not_attempted',health_state='failed')
            # Evidence contains a safe exception type, not credential-bearing URLs/errors.
            print(json.dumps({'branch':branch,'status':'failed','error_type':type(exc).__name__}))
    evidence.finish(stopped_early=False,fatal=failed)
    return 1 if failed else 0


def main():
    from collection_evidence import CollectionEvidence
    branches=REVIEWED_BRANCHES
    if MAX_BRANCHES<0: raise ValueError('Branch limit cannot be negative')
    if MAX_BRANCHES: branches=branches[:MAX_BRANCHES]
    evidence=CollectionEvidence([{'id':u} for u in branches],dry_run=DRY_RUN,
        path=os.getenv('COLLECTION_EVIDENCE_PATH'))
    try:
        source={'id':SOURCE_ID}
        db=None
        if not DRY_RUN:
            if os.getenv('NCT_REFRESH_ENABLED','false').lower()!='true':
                raise ValueError('NCT refresh activation not approved')
            db=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY'])
            source=(db.table('sources').select('id,active,source_adapter,url,fail_count').eq('id',SOURCE_ID).limit(1).execute().data or [None])[0]
            if not source or not source.get('active'): raise ValueError('NCT source is inactive')
            if source.get('source_adapter')!='nct_dedicated' or source.get('url')!=REVIEWED_BRANCHES[0]:
                raise ValueError('NCT dedicated routing/scope configuration requires review')
        return run_refresh(db,source,branches,evidence)
    except Exception:
        evidence.finish(stopped_early=True,fatal=True)
        raise


if __name__=='__main__': raise SystemExit(main())
