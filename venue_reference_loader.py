#!/usr/bin/env python3
from __future__ import annotations
import csv, difflib, io, json, os, re, datetime as dt
import requests
from supabase import create_client

DRY_RUN=os.getenv('DRY_RUN','true').lower()=='true'
LIMIT=int(os.getenv('LIMIT','0') or 0)
UA='Mozilla/5.0 (compatible; DadspaceVenueBot/1.0)'
ACTIVE_URL='https://services-eu1.arcgis.com/s9MgJChYyPlPX2Nk/ArcGIS/rest/services/APP_SitePage_View/FeatureServer/0/query'
LIBRARY_URL='https://blog.librarydata.uk/files/basic-dataset-for-libraries-2023-enhanced.csv'

def norm(v):
    t=(v or '').lower().replace('&',' and ')
    t=re.sub(r'\b(the|a|an|ltd|limited|plc)\b',' ',t)
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',t)).strip()

def pc(v):
    t=re.sub(r'\s+','',(v or '').upper())
    return t[:-3]+' '+t[-3:] if len(t)>=5 else t

def first(row,*keys):
    d={str(k).strip().lower():v for k,v in row.items()}
    for k in keys:
        v=d.get(k.lower())
        if v not in (None,''): return v
    return None

def fnum(v):
    try:return float(v)
    except:return None

def db():
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def load_existing(client):
    out=[]; start=0
    while True:
        rows=client.table('venues').select('id,venue_name,postcode,address,town_city,latitude,longitude,website,operator,category,public_visible,source_url').range(start,start+999).execute().data or []
        out.extend(rows)
        if len(rows)<1000: break
        start+=1000
    bypc={}
    for v in out:
        p=pc(v.get('postcode'))
        if p: bypc.setdefault(p,[]).append(v)
    return bypc

def match(c,bypc):
    candidates=bypc.get(pc(c.get('postcode')),[])
    n=norm(c.get('venue_name'))
    best=None
    for v in candidates:
        s=difflib.SequenceMatcher(None,n,norm(v.get('venue_name'))).ratio()
        if s==1: return v,'postcode_exact_name',1.0
        if s>=0.86 and (best is None or s>best[0]): best=(s,v)
    if best: return best[1],'postcode_fuzzy_name',best[0]
    return None

def provenance(client,venue_id,c,method,conf):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    row={'venue_id':venue_id,'source_name':c['source_name'],'source_record_id':str(c['source_record_id']),'source_url':c['source_url'],'source_role':'venue_reference','match_method':method,'match_confidence':conf,'source_payload':c.get('payload') or {},'last_seen_at':now,'updated_at':now}
    if not DRY_RUN: client.table('venue_sources').upsert(row,on_conflict='source_name,source_record_id').execute()

def enrich(client,v,c):
    patch={}
    for field in ('address','town_city','postcode','website','operator'):
        if not v.get(field) and c.get(field): patch[field]=c[field]
    for field in ('latitude','longitude'):
        if v.get(field) is None and c.get(field) is not None: patch[field]=c[field]
    if patch and not DRY_RUN: client.table('venues').update(patch).eq('id',v['id']).execute()

def create_hidden_library(client,c):
    synthetic=f"reference:{c['source_name']}:{c['source_record_id']}"
    existing=client.table('venues').select('id').eq('source_url',synthetic).limit(1).execute().data or []
    if existing:
        return str(existing[0]['id'])
    row={'venue_name':c['venue_name'],'category':'library','address':c.get('address'),'town_city':c.get('town_city'),'postcode':c.get('postcode'),'latitude':c.get('latitude'),'longitude':c.get('longitude'),'website':c.get('website'),'source':c['source_name'],'source_url':synthetic,'discovered_source_url':c['source_url'],'discovery_status':'discovered','public_visible':False,'licence':'Open Government Licence v3.0','review_reason':'New public library from reference dataset; review before publishing'}
    if DRY_RUN:return None
    try:
        data=client.table('venues').insert(row).execute().data or []
        return str(data[0]['id']) if data else None
    except Exception:
        existing=client.table('venues').select('id').eq('source_url',synthetic).limit(1).execute().data or []
        if existing:return str(existing[0]['id'])
        raise

def active_candidates():
    offset=0
    while True:
        params={'where':'recenddate IS NULL','outFields':'siteid,sitename,postcode,address,posttown,website,operatorname,lat,long,reclastchkddate,swimmingpool,sportshall,healthfitness,icerink,cycling,outdoortennis,grasspitches,agp,golf','returnGeometry':'false','f':'json','resultOffset':offset,'resultRecordCount':2000}
        r=requests.get(ACTIVE_URL,params=params,timeout=60,headers={'User-Agent':UA}); r.raise_for_status()
        feats=(r.json().get('features') or [])
        if not feats: break
        for f in feats:
            a=f.get('attributes') or {}
            yield {'source_name':'Sport England Active Places','source_record_id':a.get('siteid'),'source_url':'https://www.activeplacespower.com/','venue_name':a.get('sitename'),'postcode':pc(a.get('postcode')),'address':a.get('address'),'town_city':a.get('posttown'),'website':a.get('website'),'operator':a.get('operatorname'),'latitude':fnum(a.get('lat')),'longitude':fnum(a.get('long')),'payload':a}
        if len(feats)<2000: break
        offset+=2000

def library_candidates():
    r=requests.get(LIBRARY_URL,timeout=60,headers={'User-Agent':UA}); r.raise_for_status()
    text=r.content.decode('utf-8-sig','replace')
    for row in csv.DictReader(io.StringIO(text)):
        name=first(row,'Library name','Library Name','Name')
        postcode=pc(first(row,'Postcode','Post code'))
        if not name: continue
        rid=first(row,'UPRN','uprn','Unique property reference number') or f'{norm(str(name))}|{postcode}'
        yield {'source_name':'Public Library Open Data','source_record_id':rid,'source_url':LIBRARY_URL,'venue_name':str(name),'postcode':postcode,'address':first(row,'Address','Address 1','Address line 1'),'town_city':first(row,'Town','Local authority','Upper Tier Local Authority'),'website':first(row,'Website','Web address','URL'),'latitude':fnum(first(row,'Latitude')),'longitude':fnum(first(row,'Longitude')),'payload':row}

def run_source(client,bypc,rows,allow_create):
    seen=matched=created=ambiguous=0
    for c in rows:
        if not c.get('venue_name') or not c.get('source_record_id'): continue
        seen+=1
        if LIMIT and seen>LIMIT: break
        m=match(c,bypc)
        if m:
            v,method,conf=m
            if method=='postcode_fuzzy_name' and conf<0.95:
                ambiguous+=1
                if not DRY_RUN: client.table('venues').update({'review_reason':f"Possible {c['source_name']} match: {c['venue_name']} ({c.get('postcode') or 'no postcode'})"[:500]}).eq('id',v['id']).execute()
                continue
            enrich(client,v,c); provenance(client,str(v['id']),c,method,conf); matched+=1
        elif allow_create:
            vid=create_hidden_library(client,c)
            if vid:
                provenance(client,vid,c,'new_reference_venue',1.0)
                created+=1
    return {'seen':seen,'matched':matched,'created_or_existing_hidden':created,'ambiguous':ambiguous}

def main():
    client=db(); bypc=load_existing(client)
    active_sources={r['name'] for r in (client.table('sources').select('name').eq('source_role','venue_reference').eq('active',True).execute().data or [])}
    result={'dry_run':DRY_RUN}
    if 'Sport England Active Places' in active_sources: result['active_places']=run_source(client,bypc,active_candidates(),False)
    if 'Public Library Open Data' in active_sources: result['libraries']=run_source(client,bypc,library_candidates(),True)
    print(json.dumps(result))
if __name__=='__main__': main()
