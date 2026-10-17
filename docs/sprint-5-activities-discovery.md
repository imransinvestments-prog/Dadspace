# Activities reliability discovery — #176

Owner accepted this discovery on 17 October 2026. #176 is closed. Refined residual backlog: #180 (5), #181 (5, bounded source family), #182 (5, eligibility reporting, not canonical matching), #183 (3, programme identity regressions, not historical repair). Existing #40/#135/#146 scopes are explicitly excluded from those stories. No next sprint is committed.

Evidence captured 17 October 2026. Discovery only; no source activation, paid extraction, cleanup or schema change has been applied.

## Current baseline

The captured public view contains 488 Activities. 401 have no canonical venue ID; 148 have no recorded age range; 101 have a past end date; 198 were last seen more than seven days ago. These overlapping signals are not a count of invalid records. A regular programme can outlive one dated occurrence; a missing venue relationship does not remove its independent value.

The frozen diagnostic sample contains 100 rows across 23 recorded sources and 16 category labels (including unknown). Sixteen have a linked venue within 10km of W3 9LN; 70 have unknown distance in this query. This is **not** evidence that only 16 pilot activities exist: unmatched postcodes/locations can still be locatable by the public geocoder. It is also not a valid claim of 100 geographically and age-qualified pilot activities. Establish that cohort before #136 acceptance; report any supply shortfall instead of filling the denominator with national rows.

The source snapshot has 158 registered rows, 64 active; 20 active sources have recorded failures and 23 report zero last-event yield. Those are cross-discovery sources, not 20 proven Activities outages. Source category is not the listing classifier. See the captured source URLs/roles/adapters and individual sample rows.

## Trace and confirmed gaps

1. `worker.py` selects sources and owns fetching, robots checks, retry/paid-call budgets and source health. `events_worker.py` adds classification, programme validation, venue matching and deterministic routes; ClassForKids, library portals and MyLibrary have dedicated adapters. Source coverage and accessible detail routes remain incomplete (#120/#104/#133/#134).
2. `_activity_row` requires family evidence, confidence, a usable location/link and an evidenced recurring schedule or dates. Historical records predate parts of this contract. A nonempty schedule is not proof the current operator still offers it. Do not regenerate facts from a title.
3. Identity is already represented by `dedupe_key`, `identity_key`, `content_hash` and the stable-identity trigger. Reuse these before proposing another identity system. Test moved venues, renamed programmes and distinct sessions; migration need is an investigation outcome, not assumed.
4. Accepted changed-page rows refresh individually. The existing `refresh_activity_last_seen_from_source_check` trigger can refresh all Activities for a source on an unchanged successful hash. A root-directory hash alone is not item-level cancellation evidence; specialist adapters already avoid this shortcut where necessary. Audit other adapters for actual coverage before changing renewal semantics.
5. The live `current_activities` definition filters withdrawal, type and last-seen within 60 days; it does not exclude past `end_date`. That confirmed mechanism explains why past-end rows can remain visible. Whether each programme should stay needs occurrence/recurrence evidence, not a blanket date deletion.
6. `lib/activities.ts` reads that view. Nearby discovery can use canonical venue coordinates or postcode/location geocoding; unknown distances must stay explicit. A public listing is not necessarily pilot-age eligible. Existing #91/#93 schedule and card behaviour is retained.

## Bounded failure cohort

The frozen diagnostic subset contains **eight distinct records**: take the first three distinct sources per overlapping signal (past end, unknown age, unmatched venue, last-seen older than seven days), deduplicate IDs and cap at 12. Exact IDs and URLs are in `artefacts/data/sprint5-activity-failure-cohort.json`. This is engineering evidence, not another owner scoring task.

Source-page retrieval on 17 October used web-indexed pages; crawl dates range from days to a month old, so it is not a fresh HTTP or normal-run validation:

- [Woodstock Rhymetime](https://www.oxfordshire.gov.uk/events/libraries-oxfordshire-museum/woodstock-rhymetime): indexed official page explicitly identifies under-fives, a library address and dated sessions. The captured row's age field is missing and its dates differ from the indexed page: evidence of an extraction/freshness question, not authority to overwrite it from an older crawl.
- [Deddington Lego Club](https://www.oxfordshire.gov.uk/events/libraries/deddington-lego-club): official indexed detail states ages four-plus, named venue and a dated session list. The captured age is missing; inspect extraction and source currency rather than inferring that an age restriction never existed.
- [Art & Design Club](https://www.southwark.gov.uk/southwark-presents/artdesign-club-hotel-elephant): council-hosted public contribution describes ages 13–16; its automatically expanded date list conflicts with older term dates in the body. It is not pilot supply, and blindly trusting calendar expansion would misrepresent evidence. Do not implement the separately deferred #101 word exclusion under this discovery.
- [Hoop directory](https://hoop.co.uk/areas/london/): indexed page has general early-years football content, but that does not validate the exact Harrow programme whose stored detail URL is missing.
- Tiny Dancers detail, Salford MAPAS detail, Hillingdon directory detail and the KNT booking route were unavailable through the research tool. Cache misses/tool errors do not prove HTTP status, inactivity or source unsuitability. Supported rendered/permission checks remain work under the source-qualification slices; no bypass was attempted.

## Proposed additional engineering slices

These are provisional refinement estimates, not extra Sprint 5 commitments. The deduplicated source-check cohort contains eight records; do not estimate a full source estate from this small cohort.

| Slice | Boundary and evidence | Provisional size | Dependencies / owner gate |
| --- | --- | ---: | --- |
| Per-source run evidence | Persist accepted/rejected/unchanged/deferred counts and item coverage, distinguish job success from useful readback; no new provider | 5 | #124; approve freshness policy |
| Programme renewal and cancellation | Covered-item revalidation, disappearance/cancellation rules, no blanket renewal from incomplete roots; test changed/unchanged/partial/failing sources | 5 | Run evidence; agree retention/uncertain-disappearance policy before live withdrawal |
| Pilot eligibility and location evidence | Produce reproducible W3/10km/0–5 supply, with unknowns and national/wider-age retention; validate postcode/location fallback | 5 | #122/#123 and #40 overlap explicitly reconciled |
| Identity/session regression and repair design | Replay renamed/moved/multi-session programmes against existing triggers; propose only evidenced repairs and reversible migrations | 3 | #40/#135 scope reconciliation; any migration gets its own review |

This is an **18-point provisional additional work hypothesis**, not a fixed epic estimate or proof that 18 points will fix every source. Avoid double-counting work already in #40/#135/#146: reconcile boundaries before creating committed child stories. Source qualification/implementation stays in #104/#133/#134; #136's five points cover final 100-record scoring and scheduled/pilot acceptance, not these engineering changes. Additional source families, access problems or migration findings remain unestimated.

## Suggested sequence and gates

After Sprint 5, refine these slices against source evidence and re-plan Slots 6–7 from the roadmap. Deliver small vertical source-to-public outcomes, keep maintenance controls separate, and leave Activities acceptance open until the agreed pilot sample and breadth gates pass. At least three actual scheduled collections and the qualifying seven-day window are required later; manual tests do not substitute. Owner decides source activation, paid runs and destructive corrections separately. One consolidated review pack records those choices and the exact sample load.
