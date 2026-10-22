"""120 read-only public venue samples; response gates cannot pass on errors."""
import datetime as dt
import json,math,time,os
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
CASES={'national-first':'','national-deep':'offset=240','pilot-first':'lat=51.508924&lng=-0.275866','pilot-deep':'lat=51.508924&lng=-0.275866&offset=48','pilot-filter':'lat=51.508924&lng=-0.275866&category=library&free=true','pilot-search':'lat=51.508924&lng=-0.275866&q=library'}
def main():
 origin=os.environ.get('SPRINT11_ORIGIN','https://www.dad-space.co.uk');sha=os.environ['SPRINT11_SHA']
 result={'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'origin':origin,'deployed_sha':sha,'method':'20 sequential requests per case in one requests.Session; first transport-cold, remaining connection-reused. Server/database cache state is unknown. Wall-clock response plus JSON decoding; decoded UTF-8 JSON bytes. No user identity/cookies.','cases':[]}
 session=requests.Session()
 for name,query in CASES.items():
  rows=[];url=origin+'/api/venues'+('?' +query if query else '')
  for index in range(20):
   start=time.perf_counter();row={'sample':index+1}
   try:
    response=session.get(url,timeout=20);body=response.json()
    venues=body.get('venues')
    row.update(status=response.status_code,elapsed_ms=round((time.perf_counter()-start)*1000,2),json_bytes=len(response.content),returned=len(venues) if isinstance(venues,list) else None,total=body.get('total'),valid=response.status_code==200 and isinstance(venues,list) and len(venues)<=24 and isinstance(body.get('total'),int) and isinstance(body.get('hasMore'),bool))
   except (requests.RequestException,ValueError) as exc:row.update(valid=False,error_type=type(exc).__name__)
   rows.append(row)
  valid=all(r['valid'] for r in rows)
  p95=sorted(r['elapsed_ms'] for r in rows)[math.ceil(len(rows)*.95)-1] if valid else None
  maximum=max((r.get('json_bytes',0) for r in rows),default=0)
  item={'case':name,'url':url,'samples':rows,'p95_ms':p95,'maximum_json_bytes':maximum,'passed':valid and p95<2500 and maximum<102400}
  result['cases'].append(item)
  print(json.dumps({k:v for k,v in item.items() if k!='samples'}))
  (ROOT/os.environ.get('SPRINT11_API_OUTPUT','artefacts/data/sprint11-api-performance.json')).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
