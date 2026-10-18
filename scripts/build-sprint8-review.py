"""Generate the bounded review table from frozen #182 evidence."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ledger=json.loads((root/'artefacts/data/sprint8-eligibility-ledger.json').read_text(encoding='utf-8'))
by_id={row['id']:row for row in ledger['rows']}
def cell(value):return str(value or 'Unknown').replace('|','/').replace('\n',' ')
lines=['# Sprint 8 — review and release pack', '',
    'Tracker: #196. Delivery scope: #180 (5), #183 (3), #181 (5), #182 (5).',
    'Status: engineering complete locally; hosted/release and owner decisions remain required. No ticket acceptance or sprint closure is inferred.', '',
    '## Concrete release and policy decisions', '',
    'Approve the tested collection evidence and bounded MyLibrary maintenance evidence release. MyLibrary revalidates accepted detail rows on every check, including equal hashes. Unseen/partial/failed/cancelled candidates receive no automatic renewal or withdrawal. Existing 60-day public freshness filtering remains in force; storage is not deleted. Sutton source 813ef5bb-9469-58ef-a9ff-66549a60068d remains inactive; no source activation, paid model run or production schema/data mutation is requested.', '',
    'Accept the diagnostic eligibility ledger and the source-backed identity investigation for their bounded scope. #198 owns separately estimated identity repairs. #136 still owns final human quality/breadth acceptance; #125/#132/#129 stay open in planned Sprint 9 #197.', '',
    '## Deliverables and evidence', '',
    '| Ticket | Concrete result | Verification |', '|---|---|---|',
    '| #180 | Append-only selected-source/run ledger; failure, deferred tail, unknown coverage and bounded public-view readback | Eight isolated evidence/run-loop regressions; no failure-induced source hash/last-success advance |',
    '| #183 | Real SQL identity/trigger replay from recorded Cardiff source rows | Repeat, schedule change, rename, move and distinct-session cases; two reproduced identity gaps retained under #198 |',
    '| #181 | MyLibrary item coverage, checked/included/withheld links and unchanged/partial/failure/cancellation evidence | Four adapter regressions and real PostgreSQL-compatible source-refresh test; no blanket renewal of unseen rows |',
    '| #182 | Frozen 495-row current_activities snapshot and reproducible pilot ledger | Explicit ages, public canonical coordinates and existing same-postcode public venue coordinates; unknowns retained |', '',
    '## Eligibility findings', '',
    f"Snapshot: {ledger['captured_at']}. {ledger['pilot_eligible_count']} stored candidate rows meet evidenced age overlap and the 10km pilot location rule. They span {len(ledger['eligible_categories'])} categories and {len(ledger['eligible_provider_ids'])} recorded providers. These are candidate counts against #123 (10 / 3 / 2), not a passing breadth result: actionability, real-world distinctness, source accuracy and owner quality acceptance remain unverified.", '',
    f"{ledger['unknown_location_count']} opportunities have unresolved location and {ledger['unknown_age_count']} unresolved age; these sets overlap. All {ledger['unique_opportunities']} existing identities remain in the report. A source identity key is the report's deduplication boundary; the #198 session/rename findings limit claims about real-world uniqueness.", '',
    'No external geocoder received snapshot data. Exact published postcodes can use coordinate evidence already held for visible public venues; wider spreads and locations within 250m of the radius boundary stay unknown. City-only, school-year and unbounded age wording remain unknown. This is a conservative evidenced cohort, not a claim that no other eligible opportunities exist.', '',
    f"## Fixed review cohort — {len(ledger['review_ids'])} records", '',
    'Two eligible examples, up to two local/unknown-age examples, two unknown-location examples and two outside-age examples, in frozen ID order, deduplicated. No repeat broad content scoring is requested.', '',
    '| Record / source | Published age | Location evidence | Diagnostic result |', '|---|---|---|---|']
for key in ledger['review_ids']:
    row=by_id[key];loc=row['location_evidence']
    label=cell(row['title'])
    url=row.get('event_url') or ''
    link=f'[{label}]({url})' if url.startswith('https://') else label
    lines.append(f"| {link}<br>{key}<br>{cell(row['source_name'])} | {cell(row['age_range'])} | {cell(row.get('location'))}<br>{cell(loc.get('method'))}: {cell(loc.get('distance_km'))} km | age {row['age_evidence']['state']}; location {loc['state']} |")
lines += ['', '## Reproduce and rollback', '',
    '`python scripts/build-activity-eligibility.py artefacts/data/sprint8-activities-snapshot.json artefacts/data/sprint8-postcodes.json artefacts/data/sprint8-eligibility-ledger.json`', '',
    '`node scripts/replay-activity-identity.mjs artefacts/data/sprint8-identity-replay.json`', '',
    'Revert this release to remove the additional collection/readback artifacts and adapter coverage reporting. No schema, source-state, identity or historical content migration needs reversal. Prior evidence artifacts remain historical evidence. Existing normal collection schedules are unchanged.', '',
    '## Acceptance still required', '',
    'Hosted checks, bounded owner release/policy/diagnostic decisions and applicable production/read-only readback must be linked before closing delivery tickets. Sustained scheduled behaviour remains Sprint 9; no seven-day window or future successful dispatch is invented.']
(root/'docs/sprint-8-review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f"Wrote review pack with {len(ledger['review_ids'])} records")
