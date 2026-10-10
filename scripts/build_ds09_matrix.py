"""Build evidence-linked decisions from saved read-only snapshots, offline."""
import collections
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'artefacts/data'
def load(name):return json.loads((DATA/name).read_text(encoding='utf-8'))
def main():
    sources=[s for s in load('ds09-sources-2026-10-10.json') if s['category']!='venue_reference']
    access={x['id']:x for x in load('ds09-access-2026-10-10.json')['sources']}
    yields=load('ds09-yield-2026-10-10.json')
    segments=load('ds09-segments-2026-10-10.json')
    prior={x['url']:x for x in load('activities-source-candidates.json')}
    extraction=load('activities-venue-extraction-2026-10-08.json')['results']
    matrix=[]
    for s in sources:
        a=access[s['id']]; notes=s.get('notes') or ''; focus=s.get('focus') or ''
        ys=[x for x in yields if x['source_id']==s['id']]
        seg=[x for x in segments if x['source_id']==s['id']]
        decision='improve';reason='Validate source-specific detail, quality, repeat yield and access/republishing route before acceptance.'
        if 'Committee Meetings' in focus:
            decision='replace';reason='Registry identifies a committee calendar, outside family activity scope; locate an evidenced library/family listing.'
        elif 'replaced by per-city' in notes or 'sector training' in notes or s['name']=='NCT Local Activities & Meet-ups':
            decision='pause';reason=notes
        elif a['status']=='robots_disallowed':
            decision='pause';reason='Live robots check disallows route; seek permitted API/feed or alternative source. No bypass.'
        elif a['status']!='readable_pending_validation':
            decision='improve' if s['active'] else 'pause';reason='Live access check: '+a['status']+'; '+a.get('error','inspect recorded evidence')
        elif not s['active'] and not ys and not prior.get(s['url']):
            decision='pause';reason='Inactive discovery/operator lead with no stored-yield or extraction evidence; qualify a branch/detail route first. '+notes
        elif not s['active']:
            reason='Inactive candidate; readable HTML alone is not an event feed. '+notes
        elif s.get('last_event_count')==0:
            reason='Active route has latest recorded zero yield; separate empty supply from parser/relevance failure and inspect detail pages.'
        elif s.get('fail_count',0)>0:
            reason='Active route has recorded failures; validate worker lane and runner access before trusting stored yield.'
        lane='browser' if s['category']=='activities' else 'requests'
        if s['name']=='NCT Local Activities & Meet-ups':lane='dedicated nct_html_adapter (manual/push workflow; inactive)'
        local=s['name'] in ('Hounslow Libraries','Kempton Steam Museum','NCT Local Activities & Meet-ups','Hoop (London)','ClassForKids (London)','London Transport Museum Depot (Acton)')
        row={'id':s['id'],'name':s['name'],'url':s['url'],'registry_category':s['category'],'role':s['source_role'],'active':s['active'],'decision':decision,'reason':reason,'content_review_owner':'Imran Tajuddin','adapter_owner':'Engineering (named maintainer not yet assigned)','geography':{'nation':s['nation'],'region':s['region'],'pilot_relevance':'local route to validate' if local else 'not demonstrated for TW4 6AY'},'age_scope':'Not accepted; retain item-level age evidence without inferring from source','focus':focus or 'library/museum family scope; detail evidence required','observed_categories':sorted(set(x['category'] or 'unknown' for x in seg)),'observed_age_labels':sorted(set(x['age_range'] or 'unknown' for x in seg)),'configured_fetch_method':s['fetch_method'],'effective_workflow_lane':lane,'adapter':s['source_adapter'],'cadence':'Every second London calendar day at 07:00; no per-source cadence enforcement' if s['active'] else 'Inactive; proposed 2 days after individual approval','access_status':a['status'],'robots_status':a.get('robots_status'),'robots_allowed':a.get('robots_allowed'),'access_checked_at':a['checked_at'],'republishing_route':'Unconfirmed: Imran to review terms/licensed API or factual listing/link policy; robots is not permission','detail_completeness':'Not accepted; stored nonblank fields are structural counts only','stored_by_type':ys,'last_worker_yield':s['last_event_count'],'last_success_at':s['last_success_at'],'fail_count':s['fail_count'],'last_error':s['last_error'],'duplicate_review':'No duplicate dedupe/identity keys globally; semantic and cross-source duplicates unreviewed','operator_group':urlparse(s['url']).hostname.removeprefix('www.'),'maintenance_cost':'Unmeasured per source; inspect aggregate pipeline tokens and bounded access elapsed seconds','access_elapsed_seconds':a['elapsed_seconds'],'prior_extraction_passes':[{'attempt':x['attempt'],'status':x['status'],'accepted_row_count':len(x.get('rows',[]))} for x in extraction if x.get('url')==s['url']],'evidence':['ds09-access-2026-10-10.json','ds09-yield-2026-10-10.json','ds09-segments-2026-10-10.json','ds09-sources-2026-10-10.json']}
        matrix.append(row)
    assert len(matrix)==155 and len({x['id'] for x in matrix})==155
    assert set(access)=={x['id'] for x in matrix}
    assert sum(x['stored_count'] for x in yields)==679
    (DATA/'ds09-source-matrix-2026-10-10.json').write_text(json.dumps(matrix,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# DS-09 source decisions','', 'Generated from saved 10 October read-only evidence. Decisions are audit recommendations; production active flags are unchanged. See the DS-09 report for acceptance limits.','', '| Source | Registry | Active | Decision | Access | Stored activities/events | Owner |','|---|---|---|---|---|---|---|']
    for x in matrix:
        counts={y['listing_type']:y['stored_count'] for y in x['stored_by_type']}
        lines.append(f"| [{x['name']}]({x['url']}) | {x['registry_category']} | {x['active']} | {x['decision']} | {x['access_status']} | {counts.get('activity',0)}/{counts.get('event',0)} | Imran Tajuddin |")
    (ROOT/'artefacts/documentation/ds09-source-decisions-2026-10-10.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Sources',len(matrix),'decisions',dict(collections.Counter(x['decision'] for x in matrix)))
    print('Access',dict(collections.Counter(x['access_status'] for x in matrix)))
    print('Active',sum(x['active'] for x in matrix))

if __name__=='__main__':main()
