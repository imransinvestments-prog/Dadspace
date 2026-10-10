"""Reconcile audit recommendations; never activate or mutate source registries."""
import json
from collections import Counter

VENUE_DISCOVERY_ONLY = {'Day Out With The Kids', 'Heritage Railway Association',
                        'Kiddle', 'Muddy Puddles (Forest School Finder)'}
REDUNDANT = {'ClassForKids', 'Hoop'}

def reconcile(matrix, data):
    review = json.loads((data/'ds09-problem-route-review-2026-10-10.json').read_text(encoding='utf-8'))
    actions = json.loads((data/'ds09-problem-source-actions-2026-10-10.json').read_text(encoding='utf-8'))
    healthy = {r['id'] for r in review['excluded_healthy_sources']}
    problems = {r['id']:r for r in review['sources']}
    next_actions = {r['id']:r['next_action'] for r in actions['sources']}
    ids = {r['id'] for r in matrix}
    assert len(ids)==155 and healthy.isdisjoint(problems)
    assert healthy | set(problems) == ids
    assert set(next_actions) == set(problems)
    original = json.loads((data/'ds09-original-decisions-2026-10-10.json').read_text(encoding='utf-8'))
    original = {r['id']:r for r in original}
    assert set(original)==ids
    for row in matrix:
        row['original_decision']=original[row['id']]['decision']
        row['original_reason']=original[row['id']]['reason']
        row['content_review_owner']='Imran Tajuddin'
        row['adapter_owner']='Imran Tajuddin (accountable technical owner; Engineering implements adapters)'
        row['decision_reviewed_on']='2026-10-11'
        row['decision_status']='reconciled recommendation; access/quality acceptance remains explicit'
        row['pilot_scope']['radius_status']='owner-confirmed 2026-10-11'
        row['production_activation']='Unchanged; recommendation is not source activation'
        if row['id'] in healthy:
            row['decision']='keep'
            row['reason']='Healthy by recorded active/positive-yield/zero-failure/readable criteria. Retain existing route; excluded from follow-up fetching and adapter changes. This does not certify semantic quality or republishing rights.'
            row['next_action']='Retain existing operation and normal monitoring.'
            row['follow_up_access_status']='excluded healthy; no repeat fetch'
        else:
            problem=problems[row['id']]
            status=problem.get('root_check',{}).get('status')
            row['follow_up_access_status']=status or 'governance purpose; no repeat fetch'
            row['next_action']=next_actions[row['id']]
            row['evidence'].extend(['ds09-problem-route-review-2026-10-10.json','ds09-problem-source-actions-2026-10-10.json'])
            if 'Committee Meetings' in row['focus']:
                row['decision']='replace'
                row['reason']='Replace governance-calendar role with an evidenced family programme source. Committee meetings are outside scope.'
            elif row['name'] in VENUE_DISCOVERY_ONLY:
                row['decision']='replace'
                row['reason']='Replace this generic route as an activity/event feed; retain its independent venue/operator discovery value. Qualify individual operator programmes instead.'
            elif row['name'] in REDUNDANT:
                row['decision']='pause'
                row['reason']='Generic route is redundant with configured per-city sources. Keep paused to avoid duplicate collection; follow-up readability does not reverse this reason.'
            elif row['name']=='Federation of City Farms and Community Gardens':
                row['decision']='pause'
                row['reason']='Existing public events role is sector training/networking rather than family programmes. Retain as operator discovery, with no automatic activation.'
            elif row['name']=='NCT Local Activities & Meet-ups':
                row['decision']='pause'
                row['reason']='Useful family programmes, but the explicitly unresolved approved data-access/republishing route remains a blocker. Follow dedicated branch/detail adapter requirements before enabling.'
            elif status=='robots_disallowed':
                row['decision']='pause'
                row['reason']='Latest robots evidence disallows collection of this route. Seek a permitted organiser export/API or replacement; do not bypass.'
            else:
                row['decision']='improve'
                row['reason']='Investigate/repair the programme route before acceptance. Inactive, zero yield, inaccessible root or absent stored rows alone do not establish unsuitable supply. '+row['next_action']
        row['evidence']=list(dict.fromkeys(row['evidence']+['ds09-original-decisions-2026-10-10.json']))
    counts=Counter(r['decision'] for r in matrix)
    transitions=Counter((r['original_decision'],r['decision']) for r in matrix)
    report=['# DS-09 matrix reconciliation — 11 October 2026','',
        'All 155 original source IDs are reconciled against the 135-source follow-up and 20 healthy exclusions. The machine matrix and source table are the current recommendations. Original decisions and reasons are preserved separately for traceability; raw access, yield and registry snapshots remain historical evidence.','',
        '**Confirmed scope:** W3 9LN, ages 0–5 inclusive, 10 km radius. **Named accountable owner:** Imran Tajuddin, for content review and technical upkeep. Engineering implements adapters.','',
        '## Current decisions','',
        '| Decision | Sources | Meaning |','| --- | --- | --- |',
        f'| Keep | {counts["keep"]} | Retain healthy operation; no follow-up fetch or adapter changes. |',
        f'| Improve | {counts["improve"]} | Qualify or repair actual programme routes. Inactivity and access failure alone are not suitability verdicts. |',
        f'| Replace | {counts["replace"]} | 23 committee calendars plus four generic venue/operator discovery roles; preserve independent venue-discovery value. |',
        f'| Pause | {counts["pause"]} | Explicit robots, approved-access, redundant-route or sector-training blockers. |','',
        '## Original → reconciled','',
        '| Original | Reconciled | Sources |','| --- | --- | --- |']
    report.extend(f'| {old} | {new} | {n} |' for (old,new),n in sorted(transitions.items()))
    report += ['', '## Remaining pauses','']
    report.extend('- **'+r['name']+'**: '+r['reason'] for r in matrix if r['decision']=='pause')
    report += ['', '## Access and delivery boundaries','',
        'Original HTTP access stays in access_status; newer bounded follow-up access is stored separately in follow_up_access_status. The recommendation, access state and production active flag are independent. All source-specific next actions are carried into the matrix; useful operator alternatives do not erase robots or republishing restrictions.','',
        'Content quality, republishing permission and per-source maintenance cost remain unqualified where evidence is missing. These unknowns are recorded rather than silently accepted. #39 delivers adapters and repeated collection, #40 canonical venue matching, #32 scheduling/health and #70 the upkeep UI. Radius and named-owner questions are resolved. #38 audit acceptance and PR review/merge remain open; this reconciliation does not declare the feeds operational.','',
        '[Reconciled source table](ds09-source-decisions-2026-10-10.md) · [London collection plan](ds09-london-collection-plan-2026-10-10.md) · [Original decisions](../data/ds09-original-decisions-2026-10-10.json)','']
    (data.parent/'documentation/ds09-matrix-reconciliation-2026-10-11.md').write_text('\n'.join(report),encoding='utf-8')
    return matrix
