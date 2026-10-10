"""Build review reports from bounded access checks and researched operator routes."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'artefacts/data'
DOC = ROOT / 'artefacts/documentation'
DATE = '2026-10-10'

def read(name):
    return json.loads((DATA / f'ds09-{name}-{DATE}.json').read_text(encoding='utf-8'))

def cell(text):
    return str(text).replace('|', '\\|').replace('\n', ' ')

def main():
    manifest = read('london-source-routes')
    access = read('london-route-access')
    problems = read('problem-route-review')
    matrix = read('source-matrix')
    specific = {
        'Aberdeen Museums': 'Correct operator host to https://sites.aberdeencity.gov.uk/AAGM/whats-aberdeen-art-galleries-and-museums. Prior detail review found Loose Parts Play ages 2–5 and Baby Boogie under-five dates. Consent/host access failure is not absence of programmes; retain outside London pilot.',
        'Amersham Museum': 'Keep useful source and follow event detail/calendar export: https://amershammuseum.org/event/museum-makers-8/ gives 11 October 2026 ages 7–11. Exclude this item from 0–5 pilot, not from national supply. Review recurring programme classification.',
        'Camden Council': 'Repair branch schedule extraction on existing page: standing under-five rhyme/Duplo sessions coexist with expired June events. Do not pause merely because latest worker yield is zero. See London plan.',
        'Hounslow Libraries': 'Replace generic root extraction with rendered https://hounslowconnect.com/events and https://hounslowconnect.com/pages/local-libraries; council legacy schedule redirects there. Browser confirmed dated branch family programmes and 15-page pagination. Qualify under-five detail/standing schedules.',
        'Ealing Council': 'Use https://ealing.events.mylibrary.digital/ rather than council event-root extraction; browser confirmed current occurrence/series/detail and individual ICS export. HTTP robots check is unresolved; qualify permitted collection before enabling.',
        'Tower Hamlets Council': 'Follow https://ideastore.towerhamlets.gov.uk/events then its observed idea.events.mylibrary.digital detail links. Browser confirmed future Kids Lego Club cards. Add Young V&A family programme filtered to E2 9PA; detail confirms current under-one Mini Play series. Do not use book-groups category as family coverage.',
        'Southwark Council': 'Use official babies/toddlers standing-schedule chapters and Southwark Presents calendar, as linked in London plan. Follow branch details and discard expired dated cards.',
        'Lewisham Council': 'Retain unresolved council access; supplement with Horniman https://www.horniman.ac.uk/whats-on/ current October family craft/story/festival dates. One museum is not complete borough coverage.',
        'Horniman Museum': 'Retain and repair audience filters, Load more and detail extraction. Official index shows future October family programmes. Exclude daily venue attractions by default, preserve sold-out status and decide Activity/Event from programme frequency.',
        'V&A': 'Use https://www.vam.ac.uk/whatson/programmes/family and item details. Verified current Young V&A under-one Mini Play series; venue postcode decides borough. Source Special event label does not override recurring Dadspace Activity meaning.',
        'Woodland Trust': 'Correct 404 route to https://www.woodlandtrust.org.uk/visiting-woods/things-to-do/events/. Official page shows future October programmes including family crafts. Qualify item ages, geography and automation before reactivation.',
        'Exmoor National Park': 'Correct 404 route to https://www.exmoor-nationalpark.gov.uk/exmoor-for-everyone/events. Official calendar has current October half-term crafts and family programmes; preserve full-booked status and review conflicting card dates against detail.',
        'Cairngorms National Park': 'Replace broken discovery route with candidate official destination calendar https://www.visitcairngorms.com/whats-on/. Qualify operator provenance, family details, export/access and current dates before accepting supply.',
        'National Trust NI': 'Replace obsolete /visit/northern-ireland/events with property calendars, e.g. https://www.nationaltrust.org.uk/visit/northern-ireland/rowallane-garden/events. Official calendar has current October family/Halloween programmes. Preserve ages, child/adult cost and recurrence.',
        'National Trust for Scotland': 'Root /whats-on is unresolved; use official property event calendars discovered via https://www.nts.org.uk/visit. Brodie Castle /visit/places/brodie-castle/events/p2 is indexed with Nature Nippers but live fetch timed out; current detail and access remain unqualified.',
        'Norfolk Museums': 'Replace /whats-on with official home-linked https://www.museums.norfolk.gov.uk/events. Home confirms cross-museum date/type/audience search; events fetch timed out. Qualification remains open, not a no-activity decision.',
        'London Transport Museum Depot (Acton)': 'Use observed operator booking calendar https://bookings.ltmuseum.co.uk/; search indexes Depot Family Tours, live text fetch empty. Render detail and confirm actual dates/ages and Acton versus Covent Garden venue before accepting W3 supply.',
    }
    for r in problems['sources']:
        if r['name'] in specific:
            r['next_action'] = specific[r['name']]
        elif 'Libraries' in r['name'] and r.get('root_check', {}).get('status') == 'readable_pending_validation':
            r['next_action'] = 'Follow official branch children/family programme and booking links; extract standing rhyme/story schedules separately from dated calendar items. Root text alone is not supply. Validate term dates, ages, adult attendance and cancellations before enabling.'
        elif r['name'] in ('Day Out With The Kids', 'Kiddle', 'Heritage Railway Association', 'Federation of City Farms and Community Gardens', 'Muddy Puddles (Forest School Finder)'):
            r['next_action'] = 'Use as venue/operator discovery only unless an actual family programme detail exists. Follow the individual operator calendar; do not turn places, product pages or association membership into Activities or Events.'
        elif r['name'] in ('Little Kickers', 'Rugbytots', 'Water Babies', 'Stagecoach Performing Arts', 'The Creation Station', 'Gymboree Play & Music UK', 'Camp Beaumont', 'SuperCamps', 'The PGL Adventure'):
            r['next_action'] = 'Follow local class/centre timetable and booking detail. Preserve minimum age, postcode, term dates, session price and trial-versus-course distinction. Generic brand copy cannot establish local activity supply; request permitted export where timetable access fails.'
    assert len(manifest['boroughs']) == 33
    assert len({b['borough'] for b in manifest['boroughs']}) == 33
    healthy = {r['id'] for r in problems['excluded_healthy_sources']}
    reviewed = {r['id'] for r in problems['sources']}
    assert healthy.isdisjoint(reviewed)
    assert healthy | reviewed == {r['id'] for r in matrix}
    routes = {r['url']: r for r in access['routes']}
    london = [
        '# London activities and events collection recommendations', '',
        f'Researched {DATE}. Covers all 32 boroughs and the City of London. This is a route and adapter plan, not evidence of 33 operational feeds. Production source activation is disabled.', '',
        '## Collection approach', '',
        '1. Retain healthy registry sources. Haringey and Redbridge are listed for coverage but were not fetched again.',
        '2. Use council/library standing schedules for regular Activities and actual operator calendars for dated occurrences and rare Events. Follow detail pages, branch locations, series and pagination; a root-page text scrape misses much of the supply.',
        '3. Prefer published structured data and calendar exports when observed. Ealing exposes individual ICS links, for example https://ealing.events.mylibrary.digital/ics?id=319317. This is an observed export link, not a tested aggregate feed. No undocumented API or universal borough RSS feed has been verified.',
        '4. For pages that require rendering, use a permitted browser adapter. Cookie banners, JavaScript and host migrations are access states, not evidence that there are no activities. A browser loading successfully does not establish permission for unattended collection. Respect robots restrictions; use an organiser-provided export or reviewed schedule entry where automated access cannot be qualified.',
        '5. Add independent museum, theatre and family-centre programmes as fallback and breadth. One library or museum programme establishes a collection route, not complete borough coverage. An empty library calendar must not make the borough appear covered.', '',
        '## Acceptance before enabling a route', '',
        '- Confirm operator authority, canonical host, robots/terms or agreed export access and named adapter owner.',
        '- Demonstrate at least three successful scheduled collections across seven days, including pagination/detail extraction, stable identity, date changes and cancellation/expiry handling. This is the proposed operational acceptance threshold; it has not been run during this audit.',
        '- Confirm at least one current family Activity with supported recurrence or published occurrences per borough and a working channel for infrequent Events. A borough need not have an upcoming rare Event at all times.',
        '- Record source URL, source item ID, venue/borough, age evidence, accompanying-adult requirement, cost, availability, eligibility, timezone, last successful collection and last content review. Quarantine conflicting times, locations and ages for Imran Tajuddin to review.',
        '- Preserve explicit occurrence gaps and term-time restrictions. Do not manufacture a weekly run from one dated card. Match venues by address/postcode, not operator name; museums can serve several boroughs.',
        '- Classify by Dadspace meaning: Venues are places; Activities are regular opportunities; Events are rare/infrequent occasions. A source label of Event, a ticket link or a calendar date does not decide the Dadspace type.', '',
        '## Borough routes', '',
        'The pilot remains W3 9LN, ages 0–5 inclusive. London-wide and older-child supply remains separate. Family wording can support suitability, but broad audience tags alone must not imply a specific age range.', '',
        '| Area | Regular-activity route | Dated/occasional programme route | Adapter and automated access | Evidence and outstanding work |',
        '| --- | --- | --- | --- | --- |'
    ]
    for b in manifest['boroughs']:
        statuses = sorted({routes[u]['status'] if u in routes else 'not separately HTTP checked'
                           for u in {b['activities'], b['events']}})
        if b['adapter_family'] == 'existing': statuses = ['healthy; excluded from review']
        evidence = b['evidence'] + ' **Remaining:** ' + b['gap']
        if b.get('supplement'): evidence += ' [Detail/fallback](' + b['supplement'] + ').'
        london.append('| ' + ' | '.join(map(cell, [b['borough'], '[Source]('+b['activities']+')',
            '[Source]('+b['events']+')', b['adapter_family']+'; '+', '.join(statuses), evidence])) + ' |')
    london += ['', '## Delivery order', '',
        'Implement Ealing/MyLibrary series and individual ICS support first for the W3 pilot, then Camden/Bexley/Barnet standing-schedule extraction and Hounslow Connect rendered pagination. Reuse the MyLibrary adapter for Merton, Sutton and Idea Store where access is qualified. Add the Better embedded-timetable adapter for Bromley, Greenwich and Wandsworth. Complete the other council/library adapters and independent operator fallbacks against the borough table.', '',
        'Engineering owns adapters; Imran Tajuddin owns content/data review. The named engineering assignee remains to be assigned. #39 should deliver adapters and staged reliability checks, #40 identity/venue matching, #32 scheduling and #70 the operational review UI. #38 stays open until the outstanding audit decisions and ownership are accepted.', '',
        '## Evidence files and limitations', '',
        '[Machine route manifest](../data/ds09-london-source-routes-2026-10-10.json), [bounded HTTP access checks](../data/ds09-london-route-access-2026-10-10.json), and [existing problem-source review](ds09-problem-source-review-2026-10-10.md). HTTP checks use robots first and bounded root/detail requests. Excerpts may be navigation text; readable status measures access, not family suitability, licensing or reliable ingestion. Browser evidence in the table supplements HTTP evidence and does not override a robots refusal.', '']
    (DOC / f'ds09-london-collection-plan-{DATE}.md').write_text('\n'.join(london), encoding='utf-8')
    counts = Counter(r.get('root_check', {}).get('status', 'replace_governance') for r in problems['sources'])
    report = ['# Existing problem-source review', '',
        f'Reviewed {DATE}: {len(reviewed)} problem sources; {len(healthy)} healthy sources excluded. Every existing source ID appears in exactly one group. No AI calls, database writes, source activation or production ingestion.', '',
        '**Scope:** bounded robots/root/detail access checks and targeted operator research. This is not a claim that all 135 sources have completed manual content qualification or adapter repair. Readable pages remain unqualified until useful items and reliable collection are demonstrated.', '',
        'Healthy means active, positive latest worker yield, zero failure count and readable baseline access. Historical error text alone does not reopen a recovered source. Inactive sources remain worth investigating.', '',
        'Current results: '+', '.join(f'{k}: {v}' for k,v in sorted(counts.items()))+'.', '',
        'Replace the 23 committee/governance calendar roles: they do not establish family programme supply. London replacements are in the [borough collection plan](ds09-london-collection-plan-2026-10-10.md); non-London replacements still require local operator qualification.', '',
        '| Source | Why reviewed | Access and detail checks | Recommendation |', '| --- | --- | --- | --- |']
    for r in problems['sources']:
        checks = [r.get('root_check', {})] + r['detail_checks']
        summary = '; '.join('[check]('+c['url']+'): '+c['status'] for c in checks if c)
        report.append('| '+' | '.join(map(cell,['['+r['name']+']('+r['url']+')',
            ', '.join(r['review_triggers']), summary or 'Governance purpose confirmed from registry; no repeat fetch',
            r['next_action']]))+' |')
    report += ['', '## Sources deliberately left alone', '',
        ', '.join(r['name'] for r in problems['excluded_healthy_sources'])+'.', '',
        '## Audit evidence', '',
        '[Full result including exact source IDs, root responses and detail candidates](../data/ds09-problem-route-review-2026-10-10.json). Each non-governance source was checked at its existing root and at most two same-host candidate detail pages. Candidate selection is heuristic; failure to find a useful detail is unresolved and cannot establish absence of activities. Useful known operator alternatives and the London route map take precedence over the previous blanket pause recommendation.', '']
    (DOC / f'ds09-problem-source-review-{DATE}.md').write_text('\n'.join(report), encoding='utf-8')
    # Keep recommendations separate from raw bounded-access evidence.
    (DATA / f'ds09-problem-source-actions-{DATE}.json').write_text(json.dumps({
        'checked_on':DATE, 'production_enabled':False,
        'sources':[{'id':r['id'], 'name':r['name'], 'next_action':r['next_action']} for r in problems['sources']]
    },indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'healthy_excluded':len(healthy), 'problem_sources':len(reviewed), 'boroughs':33, 'root_results':dict(counts)}))

if __name__ == '__main__': main()
