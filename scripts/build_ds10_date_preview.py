"""Build a non-writing date backfill preview from the audited public snapshots."""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlparse
from activity_dates import HOSTS,published_date_fields

ROOT=Path(__file__).resolve().parents[1]

def main():
    sample=json.loads((ROOT/'artefacts/data/ds10-human-review-2026-10-11.json').read_text(encoding='utf-8'))
    preview=[]
    for row in sample['rows']:
        url=row.get('event_url')
        result=dict(id=row['id'],title=row['title'],url=url,last_verified_at=row.get('last_verified_at'),previous={k:row.get(k) for k in ['start_date','end_date','schedule_text','time_text']})
        if not url:result.update(status='missing_detail_link')
        elif urlparse(url).hostname not in HOSTS:result.update(status='operator_route_requires_review')
        else:
            try:
                html=(ROOT/'date-source-review'/(hashlib.sha256(url.encode()).hexdigest()+'.html')).read_text(encoding='utf-8')
                result.update(status='date_fields_recovered',proposed=published_date_fields(html,url,row['title']))
            except Exception as exc:result.update(status='requires_review',reason=str(exc))
        preview.append(result)
    output=dict(prepared_at=dt.datetime.now(dt.timezone.utc).isoformat(),database_writes=0,note='Preview only: frozen record identities and fresh public snapshots. Re-fetch and check current record/identity before approved backfill. Not human quality acceptance or activation.',rows=preview)
    (ROOT/'artefacts/data/ds10-date-backfill-preview-2026-10-12.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    from collections import Counter
    print(Counter(r['status'] for r in preview))

if __name__=='__main__':main()
