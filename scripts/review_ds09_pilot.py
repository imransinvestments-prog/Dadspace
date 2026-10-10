"""Read-only review of linked pilot pages; preserves text for internal QA."""
import json
from pathlib import Path
from audit_ds09_access import audit, get, Page

ROOT=Path(__file__).resolve().parents[1]
pages=[('Hounslow children library services','https://www.hounslow.gov.uk/libraries/library-services-children'),('Kempton calendar','https://kemptonsteam.org/whats-on/2026-calendar-of-events/'),('Kempton sensory Sundays','https://kemptonsteam.org/whats-on/sensory-friendly-sundays/')]
rows=json.loads((ROOT/'artefacts/data/ds09-pilot_rows-2026-10-10.json').read_text(encoding='utf-8'))
pages.extend((r['title'],r['event_url']) for r in rows)
results=[]
for i,(name,url) in enumerate(pages):
    result=audit({'id':str(i),'name':name,'url':url})
    if result['status']=='readable_pending_validation':
        _,_,body,_=get(url);p=Page();p.feed(body)
        result['review_request_budget']=3
        # Store only a short access excerpt. Human-reviewed facts live in DS-09 report.
        result['review_chars']=len(' '.join(p.text))
    results.append(result)
    print(name,result['status'])
(ROOT/'artefacts/data/ds09-pilot-detail-2026-10-10.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
