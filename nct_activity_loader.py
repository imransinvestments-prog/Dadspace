#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, os, re, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from supabase import create_client

BASE='https://www.nct.org.uk'
SITEMAP=BASE+'/sitemap.xml'
SOURCE_NAME='NCT Local Activities & Meet-ups'
UA='Mozilla/5.0 (compatible; DadspaceNCTBot/1.0)'
DRY_RUN=os.getenv('DRY_RUN','false').lower()=='true'
MAX_BRANCHES=int(os.getenv('LIMIT','0') or 0)
PAGE_LIMIT=50
TODAY=dt.date.today()
GENERIC={'baby-first-aid','feeding-support','nct-baby-bundles','nct-nearly-new-sales','nct-newborn-talks','nct-walk-and-talk','parent-and-baby-groups'}
H={'User-Agent':UA,'Accept-Language':'en-GB,en;q=0.9'}

def norm(v): return re.sub(r'\s+',' ',(v or '').lower()).strip()
def key(title,date,location): return hashlib.sha1('|'.join([norm(title),str(date),norm(location)]).encode()).hexdigest()
def postcode(text):
    m=re.search(r'\b(?:GIR\s?0AA|[A-PR-UWYZ][A-HK-Y]?\d[A-Z\d]?\s?\d[ABD-HJLNP-UW-Z]{2})\b',text or '',re.I)
    if not m:return None
    s=re.sub(r'\s+','',m.group(0).upper());return s[:-3]+' '+s[-3:]
def infer_date(month,day):
    try:m=dt.datetime.strptime(month[:3],'%b').month; d=int(day)
    except:return None
    candidate=dt.date(TODAY.year,m,d)
    if candidate < TODAY-dt.timedelta(days=45): candidate=dt.date(TODAY.year+1,m,d)
    return candidate

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
    r=requests.get(url,timeout=35,headers=H);r.raise_for_status()
    s=BeautifulSoup(r.text,'html.parser');out=[]
    for art in s.select('article.node--type-event.node--view-mode-list-item'):
        event_id=art.get('data-history-node-id') or art.get('about')
        date_box=art.select_one('div.uppercase.text-lg.text-error.font-bold')
        day_box=art.select_one('div.text-3xl.text-text-base')
        title_link=art.select_one('a.line-clamp-2.text-ellipsis.align-middle')
        if not (event_id and date_box and day_box and title_link):continue
        start=infer_date(date_box.get_text(' ',strip=True),day_box.get_text(' ',strip=True))
        if not start or start < TODAY:continue
        title=title_link.get_text(' ',strip=True)
        detail=BASE+art.get('about') if (art.get('about') or '').startswith('/') else (art.get('about') or branch_url)
        info=art.select('div.text-base.font-normal.text-text-base.line-clamp-2.text-ellipsis')
        time_text=info[0].get_text(' ',strip=True) if len(info)>0 else None
        location=info[1].get_text(' ',strip=True) if len(info)>1 else None
        pc=postcode(location)
        venue=(location.split(',')[0].strip() if location and location.lower()!='online' else location)
        category='parent_baby_group'
        tl=title.lower()
        if 'first aid' in tl:category='first_aid'
        elif 'nearly new' in tl or 'sale' in tl:category='family_market'
        elif 'walk' in tl:category='walks_outdoors'
        elif 'feeding' in tl or 'breastfeed' in tl:category='feeding_support'
        row={'title':title,'description':f'NCT local activity from {urlparse(branch_url).path.rsplit("/",1)[-1].replace("-"," ").title()}.','start_date':start.isoformat(),'end_date':start.isoformat(),'time_text':time_text,'location':location,'event_url':detail,'source_url':branch_url,'cost_text':None,'age_range':'Pregnant parents, babies and young children','recurrence':None,'family_relevance':5,'confidence':0.99,'extraction_method':'nct_html_adapter','dedupe_key':key(title,start.isoformat(),location),'listing_type':'activity','is_holiday_camp':False,'schedule_text':time_text,'category':category,'venue_name':venue,'venue_address':location,'postcode':pc,'last_seen_at':dt.datetime.now(dt.timezone.utc).isoformat(),'last_verified_at':dt.datetime.now(dt.timezone.utc).isoformat()}
        out.append((str(event_id),row))
    return out

def collect_branch(branch_url):
    rows=[];seen=set()
    for page in range(PAGE_LIMIT):
        events=page_events(branch_url,page)
        fresh=[(eid,row) for eid,row in events if eid not in seen]
        if not fresh:break
        rows.extend(row for eid,row in fresh); seen.update(eid for eid,row in fresh)
        if len(events)<4:break
        time.sleep(0.15)
    return rows

def main():
    db=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY'])
    source=(db.table('sources').select('id,active').eq('name',SOURCE_NAME).limit(1).execute().data or [None])[0]
    if not source or not source.get('active'):
        print('NCT source inactive; nothing loaded');return
    branches=discover_branches()
    if MAX_BRANCHES:branches=branches[:MAX_BRANCHES]
    total=branches_with_events=0; batch=[]
    for i,b in enumerate(branches,1):
        try: rows=collect_branch(b)
        except Exception as e:
            print(f'FAILED {b}: {type(e).__name__}: {e}');continue
        if rows:branches_with_events+=1
        for row in rows:
            row['source_id']=source['id'];batch.append(row);total+=1
            if len(batch)>=200:
                if not DRY_RUN:db.table('collected_events').upsert(batch,on_conflict='dedupe_key').execute()
                batch=[]
        if i%25==0:print(f'progress {i}/{len(branches)} branches, {total} events')
        time.sleep(0.15)
    if batch and not DRY_RUN:db.table('collected_events').upsert(batch,on_conflict='dedupe_key').execute()
    print({'dry_run':DRY_RUN,'branches':len(branches),'branches_with_events':branches_with_events,'events':total})
if __name__=='__main__':main()
