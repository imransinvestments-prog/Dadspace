"""Two normal-worker zero-model source passes. No database access or activation."""
import sys,json,datetime as dt
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import events_worker as worker
from hounslow_programmes import REVIEWED_URLS

worker.base.DRY_RUN=True
worker._venue_client=lambda:None
source={'id':'00000000-0000-0000-0000-000000000001','url':next(iter(REVIEWED_URLS)),
        'name':'Hounslow reviewed programme qualification','source_role':'activity_listing','source_adapter':'hounslow_programme'}
results=[]
for attempt in range(2):
    status,rows,digest,info,stats=worker.process_source(source,lambda *args:(_ for _ in ()).throw(RuntimeError('No model permitted')),dt.date.today())
    results.append({'pass':attempt+1,'status':status,'hash':digest,'kept':len(rows),'info':info,'rows':rows})
    if status!='ok' or len(rows)!=1:
        raise RuntimeError('Normal-worker source qualification failed; no activation or freshness write')
if results[0]['hash']!=results[1]['hash'] or results[0]['rows'][0]['dedupe_key']!=results[1]['rows'][0]['dedupe_key']:
    raise RuntimeError('Repeated source identity/evidence changed; review required')
out=Path('review/hounslow-qualification');out.mkdir(parents=True,exist_ok=True)
(out/'normal-worker.json').write_text(json.dumps({'dry_run':True,'model_calls':0,'database_writes':0,'source_activation':False,'results':results},indent=2),encoding='utf-8')
print(json.dumps({'passes':len(results),'kept_per_pass':[r['kept'] for r in results],'statuses':[r['status'] for r in results],'model_calls':0,'database_writes':0,'activation':False}))
