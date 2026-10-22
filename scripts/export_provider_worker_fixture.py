"""Offline real collector/cleaner payloads for the approved identity gate."""
import datetime as dt
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import events_worker as quality
from library_portal import collect_portal
from provider_session_identity import ADAPTER

SOURCE={'id':'10000000-0000-0000-0000-000000000001','url':'https://libraries.ealing.gov.uk/events','source_adapter':ADAPTER}

def worker_rows(records):
    stream='a:'+json.dumps(['$','component',None,{'isEvents':True,'source':records}])+'\n'
    html='<main>Published programme index</main><script>self.__next_f.push('+json.dumps([1,stream])+')</script>'
    today=dt.date(2026,10,11)
    raw,_,_=collect_portal(SOURCE,today,lambda _:html,lambda _:(True,''),{})
    with patch.object(quality,'_resolve_venue',return_value=None):
        rows=quality.clean_events(raw,SOURCE,SOURCE['url'],ADAPTER,today,{})
    for row in rows:
        row.pop('last_seen_at',None); row.pop('last_verified_at',None)
    return sorted(rows,key=lambda r:r['provider_session_id'])

def fixture():
    records=json.loads(Path('tests/fixtures/library-portal-records.json').read_text(encoding='utf-8'))
    for r in records:
        r['name']='Same published session title'
        r['location_name']='Reviewed test library'
        r['location_id']=63
    return worker_rows(records)

if __name__=='__main__':
    Path(sys.argv[1]).write_text(json.dumps(fixture(),indent=2)+'\n',encoding='utf-8')
