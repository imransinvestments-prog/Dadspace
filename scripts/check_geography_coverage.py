"""Bounded read-only feature observations through existing public app APIs.

No credentials, DB connections, models, source activation, challenge handling or retries.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode, urlsplit

import requests

ROOT=Path(__file__).resolve().parents[1]
FEATURES=('location','venues','activities','events')


def assess(feature, status, body):
    if status != 200 or not isinstance(body,dict) or body.get('loadFailed') or body.get('isSample'):
        return dict(status='unavailable', count=None, completeness='unknown')
    if feature=='location':
        rows=body.get('results')
        if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict) or not all(isinstance(rows[0].get(k),(int,float)) for k in ('lat','lng')):
            return dict(status='failed',count=None,completeness='unknown')
        return dict(status='passed',count=1,completeness='lookup_only')
    rows=body.get(feature)
    if not isinstance(rows,list) or any(not isinstance(row,dict) or not isinstance(row.get('id'),str) for row in rows):
        return dict(status='unavailable',count=None,completeness='unknown')
    if len({row['id'] for row in rows}) != len(rows):
        return dict(status='failed',count=None,completeness='duplicate_items')
    total=body.get('total')
    if total is not None and (type(total)!=int or total<len(rows)):
        return dict(status='unavailable',count=None,completeness='invalid_total')
    partial=body.get('hasMore') is True or isinstance(total,int) and total>len(rows)
    # Events has no total/completeness contract. Retain visible-row count, not an inventory claim.
    complete=not partial and isinstance(total,int) and total==len(rows) and body.get('hasMore') is False
    return dict(status='observed_nonempty' if rows else 'observed_empty',count=len(rows),
                reported_total=total,completeness='first_page' if partial else 'endpoint_result' if complete else 'not_established')


def read(base, path):
    url=base+path
    try:
        response=requests.get(url,timeout=(5,35),allow_redirects=False,
                              headers={'User-Agent':'DadspaceCoverageCheck/1.0','Accept':'application/json'})
        if len(response.content)>2_000_000: return 0,None,'response_budget'
        return response.status_code,response.json() if response.status_code==200 else None,None
    except (requests.RequestException,ValueError) as error:
        return 0,None,type(error).__name__


def observe(case,base):
    if case['state']=='blocked_licence':
        return [dict(case_id=case['id'],feature=feature,status='blocked_licence',count=None,
                     completeness='not_tested',reason=case['reason']) for feature in FEATURES]
    # Matches existing parsePoint precision; the centroid is not an address or travel-time measure.
    lat=int(case['latitude']*100+.5)/100
    lng=int(case['longitude']*100+.5)/100 if case['longitude']>=0 else __import__('math').floor(case['longitude']*100+.5)/100
    query=urlencode(dict(lat=lat,lng=lng,radiusKm=case['radius_km'],scope='local'))
    observations=[]
    for feature in FEATURES:
        path='/api/location?'+urlencode({'q':case['postcode']}) if feature=='location' else '/api/'+feature+'?'+query
        status,body,error=read(base,path)
        item=dict(case_id=case['id'],feature=feature,http_status=status or None,request_path=path,
                  observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),centre=dict(lat=lat,lng=lng),
                  radius_km=case['radius_km'],eligibility='Existing public selector; age 0–5 suitability and source freshness not independently reviewed',
                  **assess(feature,status,body))
        if error: item['error_type']=error
        if feature=='location' and item['status']=='passed':
            point=body['results'][0]
            if abs(point['lat']-lat)>.011 or abs(point['lng']-lng)>.011:
                item.update(status='failed',reason='Location differs from reference representative point')
        observations.append(item)
        print(case['id'],feature,item['status'],item.get('count'),flush=True)
    return observations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--limit',type=int,default=30)
    parser.add_argument('--output',type=Path,default=ROOT/'review/geography-baseline.json')
    args=parser.parse_args()
    origin=urlsplit(args.base_url)
    if origin.username or origin.password or origin.query or origin.fragment or origin.path not in ('','/') or not (origin.scheme=='https' or origin.scheme=='http' and origin.hostname in ('localhost','127.0.0.1')):
        raise SystemExit('Use an HTTPS origin or local development origin')
    if not 1<=args.limit<=30: raise SystemExit('Limit must be 1–30')
    pack_bytes=(ROOT/'geography/test-pack.json').read_bytes()
    pack=json.loads(pack_bytes)
    base=args.base_url.rstrip('/')
    selected=pack['cases'][:args.limit]
    with ThreadPoolExecutor(max_workers=2) as executor:
        groups=list(executor.map(lambda case:observe(case,base),selected))
    observations=[row for group in groups for row in group]
    for case in pack['cases'][args.limit:]:
        observations.extend(dict(case_id=case['id'],feature=feature,status='untested',count=None,completeness='not_tested') for feature in FEATURES)
    global_features=[]
    for feature,path in [('deals','/api/home/deals'),('originals','/originals'),('news','/news')]:
        status,body,error=read(base,path) if feature=='deals' else (None,None,None)
        global_features.append(dict(feature=feature,status='observed_nonempty' if isinstance(body,list) and body else 'observed_empty' if body==[] else 'unavailable' if feature=='deals' else 'manual_review',
                                    http_status=status,count=len(body) if isinstance(body,list) else None,
                                    scope='National selector; not credited as council-specific coverage',
                                    completeness='homepage_sample' if feature=='deals' else 'not_tested',request_path=path))
    report=dict(version=1,observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),base_url=base,
        environment='local' if origin.hostname in ('localhost','127.0.0.1') else 'specified remote origin',
        test_pack_sha256=hashlib.sha256(json.dumps(pack,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
        reference_release=json.loads((ROOT/'geography/reference.json').read_text(encoding='utf-8'))['release_id'],
        database_writes=0,model_calls=0,source_changes=0,observations=observations,national_features=global_features,
        limitations=['Point samples are not council inventories or national coverage certification.',
                    'Age, actionability, freshness and source completeness require content review.',
                    'News locality and Originals content remain manual browser checks; no inferred pass.',
                    'A current API success is not historical or scheduled observation acceptance.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Report:',args.output)


if __name__=='__main__': main()
