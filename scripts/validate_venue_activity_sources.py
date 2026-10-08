"""Two bounded real extraction passes through the normal quality worker.

No database mutations: DRY_RUN is set explicitly, including venue resolution.
Outputs all accepted rows and rejection reasons, API/token usage and repeat keys.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DRY_RUN'] = 'true'
import events_worker
import worker as base

PILOT = {'Kent Libraries','Libraries NI','Cardiff Libraries','Museum Wales',
         'Birmingham Museums','Horniman Museum','Amersham Museum','Royal Museums Greenwich'}


def main():
    base.DRY_RUN = True
    events_worker.install_quality_rules()
    sources = json.loads((ROOT/'artefacts/data/activities-source-candidates.json').read_text())
    extract = base.make_gemini_caller()
    results=[]
    for source in sources:
        if source['name'] not in PILOT:
            continue
        source=dict(source, id='preview-'+source['name'], last_hash=None, last_success_at=None)
        for attempt in (1, 2):
            try:
                status,rows,page_hash,message,stats=base.process_source(source, extract, base.today_uk())
                result=dict(source=source['name'],url=source['url'],attempt=attempt,status=status,
                            rows=rows,page_hash=page_hash,message=message,stats=stats)
            except Exception as exc:
                result=dict(source=source['name'],attempt=attempt,status='failed',error=str(exc))
            results.append(result)
            print(source['name'],attempt,result['status'],len(result.get('rows',[])),flush=True)
            # Persist after each source so a failed run retains its evidence.
            output=ROOT/'venue-source-review/results.json'
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps({'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
                'database_writes':0,'metrics':extract.metrics,'results':results},indent=2),encoding='utf-8')
    if not any(r.get('rows') for r in results):
        raise SystemExit('No accepted pilot supply: inspect source and rejection evidence')


if __name__=='__main__':
    main()
