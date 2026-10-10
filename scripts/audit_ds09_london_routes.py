"""Bounded access checks of researched London routes; no model/database writes."""
import concurrent.futures as cf
import json
from pathlib import Path
from audit_ds09_access import audit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'artefacts/data'

def main():
    manifest=json.loads((DATA/'ds09-london-source-routes-2026-10-10.json').read_text(encoding='utf-8'))
    rows=manifest['boroughs']
    assert len(rows)==33 and len({r['borough'] for r in rows})==33
    # Explicitly preserve the two healthy London registry routes.
    urls=sorted({r[k] for r in rows if r['adapter_family']!='existing'
                 for k in ('activities','events','supplement') if r.get(k)})
    result={'ai_calls':0,'database_writes':0,'scope':'New/replacement London routes only; healthy Haringey and Redbridge excluded','routes':[]}
    path=DATA/'ds09-london-route-access-2026-10-10.json'
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(audit,[{'id':u,'name':u,'url':u} for u in urls]):
            result['routes'].append(row)
            path.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(row['url'],row['status'],flush=True)
    assert len(result['routes'])==len(urls)

if __name__=='__main__':main()
