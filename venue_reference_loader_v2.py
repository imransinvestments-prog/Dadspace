#!/usr/bin/env python3
from __future__ import annotations
import csv, datetime as dt, difflib, io, os, re
import requests
from supabase import create_client

ACTIVE_URL='https://services-eu1.arcgis.com/s9MgJChYyPlPX2Nk/ArcGIS/rest/services/APP_SitePage_View/FeatureServer/0/query'
LIBRARY_URL='https://blog.librarydata.uk/files/basic-dataset-for-libraries-2023-enhanced.csv'
UA='Mozilla/5.0 (compatible; DadspaceVenueBot/2.0)'
DRY_RUN=os.getenv('DRY_RUN','true').lower()=='true'
LIMIT=int(os.getenv('LIMIT','0') or 0)
H={'User-Agent':UA,'Accept':'application/json,text/csv,*/*'}

def norm(v):
    t=(v or '').lower().replace('&',' and ')
    t=re.sub(r'\b(the|a|an|ltd|limited|plc)\b',' ',t)
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',t)).strip()
def pc(v):
    t=re.sub(r'\s+','',(v or '').upper()); return t[:-3]+' '+t[-3:] if len(t)>=5 else t
def first(row,*keys):
    d={str(k).strip().lower():v for k,v in row.items()}
    for k in keys:
        v=d.get(k.lower())
        if v not in (None,''):return v
    return None
def fnum(v):
    try:return float(v)
    except:return None

def load_venues(db):
    rows=[];start=0
    while True:
        part=db.table('venues').select('id,venue_name,postcode,address,town_city,latitude,longitude,website,operator,source_url').range(start,start+999).execute().data or []
        rows.extend(part)
        if len(part)<1000:break
        start+=1000
    bypc={};bysource={}
    for v in rows:
        if pc(v.get('postcode')):bypc.setdefault(pc(v['postcode']),[]).append(v)
        if v.get('source_url'):bysource[v['source_url']]=v
    return bypc,bysource

def choose(c,bypc):
    n=norm(c['venue_name']);best=None
    for v in bypc.get(pc(c.get('postcode')),[]):
        score=difflib.SequenceMatcher(None,n,norm(v.get('venue_name'))).ratio()
        if score==1:return v,'postcode_exact_name',1.0
        if score>=.86 and (best is None or score>best[0]):best=(score,v)
    return (best[1],'postcode_fuzzy_name',best[0]) if best else None

def prov(vid,c,method,conf):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    return {'venue_id':str(vid),'source_name':c['source_name'],'source_record_id':c['source_record_id'],'source_url':c['source_url'],'source_role':'venue_reference','match_method':method,'match_confidence':conf,'source_payload':c['payload'],'last_seen_at':now,'updated_at':now}
def enrich(db,v,c):
    patch={}
    for k in ('address','town_city','postcode','website','operator'):
        if not v.get(k) and c.get(k):patch[k]=c[k]
    for k in ('latitude','longitude'):
        if v.get(k) is None and c.get(k) is not None:patch[k]=c[k]
    if patch and not DRY_RUN:db.table('venues').update(patch).eq('id',v['id']).execute()
def flush_prov(db,rows):
    if not rows or DRY_RUN:return
    unique={(r['source_name'],r['source_record_id']):r for r in rows}
    db.table('venue_sources').upsert(list(unique.values()),on_conflict='source_name,source_record_id').execute()

def active_rows():
    offset=0
    while True:
        params={'where':'recenddate IS NULL','outFields':'siteid,sitename,postcode,address,posttown,website,operatorname,lat,long','returnGeometry':'false','f':'json','resultOffset':offset,'resultRecordCount':2000}
        r=requests.get(ACTIVE_URL,params=params,timeout=60,headers=H);r.raise_for_status();fs=r.json().get('features') or []
        if not fs:break
        for f in fs:
            a=f.get('attributes') or {}
            if a.get('siteid') and a.get('sitename'):
                yield {'source_name':'Sport England Active Places','source_record_id':str(a['siteid']),'source_url':'https://www.activeplacespower.com/','venue_name':a['sitename'],'postcode':pc(a.get('postcode')),'address':a.get('address'),'town_city':a.get('posttown'),'website':a.get('website'),'operator':a.get('operatorname'),'latitude':fnum(a.get('lat')),'longitude':fnum(a.get('long')),'payload':a}
        if len(fs)<2000:break
        offset+=2000

def library_rows():
    r=requests.get(LIBRARY_URL,timeout=60,headers=H);r.raise_for_status()
    for row in csv.DictReader(io.StringIO(r.content.decode('utf-8-sig','replace'))):
        name=first(row,'Library name','Library Name','Name');p=pc(first(row,'Postcode','Post code'))
        if not name:continue
        uprn=str(first(row,'UPRN','uprn','Unique property reference number') or '').strip()
        rid=uprn or f'{norm(str(name))}|{p}'
        yield {'source_name':'Public Library Open Data','source_record_id':rid,'source_url':LIBRARY_URL,'venue_name':str(name),'postcode':p,'address':first(row,'Address','Address 1','Address line 1'),'town_city':first(row,'Town','Local authority','Upper Tier Local Authority'),'website':first(row,'Website','Web address','URL'),'operator':None,'latitude':fnum(first(row,'Latitude')),'longitude':fnum(first(row,'Longitude')),'payload':row}

def run_active(db,bypc):
    seen=matched=ambiguous=0;provs=[]
    for c in active_rows():
        seen+=1
        if LIMIT and seen>LIMIT:break
        m=choose(c,bypc)
        if not m:continue
        v,method,conf=m
        if method=='postcode_fuzzy_name' and conf<.95:
            ambiguous+=1
            if not DRY_RUN:db.table('venues').update({'review_reason':f"Possible Sport England match: {c['venue_name']} ({c.get('postcode')})"[:500]}).eq('id',v['id']).execute()
            continue
        enrich(db,v,c);provs.append(prov(v['id'],c,method,conf));matched+=1
        if len(provs)>=200:flush_prov(db,provs);provs=[]
    flush_prov(db,provs);return {'seen':seen,'matched':matched,'ambiguous':ambiguous}

def run_libraries(db,bypc,bysource):
    seen=matched=hidden=ambiguous=0;provs=[];pending=[]
    def flush_pending():
        nonlocal pending,hidden,provs
        if not pending:return
        unique={row['source_url']:(row,c) for row,c in pending};items=list(unique.values())
        if DRY_RUN:hidden+=len(items);pending=[];return
        inserted=db.table('venues').upsert([x[0] for x in items],on_conflict='source_url').execute().data or []
        ids={x['source_url']:x['id'] for x in inserted if x.get('source_url') and x.get('id')}
        for row,c in items:
            vid=ids.get(row['source_url']) or (bysource.get(row['source_url']) or {}).get('id')
            if vid:provs.append(prov(vid,c,'new_reference_venue',1.0));hidden+=1
        pending=[]
    for c in library_rows():
        seen+=1
        if LIMIT and seen>LIMIT:break
        m=choose(c,bypc)
        if m:
            v,method,conf=m
            if method=='postcode_fuzzy_name' and conf<.95:
                ambiguous+=1
                if not DRY_RUN:db.table('venues').update({'review_reason':f"Possible Public Library match: {c['venue_name']} ({c.get('postcode')})"[:500]}).eq('id',v['id']).execute()
                continue
            enrich(db,v,c);provs.append(prov(v['id'],c,method,conf));matched+=1
        else:
            synthetic=f"reference:{c['source_name']}:{c['source_record_id']}"
            existing=bysource.get(synthetic)
            if existing:provs.append(prov(existing['id'],c,'new_reference_venue',1.0));hidden+=1
            else:pending.append(({'venue_name':c['venue_name'],'category':'library','address':c.get('address'),'town_city':c.get('town_city'),'postcode':c.get('postcode'),'latitude':c.get('latitude'),'longitude':c.get('longitude'),'website':c.get('website'),'source':c['source_name'],'source_url':synthetic,'discovered_source_url':LIBRARY_URL,'discovery_status':'discovered','public_visible':False,'licence':'Open Government Licence v3.0','review_reason':'New public library from reference dataset; review before publishing'},c))
        if len(pending)>=100:flush_pending()
        if len(provs)>=200:flush_prov(db,provs);provs=[]
    flush_pending();flush_prov(db,provs)
    return {'seen':seen,'matched':matched,'hidden_or_existing':hidden,'ambiguous':ambiguous}

def main():
    db=create_client(os.environ['SUPABASE_URL'],os.environ['SUPABASE_KEY']);bypc,bysource=load_venues(db)
    active={x['name'] for x in (db.table('sources').select('name').eq('source_role','venue_reference').eq('active',True).execute().data or [])};out={'dry_run':DRY_RUN}
    if 'Sport England Active Places' in active:out['active_places']=run_active(db,bypc)
    if 'Public Library Open Data' in active:out['libraries']=run_libraries(db,bypc,bysource)
    print(out)
if __name__=='__main__':main()
