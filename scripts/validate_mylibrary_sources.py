"""Two read-only passes via the normal quality worker, no Gemini/DB writes."""
import datetime as dt
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['DRY_RUN']='true'
import events_worker
import worker
from collection_evidence import CollectionEvidence

SOURCES=[
    ('Ealing libraries','https://libraries.ealing.gov.uk/events'),
    ('Merton libraries','https://libraries.merton.gov.uk/events'),
    ('Sutton library','https://events.sutton.gov.uk/event?id=364833'),
]

def selected_sources(family):
    if family=='all': return SOURCES
    return [(name,url) for name,url in SOURCES
            if ('library_portal' if 'libraries.' in url else 'mylibrary_calendar')==family]


def acceptance_errors(results, expected_sources=None):
    errors=[]
    for name,_ in SOURCES if expected_sources is None else expected_sources:
        passes=[r for r in results if r['name']==name]
        if len(passes)!=2 or any(r['status']!='ok' or not r['rows'] for r in passes):
            errors.append(name+': both passes must accept supply')
            continue
        keys=[sorted(row.get('dedupe_key','') for row in r['rows']) for r in passes]
        if keys[0]!=keys[1] or any(not key for key in keys[0]) or len(set(keys[0]))!=len(keys[0]):
            errors.append(name+': missing, duplicate or unstable item identities')
        if any(r['stats'].get('gemini_logical_calls')!=0 for r in passes):
            errors.append(name+': unexpected model calls')
    return errors

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--family',choices=['all','mylibrary_calendar','library_portal'],default='all')
    args=parser.parse_args()
    selected=selected_sources(args.family)
    worker.DRY_RUN=True
    results=[]
    path=ROOT/'mylibrary-source-review/results.json'
    path.parent.mkdir(exist_ok=True)
    for name,url in selected:
        source=dict(id='preview-'+name,name=name,url=url,
                    source_adapter='library_portal' if 'libraries.' in url else 'mylibrary_calendar',
                    collection_days=7 if name=='Merton libraries' else 30)
        for attempt in (1,2):
            ledger=CollectionEvidence([source],dry_run=True,
                path=path.parent/(name.lower().replace(' ','-')+'-'+str(attempt)+'.jsonl'))
            status,rows,digest,message,stats=events_worker.process_source(source,None,worker.today_uk())
            ledger.source(source,status,stats,rows,write_state='dry_run',health_state='dry_run')
            ledger.finish(stopped_early=False,fatal=False)
            results.append(dict(name=name,url=url,attempt=attempt,status=status,rows=rows,
                                page_hash=digest,message=message,stats=stats))
            print(name,attempt,status,len(rows),message,flush=True)
            path.write_text(json.dumps(dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                family=args.family,database_writes=0,model_calls=0,production_enabled=False,results=results),indent=2),encoding='utf-8')
            if digest: source.update(last_hash=digest,last_success_at=dt.datetime.now(dt.timezone.utc).isoformat())
    errors=acceptance_errors(results,selected)
    if errors: raise SystemExit('\n'.join(errors))

if __name__=='__main__': main()
