"""Two read-only passes via the normal quality worker, no Gemini/DB writes."""
import datetime as dt
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['DRY_RUN']='true'
import events_worker
import worker

SOURCES=[
    ('Ealing Southall','https://ealing.events.mylibrary.digital/event?id=319317'),
    ('Ealing Northolt','https://ealing.events.mylibrary.digital/event?id=264081'),
    ('Merton storytelling','https://merton.events.mylibrary.digital/event?id=378391'),
    ('Sutton library','https://events.sutton.gov.uk/event?id=364833'),
]

def main():
    worker.DRY_RUN=True
    results=[]
    path=ROOT/'mylibrary-source-review/results.json'
    path.parent.mkdir(exist_ok=True)
    for name,url in SOURCES:
        source=dict(id='preview-'+name,name=name,url=url,source_adapter='mylibrary_calendar')
        for attempt in (1,2):
            status,rows,digest,message,stats=events_worker.process_source(source,None,worker.today_uk())
            results.append(dict(name=name,url=url,attempt=attempt,status=status,rows=rows,
                                page_hash=digest,message=message,stats=stats))
            print(name,attempt,status,len(rows),message,flush=True)
            path.write_text(json.dumps(dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                database_writes=0,model_calls=0,production_enabled=False,results=results),indent=2),encoding='utf-8')
            if digest: source.update(last_hash=digest,last_success_at=dt.datetime.now(dt.timezone.utc).isoformat())
    if not any(r['rows'] for r in results): raise SystemExit('No accepted supply; inspect access/detail evidence')

if __name__=='__main__': main()
