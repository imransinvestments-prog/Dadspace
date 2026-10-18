# Sprint 8 — review and release pack

Completed 18 October 2026 under the owner's request to finish #196. PR #199 is
merged and production verified; bounded delivery is 18/18. The concrete proposals
below are retained as the pre-release pack. See [sprint-8-closure.md](sprint-8-closure.md)
for final verification, acceptance accounting, remaining quality/observation gates
and the engineering retrospective. No separate owner scoring is invented.

Tracker: #196. Delivery scope: #180 (5), #183 (3), #181 (5), #182 (5).
Status: engineering complete locally; hosted/release and owner decisions remain required. No ticket acceptance or sprint closure is inferred.

## Concrete release and policy decisions

Approve the tested collection evidence and bounded MyLibrary maintenance evidence release. MyLibrary revalidates accepted detail rows on every check, including equal hashes. Unseen/partial/failed/cancelled candidates receive no automatic renewal or withdrawal. Existing 60-day public freshness filtering remains in force; storage is not deleted. Sutton source 813ef5bb-9469-58ef-a9ff-66549a60068d remains inactive; no source activation, paid model run or production schema/data mutation is requested.

Accept the diagnostic eligibility ledger and the source-backed identity investigation for their bounded scope. #198 owns separately estimated identity repairs. #136 still owns final human quality/breadth acceptance; #125/#132/#129 stay open in planned Sprint 9 #197.

## Deliverables and evidence

| Ticket | Concrete result | Verification |
|---|---|---|
| #180 | Append-only selected-source/run ledger; failure, deferred tail, unknown coverage and bounded public-view readback | Eight isolated evidence/run-loop regressions; no failure-induced source hash/last-success advance |
| #183 | Real SQL identity/trigger replay from recorded Cardiff source rows | Repeat, schedule change, rename, move and distinct-session cases; two reproduced identity gaps retained under #198 |
| #181 | MyLibrary item coverage, checked/included/withheld links and unchanged/partial/failure/cancellation evidence | Four adapter regressions and real PostgreSQL-compatible source-refresh test; no blanket renewal of unseen rows |
| #182 | Frozen 495-row current_activities snapshot and reproducible pilot ledger | Explicit ages, public canonical coordinates and existing same-postcode public venue coordinates; unknowns retained |

## Eligibility findings

Snapshot: 2026-10-18T16:50:44.760Z. 20 stored candidate rows meet evidenced age overlap and the 10km pilot location rule. They span 3 categories and 2 recorded providers. These are candidate counts against #123 (10 / 3 / 2), not a passing breadth result: actionability, real-world distinctness, source accuracy and owner quality acceptance remain unverified.

380 opportunities have unresolved location and 281 unresolved age; these sets overlap. All 495 existing identities remain in the report. A source identity key is the report's deduplication boundary; the #198 session/rename findings limit claims about real-world uniqueness.

No external geocoder received snapshot data. Exact published postcodes can use coordinate evidence already held for visible public venues; wider spreads and locations within 250m of the radius boundary stay unknown. City-only, school-year and unbounded age wording remain unknown. This is a conservative evidenced cohort, not a claim that no other eligible opportunities exist.

## Fixed review cohort — 7 records

Two eligible examples, up to two local/unknown-age examples, two unknown-location examples and two outside-age examples, in frozen ID order, deduplicated. No repeat broad content scoring is requested.

| Record / source | Published age | Location evidence | Diagnostic result |
|---|---|---|---|
| [Little Kickers Football Classes - St Johns Wood](https://hoop.co.uk/areas/london/www.littlekickers.co.uk)<br>08fc64a3-8ce0-4dad-8c78-8730ce08ad9e<br>Hoop (London) | 18 months to 8 years | St Johns Wood, London<br>public_canonical_venue: 7.438242 km | age eligible; location local |
| [Little Kickers Football Classes- St Johns Wood (Church of our Lady)](https://hoop.co.uk/little-kickers-watford-harrow-pinner/i2MTUh-little-kickers-football-classes-st-johns-wood-church-of-our-lady/)<br>3b5ff6b2-cee5-4354-87a2-c505763a2fd1<br>Hoop (London) | 18 months - 8 years | Church of our Lady, 54 Lodge Road, NW8 8LA<br>public_canonical_venue: 7.438242 km | age eligible; location local |
| [NCT Brentford Walk & Talk](https://www.nct.org.uk/events/twickenham-hounslow-and-district/nct-brentford-walk-talk-9)<br>bc1ee5d9-77d8-4284-95db-037da0c2eacf<br>NCT Local Activities & Meet-ups | Pregnant parents, babies and young children | Brentford Family Hub East, Brentford, TW8 0BJ<br>existing_public_venues_same_full_postcode: 2.661071 km | age unknown; location local |
| Baby Beeps - Union Church and Community Centre - Crouch End<br>002565f1-4706-4634-8885-94b7b061a6a0<br>Hoop (London) | Sitting to confident walking | Union Church and Community Centre, Crouch End<br>unresolved_postcode_or_location: Unknown km | age eligible; location unknown |
| [Toddler Rhyme Time](https://hoop.co.uk/e/EneZmzg/)<br>0196a4a2-bb76-422d-ac8b-56f686861362<br>Hoop (Greater Manchester) | toddler | Unknown<br>unresolved_postcode_or_location: Unknown km | age eligible; location unknown |
| [Creative Writing Club](https://creative-writing-club.classforkids.io)<br>06f0353a-f066-48c0-b51f-a9e13fba55f1<br>ClassForKids (London) | 10 years to 15 years | Virtual classroom, EC1V 2NX<br>delivery_mode_or_location_requires_review: Unknown km | age outside; location unknown |
| [Nextsteps Football FC - Houghend Astroturf Pitches](https://nextsteps-football-fc-chorlton-boys.classforkids.io?venueName=Houghend Astroturf Pitches)<br>0a11bb89-d55e-4611-8287-3510032641f8<br>ClassForKids (Manchester) | 11 years to 14 years | Manchester<br>public_canonical_venue: 252.098476 km | age outside; location outside |

## Reproduce and rollback

`python scripts/build-activity-eligibility.py artefacts/data/sprint8-activities-snapshot.json artefacts/data/sprint8-postcodes.json artefacts/data/sprint8-eligibility-ledger.json`

`node scripts/replay-activity-identity.mjs artefacts/data/sprint8-identity-replay.json`

Revert this release to remove the additional collection/readback artifacts and adapter coverage reporting. No schema, source-state, identity or historical content migration needs reversal. Prior evidence artifacts remain historical evidence. Existing normal collection schedules are unchanged.

## Acceptance still required

Hosted checks, bounded owner release/policy/diagnostic decisions and applicable production/read-only readback must be linked before closing delivery tickets. Sustained scheduled behaviour remains Sprint 9; no seven-day window or future successful dispatch is invented.
