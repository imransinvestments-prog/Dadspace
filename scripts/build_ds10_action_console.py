"""Build an offline decision console for the owner's selected historical actions."""
import json,html,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artefacts/documentation/ds10-action-console-2026-10-12.html'
COHORT=ROOT/'artefacts/data/ds10-action-console-19-2026-10-12.json'
def select_group(r):
    t=r.get('remaining_task') or ''
    if r['status']=='route-recovery-required' or 'primary operator link now 404' in t:return 'routes'
    if any(x in t for x in ['Replace aggregate','multiple sports','individual group age','Split by venue/class','split sessions','many local coaches']):return 'split'
    if 'Place rather' in t:return 'venue'
    if 'Mobile 1:1' in t:return 'mobile'
def main():
    # A checkout can rebuild the standalone page from its committed snapshot.
    # Full database backups are needed only for the initial cohort preparation.
    if COHORT.exists():
        render(json.loads(COHORT.read_text(encoding='utf8')))
        return
    ledger=json.loads((ROOT/'artefacts/data/ds10-uncertain-191-review-2026-10-12.json').read_text(encoding='utf8'))['ledger']
    snapshot={x['row']['id']:x for x in json.loads((ROOT/'event-backup/uncertain-191-after.json').read_text(encoding='utf8'))}
    evidence={x['url']:x for x in json.loads((ROOT/'event-backup/uncertain-fresh-source-evidence.json').read_text(encoding='utf8'))}
    selected=[]
    for r in ledger:
        group=select_group(r)
        if not group:continue
        current=snapshot[r['id']]['row']
        links=[dict(label='Current detail',url=r['event_url']),dict(label='Source index',url=r['source_url'])]
        links +=[dict(label='Observed programme route',url=u) for u in r['observed_candidate_urls']]
        for a in evidence.get(r['event_url'],{}).get('links',[]):
            if a['url'].startswith('https://') and any(w in a['text'].lower() for w in ['website','find a','www.miltoncountrypark.org/wildplaceactivities','www.shredderskateschool']):
                links.append(dict(label=a['text'],url=a['url']))
        unique={a['url']:a for a in links if a.get('url')}
        selected.append(dict(id=r['id'],title=r['title'],group=group,task=r['remaining_task'],links=list(unique.values()),current={k:current.get(k) for k in ['title','venue_name','location','postcode','age_range','schedule_text','time_text','start_date','end_date','event_url','venue_id']},fingerprint=snapshot[r['id']]['fingerprint'],seed_sessions=[]))
    assert collections.Counter(r['group'] for r in selected)==dict(split=11,routes=6,venue=1,mobile=1)
    stay=next(r for r in selected if r['title']=='Child & Family Centres - Stay and Play')
    centres=[('Fawcett Child and Family Zone','Fawcett Primary School, Alpha Terrace, Trumpington','CB2 9FS','Tuesday 10–11:30am'),('Chesterton Child and Family Centre','Shirley Community Primary School, Nuffield Road, Cambridge','CB4 1TF','Wednesday 1:30–3pm'),('Bewick Bridge Child and Family Zone','Bewick Bridge Community Primary School, Fulbourn Old Drift, Cambridge','CB1 9ND','Thursday 10am–12 noon; term time only'),('North Cambridge Child and Family Centre','Campkin Road, Cambridge','CB4 2LD','Thursday 1:30–3pm'),('The Fields Child and Family Centre','Galfrid Road, Cambridge','CB5 8ND','Friday 10–11:30am')]
    stay['seed_sessions']=[dict(name='Stay and Play — '+v,venue=v,location=loc,postcode=pc,ages='10 months–5 years; older siblings up to 8 in school holidays',schedule=sc,evidence_url=stay['current']['event_url'],booking_url='',dates='',notes='Free; booking required by phone/email. Confirm current session before approval.'+(' Timetable calls this Berwick Bridge; address calls it Bewick Bridge. Confirm venue identity.' if 'Bewick' in v else '')) for v,loc,pc,sc in centres]
    data=dict(version=1,cohort='ds10-selected-19-2026-10-12',owner='Imran Tajuddin',records=selected)
    COHORT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    render(data)
def render(data):
    selected=data['records']
    assert len({r['id'] for r in selected})==19
    assert collections.Counter(r['group'] for r in selected)==dict(split=11,routes=6,venue=1,mobile=1)
    template=(ROOT/'scripts/ds10_action_console.html').read_text(encoding='utf8')
    logic=(ROOT/'scripts/ds10_action_console.js').read_text(encoding='utf8')
    page=template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')).replace('__LOGIC__',logic)
    OUT.write_text(page,encoding='utf8')
    print(json.dumps({'records':len(selected),'groups':dict(collections.Counter(r['group'] for r in selected)),'prefilled_sessions':sum(len(r['seed_sessions']) for r in selected),'output':str(OUT)}))
if __name__=='__main__':main()
