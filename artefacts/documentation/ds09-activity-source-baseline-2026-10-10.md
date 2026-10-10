# DS-09: activity source matrix and TW4 6AY coverage baseline

Delivery ticket: [#38](https://github.com/imransinvestments-prog/Dadspace/issues/38). Audit date: 10 October 2026, Europe/London. Repository baseline: `8fcc8fc6269994d6c7e1f44b1ad66aa5d556676b`.

## Product model — owner clarification

Apply [Dadspace's discovery model](../../docs/discovery-model.md): venues are independently useful places; Activities represent regular opportunities at places such as museums, libraries and family centres; Events represent infrequent or rare occasions. Events may also be discovered alongside activities. Dates and source categories alone do not establish an Event classification. No linked activities means a discovery/matching gap, not that a venue lacks regular programmes.

## Scope and decisions

Imran selected **TW4 6AY** as the pilot centre and **Imran Tajuddin** as the ongoing content/data reviewer. Engineering owns adapter work; a named technical maintainer remains unassigned. Use a provisional **10 km straight-line radius**, not a travel-time promise. This radius and the age bands still need product agreement under #31. Postcodes.io resolves the centre to latitude 51.466329, longitude -0.387970 ([lookup](https://api.postcodes.io/postcodes/TW46AY)); coordinates identify the pilot centre, not a visitor tracking record.

All 155 configured event/activity routes are covered: 75 activities, 52 councils, 22 heritage/parks, six niche venues; 62 are active. The two `venue_reference` rows are explicitly excluded from event-feed decisions because they enrich venue identities. The audit includes inactive routes, existing directory sources, NCT and the 37 inactive library/museum additions. It does not assume that source categories correctly classify their extracted items.

Each route has an evidence-linked recommendation, content owner, geography, focus, observed item categories/age labels, effective fetch lane, cadence, access/republishing dependency, structural detail/yield counts, duplication limits and maintenance-cost status. The [readable decision table](ds09-source-decisions-2026-10-10.md) and [full matrix](../data/ds09-source-matrix-2026-10-10.json) cover every source ID exactly once.

Decisions: **88 improve, 44 pause, 23 replace**. No route is labelled fully accepted/keep: the available evidence does not support source-specific human quality and access/republishing acceptance. Replace recommendations identify committee-calendar routes already described as outside family scope in the registry. Pause covers inactive discovery-only or superseded routes, NCT's outstanding access policy, inaccessible candidates and explicit robots disallow. Improve covers current routes and promising candidates with detailed validation/repair actions. These are audit recommendations; no source flag or URL was changed.

## Live access evidence

All 155 routes received a bounded standard-library HTTP check from this Windows environment: at most four concurrent tasks, robots first, no retries, 12-second socket timeout, two requested URLs per source and a 2 MB response-read cap. Redirects may cause extra HTTP requests. A robots failure stops this audit's listing request; a robots 404 allows the listing probe. HTTP access uses DadspaceEventsBot/1.0. No browser, model calls, database writes or source activation occurred. A timeout is a socket timeout, not a guaranteed whole-run deadline.

Results: **100 readable pending validation; 35 robots unavailable; 11 HTTP failures; three insufficient-content; three other access failures; three robots disallowed**. Readable includes navigation and generic portals: it is not a suitable-feed verdict. Evidence: [access snapshot](../data/ds09-access-2026-10-10.json). Each route retains timestamp, result, redirect URL where available, elapsed time and short access excerpt. Links are discovery candidates, not approved pages. Failed local probes are not proof of failure on GitHub's browser runner. Robots permission is not republication permission; the latter remains explicitly unconfirmed in the matrix.

The audit complements the existing 8 October inventory: all 4,571 museums and 3,440 libraries were inventoried, with 1,710 distinct museum domains and 151 library town buckets. Only four library records had websites and their operator values were missing. Those complete inventory files remain the coverage backlog; 38 operator seeds do not cover every venue. See [earlier report](activities-feed-repair-2026-10-08.md). Its six-source/two-pass figures are an earlier snapshot: #39 records later final-run results and should take precedence when planning #39 repairs. The matrix marks its copied extraction counts as prior-pass evidence, not latest yield or live repeat ingestion.

## Stored supply and quality baseline

Read-only snapshots contain **679 listings: 453 activities and 226 events**. Stored yield is not current, actionable or public-approved supply. [Source/type counts](../data/ds09-yield-2026-10-10.json) record schedule/location/URL nonblank counts and canonical venue links. A nonblank clock time is not a recurring weekday; dates, cancellations, booking and age accuracy require source review. [Category/age segments](../data/ds09-segments-2026-10-10.json) preserve unknown/free-text labels instead of turning them into invented age coverage.

There are **zero duplicate dedupe-key groups and zero duplicate nonnull identity-key groups** ([snapshot](../data/ds09-duplicates-2026-10-10.json)). This does not establish semantic uniqueness across different keys, providers or aggregators. Domain grouping aids collection maintenance; ClassForKids city rows and Hoop city rows must not count as independent providers. Directory-listed operators need item-level provenance before provider diversity can be accepted.

The latest stored live run totals on 9 October are 57,680 input+output tokens across four activity model calls and 247,485 tokens across 19 civic model calls. Per-source cost cannot be reconstructed: pipeline `details` are null. Money is unmeasured; no price estimate is invented. [Ten stored run summaries](../data/ds09-runs-2026-10-10.json) provide the aggregate evidence. Access elapsed seconds measure this audit only, not production maintenance effort.

## TW4 6AY pilot coverage and age/category gaps

The radius query uses existing canonical venue coordinates and the haversine distance. It is limited to geocoded records in a bounding box, then <=10 km; missing coordinates and unmatched activities are excluded from the linked count. Venue public visibility is reported separately, not treated as validation approval.

| Inventory category | Within 10 km | Public-visible | Linked stored activities |
|---|---:|---:|---:|
| Libraries | 61 | 59 | 0 |
| Museums | 35 | 35 | 0 |
| Children's playgrounds | 489 | 489 | 0 |
| Indoor/soft play | 8 | 8 | 0 |
| Trampolines | 3 | 3 | 0 |
| Zoo/animal park | 1 | 1 | 0 |
| Amusement arcades | 5 | 5 | 0 |

Evidence: [radius aggregate](../data/ds09-pilot-2026-10-10.json). This is a linkage/supply gap, not a claim that no activities exist locally.

A separate text-location search for Hounslow/Heston/Feltham/TW4 finds three stored NCT rows, all without canonical venue IDs. Their detail pages were checked and the date, time and local location match the saved records: Alf King Baby Cafe, 21 December; Lampton Baby Cafe, 23 December; Lampton Park Walk & Talk, 10 December 2026. These are dated occurrences currently labelled `activity` with clock-only schedule text; the NCT-specific loader bypasses the normal recurring schedule gate. Under the owner's clarified model, a dated occurrence can still belong to a regular activity: dates alone do not justify reclassifying it as an event. Verify programme regularity and preserve the occurrence date. The pages describe free sessions but also link to Eventbrite for pricing/tickets; do not invent booking conditions or treat broad infant wording as a verified age interval. This verifies three page/record pairs, not all 124 NCT rows or recurring availability. NCT remains inactive pending the recorded access/republishing decision.

| Provisional segment (not accepted audience scope) | Pilot evidence | Gap / next route |
|---|---|---|
| Babies/toddlers; parent groups | Three local NCT dated occurrences; Hounslow states storytimes exist without branch schedule | Review NCT access policy; obtain branch schedules and exact booking conditions |
| Preschool; libraries | No linked recurring rows | Hounslow branch story/rhyme-time schedules and canonical branch identities |
| Primary-age; museums/arts/outdoors | Kempton offers current family-relevant pages; no linked pilot rows | Calendar/detail/cancellation adapter and item-specific age evidence |
| Secondary-age; sport/performing arts | No verified pilot coverage | Qualify postcode-specific operator routes, not generic national homepages |
| Holiday camps, swimming, sports, arts/crafts | Registry contains discovery leads, not verified postcode/age coverage | Review direct local operator pages; trial only after access/detail qualification |

Zero verified counts above mean this audit has not established acceptance. Unknown ages stay unknown. The 10-activities/three-categories/two-provider target from #39 is not met or signed off by this work; no second/third pilot area is inferred from London/Manchester directory rows.

## Prioritised adapters and dependencies

1. **Hounslow Libraries (#39/#40):** pilot priority. Main hub and children's page are accessible, but the child page only says storytimes take place in most libraries; it provides no branch day/time. Follow linked branch/event pages and capture exact schedule, branch address/postcode, cost and booking. Library identity/operator enrichment is required. Do not activate the root page as accepted supply.
2. **Kempton Steam Museum (#39):** current requests route is readable. Linked calendar and sensory pages provide useful dates, times, address and admission facts. The calendar explicitly cancels 21–22 November and site banner records closure 20 October–20 November. The sensory page lists 6 December, 11:00–15:00, adults £7/under-18s free. Build cancellation/closure precedence and calendar+detail merging; don't infer unrestricted child suitability from free admission. A separate railway requires separate tickets. This is source qualification evidence, not a new extracted/public record.
3. **NCT (#38/#39):** Imran to resolve its documented access/republishing dependency. If accepted, review classification using programme regularity, not dates alone, retain explicit source age evidence and review the existing 124 rows; define refresh cadence (its dedicated workflow is manual/push, not scheduled). Useful records must survive venue-resolution ambiguity.
4. **ClassForKids London and Hoop London (#39):** postcode-level schedules, specific booking URLs and operator identity must replace broad London coverage claims. ClassForKids failed this environment's access probe; test the configured browser runner before deciding to replace. Hoop readable content includes editorial/area material, so accepted yield needs item-level review.
5. **London Transport Museum (#39):** requests returned 403, consistent with recorded repeated worker failures. Find a supported browser/API route; distinguish Acton depot from central museum events. Neither URL presence nor a generic museum label establishes pilot locality.
6. **National backlog:** 23 committee routes require replacement; three robots-disallowed routes require permitted alternatives; all 35 robots-unavailable routes need checked access. Retain inactive flags for unvalidated additions. For the eight #39 trial sources, use the later final-run evidence: Cardiff identity replay is stable; NI repeat access, Kent 403, Greenwich/Horniman venue drift, Museum Wales classification, Birmingham yield and Amersham detail links remain explicit repairs.

## Cadence and operational dependencies

`daily-workers.yml` runs every second London calendar day at 07:00 (anchor 1 October 2026). Activities still require civic success, and civic requires news success; `collect-all.yml` also sequences activities after civic. The activity category uses the browser workflow even when registry `fetch_method` is html/unknown; civic/heritage/niche categories use requests. Candidate `cadence_days` metadata is proposed, not enforced by the worker. Record these dependencies under #32 instead of implying independence or individual cadence exists.

The [bounded production activity run 37925215149](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37925215149) on released commit `d71a037...` is **completed/cancelled**, not pending or successful. It cannot establish live repeat-ingestion acceptance. This audit does not dispatch or modify a production collector.

## Reproduction and verification

The source/yield/segment/pilot/run snapshots are read-only Supabase queries taken on 10 October; they contain no keys or private user records. Source registry has 157 total rows; matrix scope has 155. Database values and web text are evidence, not instructions. No database schema changes are part of this PR.

```sh
python scripts/audit_ds09_access.py --registry artefacts/data/ds09-sources-2026-10-10.json --output artefacts/data/ds09-access-2026-10-10.json
python scripts/review_ds09_pilot.py
python scripts/build_ds09_matrix.py
python -m py_compile scripts/audit_ds09_access.py scripts/review_ds09_pilot.py scripts/build_ds09_matrix.py
```

The matrix builder verifies 155 unique IDs, exact access/registry coverage and 679 stored listings. Generation is offline and does not import the production worker. The pilot check follows six explicit recorded/linked pages, respects robots and makes at most three requested URLs per page (redirects excluded). It retains short access excerpts, not full website text. No production worker behavior changes, source activation, event writes, model spending or blanket historical cleanup occurred.

## Acceptance status

Source inventory, all-source recommendations, named content owner, current access evidence, measured pilot linkage gaps and a prioritised adapter/access backlog are delivered. **Keep #38 open** for Imran's per-source decision/access-policy review and acceptance of the provisional radius/age scope. Republish permissions and source maintenance costs remain explicit unknowns; no source is silently marked validated. #39 owns extraction repairs/activation/repeat ingestion, #40 owns matching/provenance and #32 owns independence/cadence/health. Feed quality review and public launch remain under their existing release gates.
