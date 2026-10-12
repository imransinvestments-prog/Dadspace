"""Apply an offline Rhymetime extraction to proposals, never live listings."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cambridgeshire_rhymetime import parse_snapshots
ID='368a7430-a54b-4c02-9af7-0d4702d740dc'
def main(path):
    snap=json.loads(Path(path).read_text(encoding='utf8'))
    programme=snap['programme']
    parent_id={'rhymetime':ID,'storytime':'bbc6d669-367b-4eb4-9cde-18372c8afe77'}[programme]
    proposals,issues=parse_snapshots(snap,programme)
    cohort_path=ROOT/'artefacts/data/ds10-action-console-19-2026-10-12.json'
    cohort=json.loads(cohort_path.read_text(encoding='utf8'))
    record=next(r for r in cohort['records'] if r['id']==parent_id)
    record['seed_sessions']=proposals
    record['automation']=dict(proposals=len(proposals),coverage_complete=False,index_capture_complete=snap['index_capture_complete'],mode='offline snapshot extraction',unattended_access='blocked by robots',issues=['Unattended crawling disallowed by provider robots; a permitted feed/access route is still required.']+[x.get('title','Directory')+': '+x['reason'] for x in issues])
    label='Current '+programme.title()+' directory'
    record['links']=[x for x in record['links'] if x['label']!=label]+[dict(label=label,url=snap['index_url'])]
    evidence_path=ROOT/f'artefacts/data/ds10-cambridgeshire-{programme}-extraction-2026-10-12.json'
    evidence=dict(programme=record['title'],parent_record_id=parent_id,checked_on=snap['checked_on'],capture_method=snap['capture_method'],observed_details=len(snap['records']),proposals=len(proposals),issues=issues,index_capture_complete=snap['index_capture_complete'],unattended_collection_qualified=False,database_writes=0,model_calls=0,sessions=proposals)
    evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    report_path=ROOT/'artefacts/data/ds10-automated-session-proposals-2026-10-12.json'
    report=json.loads(report_path.read_text(encoding='utf8'))
    old=next(x for x in report['records'] if x['record_id']==parent_id)
    old.update(proposal_count=len(proposals),coverage_complete=False,issues=record['automation']['issues'],mode='offline snapshot extraction')
    retained=[]
    for x in report['distinct_session_proposals']:
        x['parent_record_ids']=[id for id in x['parent_record_ids'] if id!=parent_id]
        if x['parent_record_ids']:retained.append(x)
    by_key={x['session']['proposal_key']:x for x in retained}
    for p in proposals:
        if p['proposal_key'] in by_key:
            by_key[p['proposal_key']]['parent_record_ids'].append(parent_id)
        else:
            entry=dict(session=p,parent_record_ids=[parent_id])
            retained.append(entry);by_key[p['proposal_key']]=entry
    report['distinct_session_proposals']=retained
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    cohort_path.write_text(json.dumps(cohort,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'details_reviewed':len(snap['records']),'session_proposals':len(proposals),'issues':issues,'combined_distinct_proposals':len(retained),'live_writes':0}))
if __name__=='__main__':main(sys.argv[1])
