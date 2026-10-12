# DS-10 selected-source completion report — 12 October 2026

Owner: **Imran Tajuddin**. Delivery: draft PR #71; acceptance ticket #39.

## Outcome
All **19 selected records** now have extraction or an explicit source-review outcome: 11 aggregate programmes, six route recoveries, one place conversion and one mobile-service review. There are **201 distinct unapproved proposals**, represented by **223 parent rows** in the action console. The difference is shared Hertfordshire Story Time rows and mixed Cambridge Storytime/Rhymetime identities. **Eleven Shredder rows are enquiry-only coach/day drafts, not timed sessions.**

This report completes the requested source pass. It does not close #39, claim the broader 191-record queue is approved, or establish pilot coverage. Sources already extracting well were preserved rather than re-audited. No live database writes, source activation, canonical venue creation, merge or deployment occurred in this source-proposal work. Earlier historical corrections documented on #39 remain a separate live batch.

## Programme results

| Parent programme | Proposed rows | Qualification / remaining work |
|---|---:|---|
| Baby Rhyme Time | 20 | Partial / further source or owner evidence required |
| Rhymetimes for Babies and Toddlers | 31 | Partial / further source or owner evidence required |
| Sports Coaching Sessions for Children - GK Fit | 11 | Reviewed page scope complete; owner and venue checks remain |
| Storytime | 20 | Partial / further source or owner evidence required |
| Beavers, Cubs & Scouts in South Cambridgeshire | 51 | Partial / further source or owner evidence required |
| Mini Athletics | 11 | Reviewed page scope complete; owner and venue checks remain |
| Baby Gym | 7 | Reviewed page scope complete; owner and venue checks remain |
| Child & Family Centres - Stay and Play | 5 | Reviewed page scope complete; owner and venue checks remain |
| LEGO workshops | 20 | Partial / further source or owner evidence required |
| Storytime | 20 | Partial / further source or owner evidence required |
| Shredder Skate School | 11 | Coach/day drafts only; published clock times and availability missing |
| Storytimes for Under 5s | 16 | Partial / further source or owner evidence required |

Library.Live Rhymetime: 33 detail pages reviewed, 31 retained proposals; two relocated listings excluded and Huntingdon addresses unresolved. Storytime: 16 detail pages, two shared Rhymetime identities; six flags across five listings. Both council programmes support offline snapshot parsing only: provider robots disallows unattended collection. A permitted feed or authorised route remains required.

GK Fit: 11 proposals from 19 catalogue cards; eight ended/full cards excluded. Course start labels and term lengths are not expanded into invented occurrences. Royston Nov–Dec card times supersede older timetable times; year/end bounds remain unknown. Holiday regularity requires classification review.

Scouts: 51 proposals across 16 of 21 groups. Four groups need current timetable/identity evidence; Shelfords is waiting-list-only. Milton Squirrels lacks times, Over Beavers is unavailable, Duxford non-Beavers are waiting-list-only, and Fulbourn Beavers has conflicting age statements. Addresses from reviewed HAY inventory require section-specific confirmation; its current HTTP route returned 403. No cross-group timetable borrowing.

Shredder: all six Cambridge-area venue pages reviewed. Seven coaches yield 11 child-facing coach/day drafts. Group buttons request email enquiries; exact times are absent. Private-only Jesus Green and undated holiday offers do not produce occurrences. Operator age 5+ supersedes older directory age 3+. Adult Monday classes are excluded. Unknown-time drafts cannot be marked ready in the console.

Baby Gym: recovered primary operator table yields seven weekly sessions for ages 9 months+. Duplicate RISE timetable rows are not collected. Only the starred Tuesday 10:30 session is explicitly term-time-only. Venue addresses and £4.50/£4.10 pricing discrepancy need review.

## Route, place and mobile decisions

| Record | Evidence-based recommendation | Remaining action |
|---|---|---|
| Curiosity Club | Current Curiosity Club is for adults 50+/55+, not evidenced child/family supply. Old route returns 404. | Owner review before withdrawal from family activities; retain adult-programme evidence separately. |
| Wildlings at Milton Country Park | Primary forest-activities route and Wildlings booking route recovered. Programme page gives Fridays 12:00–13:30 for non-walking babies, but its listed next dates are May 2026. | Confirm current dated availability before restoring verification; do not substitute fully booked Wild Beginnings or unrelated Wildlings operators. |
| BAYSE Multi-Sports | Original route now returns 404. Cached October 6 occurrence describes weekly Tuesday 18:00–19:30 at Brookhouse, excluding bank holidays/festive period. | Find current provider timetable; cached past date does not qualify current supply or prove closure. |
| Baby Gym | Current operator table yields seven weekly Baby Gym sessions for ages 9 months+. Select the split action to review the generated rows. | Match actual venue addresses before application; resolve £4.50 primary-page versus £4.10 old-product pricing. |
| Bampton: Rhymetime - Poetry Special | Published occasion was 30 September 2026, 10:30–11:00; original page now returns 404. This was a Poetry Special, not evidence of a weekly recurring programme. | Owner review of expiry before withdrawal; keep branch directory as discovery evidence rather than substituting another activity. |
| Marble Triceratops Skull public sculpture | Primary gallery evidence locates the public sculpture in Berkeley Square, Mayfair. Hoop daily occurrence and 23:00–22:59 range are not an actionable activity timetable. | Match/create an appropriate venue candidate before withdrawing the activity alias; preserve independent place value. |
| Didcot: Rhymetime | Old occurrence was 17 July 2026 and now returns 404. Current branch page lists Cantonese Rhymetime and other programmes. | Do not overwrite English Rhymetime with another language/programme; collect newly evidenced future occurrences separately. |
| Total Ballers 1-2-1 Sessions Football | Provider site and booking hub recovered. Mobile coaching is arranged with the family; Hoop daily 17:00 slot and SW11 map pin do not establish a fixed venue or daily availability. | Confirm service area, session age eligibility and appointment through actual booking; £35/hour primary versus £40/monthly-paid aggregator pricing needs review. |

A 404 alone does not prove closure. Cached past dates are labelled as historical evidence. Curiosity Club is excluded from evidenced child/family supply because its current programme is 50+/55+. Bampton Poetry Special was 30 September; old Didcot Rhymetime was 17 July. Branch discovery pages do not substitute another programme for either historical row. Wildlings has an accessible route but lists May dates, so current availability is unqualified. BAYSE has only a cached past occurrence and a current 404.

The marble sculpture belongs in place review with primary Berkeley Square evidence; venue matching must precede withdrawal of the activity alias. Total Ballers is mobile/by arrangement; neither the generic Hoop map pin nor daily placeholder time establishes a fixed venue or guaranteed availability. The primary booking hub is retained without making contact or a booking.

## Interface and evidence

Open [the local action console](ds10-action-console-2026-10-12.html), refresh, then **Add generated proposals to this draft**. Existing edits are preserved and proposal keys prevent repeated additions. For Baby Gym, choose **Split into individual sessions**. Route/place/mobile reviews show the recommendation and remaining questions. JSON export/import retains cohort/fingerprint validation; ready status remains a human decision. The console is an offline prototype, not the authenticated production operations UI requested in #70.

Evidence files in `artefacts/data`: `ds10-automated-session-proposals-2026-10-12.json`, the two council snapshots/extractions, GK Fit/Scouts/Shredder extraction ledgers, the Scout route manifest, and `ds10-remaining-source-review-2026-10-12.json`. Their public links, constraints and exclusions remain with proposals. Local full database backups, caches, virtual environments and dependency runtimes are excluded from publication.

## Verification and operating limits

**152 Python tests passed**, plus console validation, guarded import tests and both inline JavaScript syntax checks. Tests cover duplicate identities, changed layouts, unsafe links, past/full/ended exclusions, age conflicts, separate colonies/nights, missing times and partial failures. Single-programme replay preserves other parent records. No model calls are used by these deterministic proposal adapters. Per-run limits are 50 network attempts and 36 checked public pages; last-run counters are not cumulative totals. Browser-derived council snapshots are clearly separated from HTTP collection.

Run one selected programme at a time with `scripts/collect_ds10_session_proposals.py --record-id <record UUID> --as-of 2026-10-12`, then rebuild with `scripts/build_ds10_action_console.py`. The route ledger is attached with `scripts/record_ds10_remaining_source_review.py`. Global request budgets may make a full batch partial; source failures are not proof of absent supply.

## Acceptance and ticket follow-up

- **#39:** implementation/proposals and route review delivered; retain human 100-row scoring, current source access, venue/eligibility review, historical decision application, normal worker rollout/repeat ingestion, pilot breadth and seven-day evidence as open.
- **#40:** canonical matching, alias resolution (including Barton and the sculpture), relationship provenance and repeat/concurrent-import checks remain open. Named venues are not approved canonical identities.
- **#70:** offline 19-record prototype and schemas provided; authenticated production operations UI, permissions and all other operational queues remain open.
- **#32:** bounded cost/access evidence provided; scheduled monitoring and seven-day operational observation remain open.
- **#44 / #29:** no release or pilot acceptance claimed. Pilot remains W3 9LN, 10 km, ages 0–5; national/wider-age proposals are not London pilot supply.
- **#38:** closed source-audit baseline remains closed; these implementation/access findings are follow-up evidence under #39.

All relevant ticket updates link to this report on the draft branch. PR #71 remains draft and unmerged.
