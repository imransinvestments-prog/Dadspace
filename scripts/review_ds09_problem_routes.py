"""Read-only follow-up of problem routes. Healthy routes are explicitly excluded.

Access checks are evidence, not publication permission or successful ingestion.
No model calls, database connections, consent automation or challenge bypasses.
"""
import concurrent.futures as cf
import json
from pathlib import Path
from urllib.parse import urlparse
from audit_ds09_access import audit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'artefacts/data'

def healthy(row):
    return (row['active'] and (row['last_worker_yield'] or 0) > 0
            and row['fail_count'] == 0
            and row['access_status'] == 'readable_pending_validation')

def review(row):
    reasons = []
    if not row['active']: reasons.append('inactive/unqualified')
    if not row['last_worker_yield']: reasons.append('zero or unknown latest yield')
    if row['fail_count']: reasons.append('recorded worker failure')
    if row['access_status'] != 'readable_pending_validation': reasons.append(row['access_status'])
    out = {'id':row['id'], 'name':row['name'], 'url':row['url'],
           'review_triggers':reasons, 'prior_decision':row['decision'],
           'prior_reason':row['reason'], 'detail_checks':[]}
    if 'Committee Meetings' in row['focus']:
        out['next_action'] = 'Replace committee-calendar role with borough library/operator/family programme route; do not extract governance meetings.'
        return out
    root = audit(row)
    out['root_check'] = root
    host = urlparse(root.get('final_url',row['url'])).hostname
    candidates = [u for u in root.get('detail_candidates',[]) if urlparse(u).hostname == host and u.rstrip('/') != row['url'].rstrip('/')]
    candidates.sort(key=lambda u: (-sum(k in u.lower() for k in ('family','children','story','rhyme','event/','events/')), len(u)))
    for url in candidates[:2]:
        out['detail_checks'].append(audit({'id':row['id'],'name':row['name']+' detail','url':url}))
    out['next_action'] = ('Qualify detail/series extraction, dated freshness and explicit regular schedules; readable pages are not accepted supply.'
                          if root['status']=='readable_pending_validation'
                          else 'Resolve operator/feed access or obtain organiser export. Retain as unresolved access, not evidence of no activities.')
    return out

def main():
    matrix = json.loads((DATA/'ds09-source-matrix-2026-10-10.json').read_text(encoding='utf-8'))
    skipped = [r for r in matrix if healthy(r)]
    problems = [r for r in matrix if not healthy(r)]
    result = {'healthy_exclusion_rule':'active, positive latest yield, zero failure count, readable baseline access; historical error strings alone do not reopen a recovered source',
              'excluded_healthy_sources':[{'id':r['id'],'name':r['name']} for r in skipped],
              'ai_calls':0,'database_writes':0,'sources':[]}
    path = DATA/'ds09-problem-route-review-2026-10-10.json'
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(review, problems):
            result['sources'].append(row)
            path.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(row['name'], row.get('root_check',{}).get('status','replace governance feed'),flush=True)
    assert len(result['sources']) + len(skipped) == len(matrix)

if __name__=='__main__':main()
