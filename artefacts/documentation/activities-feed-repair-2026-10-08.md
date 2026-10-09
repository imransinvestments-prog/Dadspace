# Activities feed repair and source coverage

Delivery: [DS-10 #39](https://github.com/imransinvestments-prog/Dadspace/issues/39), supporting source audit #38 and venue matching #40. Audit date: 8 October 2026 (Europe/London).

## Baseline and data review

The database contains 422 recurring activities and 211 dated events. Only 58 activities and 19 events have canonical venue links. Activities have 107 missing schedules, 74 bare clock-time schedules, 28 missing locations and 36 missing specific URLs. A stricter structural review finds only 27/422 with all three of location, URL and recurring day/frequency. This is an actionability screen, not human accuracy approval. The remaining 395 need detail-page review; do not invent schedules or bulk delete records.

The latest 30 records were inspected. Hertfordshire's generic Baby Rhyme Time has duration '30 minutes', Storytime has no schedule, and LEGO Workshops says 'Regular sessions': these are useful discovery leads, not complete local activities. Multiple Hoop records have a clock time but no weekday or location. The new gate requires a recurring day/frequency, a location and a specific link before saving a new activity. Public eligibility of historical incomplete rows remains a follow-up; the gate does not retroactively validate or remove them.

## Comprehensive venue inventory and source candidates

All 4,571 Museum and 3,440 library records were inventoried. Museum websites are populated for 2,037 records; grouping reveals 1,710 website domains plus the missing-website group. Libraries have only four websites, no operator values, and 151 town buckets including missing town. 2,932 libraries are visible. Council/branch identity enrichment is essential; town or county names alone are not sufficient venue-match evidence.

The manifest adds 38 operator-level candidates across all four UK nations: 17 library and 21 museum sources. Museum-domain matches cover 103 existing museum records. Access tests find 28 readable routes, six failed requests and four pages with insufficient rendered HTTP content. Access is not validated extraction or republication permission. Full inventory, current sources, candidate routes and the latest 30-row review are included in the downloadable evidence bundle. Repository CSVs account for every museum domain and library town bucket, including explicit unserved gaps.

37 new candidates were inserted into `sources` **inactive**; Hertfordshire's existing URL was preserved. No duplicate URL, automatic source activation or website-wide crawling. Candidate access failures remain visible and must be repaired or assigned a browser/API route. Every source still needs maintenance ownership, source terms and an extraction decision.

## Implemented repairs

- PostgreSQL SQLSTATE 21000 occurs when the identity trigger maps different batch dedupe keys onto one canonical row. The failed bulk statement is atomic; retry only this error as sequential upserts. Other errors and partial fallback failures remain failed saves, so the worker does not advance the source hash. Retries are idempotent under the existing identity trigger.
- An opt-in `venue_listing_details` adapter fetches a listing plus at most four same-host event/family detail pages (hard cap eight), with robots checks and existing request/time budgets. It strips navigation, deduplicates links, rejects external/private/download routes, and retains source-page URLs in the extraction content. Detail failures fail the source; they cannot become a successful empty refresh. External booking hosts and deep pagination remain source-specific work.
- Recurring activities require evidence of location, URL and a weekday/frequency; duration and clock-only schedules are rejected with counters. Existing family/date/age gates remain.
- Read-only baseline explicitly sets `base.DRY_RUN=True`: venue resolution must not create candidates during a read-only test.
- Live migration `20261008202338_activity_freshness_only_after_unchanged_success` stops failed/changed-page checks refreshing all old activities. Successful unchanged-hash checks alone may renew existing activity evidence; changed-page saves renew only accepted rows. The function uses invoker permissions and public/anon/authenticated execution remains revoked.

## Verification and operating steps

All 79 Python tests, including 12 focused ingestion regressions, and the existing worker self-test passed locally. Live transaction-only probes confirmed failed fetch 0/6 refreshed, changed page 0/8 refreshed, and successful unchanged check 8/8 refreshed; all transactions rolled back. Source access audit made zero AI calls and zero database writes. Candidate inserts and the freshness migration were verified separately.

`activity-venue-source-review.yml` performs two real extraction passes through the normal quality worker for eight pilot sources, with all database and venue writes disabled. It records every accepted row, rejected counters, source failure, page hash and actual model/API/token usage. The existing browser baseline covers five current directory sources. The real eight-source review completed successfully in run 37839982261, with zero database writes. Kent failed HTTP 403 twice and Libraries NI timed out twice on the runner. Six sources returned accepted rows, with 100 accepted rows across both passes and 48 distinct identities after replaying the repaired key logic. API usage was 12 attempts, 106,199 prompt tokens, 83,078 output tokens and 189,277 total tokens (thinking is a reported subset, not added again). Monetary cost depends on the account pricing; no charge estimate was invented. Two forced extraction passes are extraction-repeat evidence; they are not live database repeat-ingestion evidence.

After reviewing extraction artifacts: repair unsupported sources; confirm canonical branch identities; deploy the worker; enable only individually approved routes; back up events; run a bounded live collector twice; verify stable IDs and no duplicate identity keys; review public results; and observe scheduled freshness/health. Source activation before worker rollout would use the old collector and is unsafe. Human 90%/100 quality review, pilot coverage and seven-day reliability are still open. Production site launch remains subject to the existing release gate.

## Reproduction

`python events_worker.py --self-test`

`python -m unittest discover -s tests -p test_activity_ingestion.py -v`

`python scripts/audit_activity_sources.py --output activity-source-access.json`

`DRY_RUN=true python scripts/validate_venue_activity_sources.py` (requires existing Supabase/Gemini secrets; read-only)

Canonical source metadata and access evidence: `artefacts/data/activities-source-candidates.json`, `activities-source-access-2026-10-08.json`, `activities-museum-domain-coverage.csv`, `activities-library-town-coverage.csv`. Reviewed source inserts: `activity-source-candidates.sql`. Replay schema via the recorded migration; do not re-run ad hoc edits.

## Extraction review findings

| Source | Pass 1 | Pass 2 | Matching identities |
|---|---:|---:|---:|
| Cardiff Libraries | 7 | 7 | 7 |
| Museum Wales | 10 | 11 | 10 |
| Royal Museums Greenwich | 11 | 11 | 11 |
| Birmingham Museums | 8 | 8 | 8 |
| Horniman Museum | 8 | 4 | 4 |
| Amersham Museum | 2 | 3 | 2 |

Cardiff originally changed every key when titles gained/lost a venue suffix and addresses changed wording. Titles now remove only an exact redundant venue suffix; dated listings use specific detail URL, date and venue for identity. Replay of the recorded seven-row fixture matches 7/7. The actual extraction report retains original rows for reproducibility. Counts above use the repaired identity logic and are not live database upsert results.

Museum Wales inconsistently classified Play Sessions as a dateless activity (rejected for missing schedule) or a dated event; Horniman lost four rows between passes and includes exhibition start dates of today, which require detail-page date confirmation. Amersham added a lacemaking listing linked to the generic calendar in its second pass. These routes remain unapproved: neither a successful process nor accepted row count proves source accuracy. Birmingham's duplicate title variants collapse to eight rows, though the old kept counter says nine; the new key-level counter records merged duplicates correctly. Cardiff venues are absent from the current canonical library inventory and require explicit branch enrichment. Existing source links and automatically found venue names do not prove canonical linkage.

The five-directory browser baseline produced 47 eligible rows; the five-source civic baseline produced one, with one 404. These baseline artifacts contain counters, not all accepted row content, so only the eight-source extraction artifact supports new-row detail review. Public discovery/SEO, deals-quality and civic checks passed on d05d8ce; final identity changes must pass the subsequent branch checks before merge.

The bounded inventory discovery script starts from real inventoried museum homepages, respects robots, retains canonical IDs, and follows only actually linked pages. Its first 20 distinct domains found 21 candidate URLs on eight sites; eight had no suitable links and four failed. A cursor allows the full 1,710-domain backlog to be processed in reviewed batches without a broad automatic crawl, AI calls or activation. This is comprehensive inventory coverage with an explicit discovery backlog, not a claim that 38 seeds cover all venues.

Evidence includes the full stored-row structural review, all accepted/rejected pilot rows and token counters, replay overlap, complete inventories, access failures and the first discovery batch. Historical incomplete records, source-specific extraction instability, inaccessible routes and live repeat ingestion remain outstanding delivery work under DS-10.
