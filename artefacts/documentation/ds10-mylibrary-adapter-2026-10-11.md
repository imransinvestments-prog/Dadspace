# DS-10 MyLibrary adapter delivery

This is the first implementation of the #38 collection plan under #39. Pilot: W3 9LN, ages 0–5 inclusive, confirmed 10 km radius. Imran Tajuddin is the content/technical owner. Candidate sources remain inactive; the 20 healthy routes are unchanged.

## Implemented behaviour

- An explicit `source_adapter=mylibrary_calendar` routes through the normal quality worker without Gemini. The default collector and existing active source lanes remain unchanged.
- Browser rendering expands the observed Upcoming Events Load More control. Page, request, time and pagination limits are enforced; an incomplete snapshot fails rather than publishing partial supply or refreshing stale records.
- Public event details supply venue/address/postcode, description, cost, current-item age restriction, time and booking evidence. Related-event age tags are excluded. Ambiguous Activity/Event classification is rejected for review; dates alone do not determine the type.
- Explicit regularity plus full-series tables supply published occurrence dates. Missing weeks are preserved. Conflicting venue, age or start-time evidence fails the snapshot. Cancelled occurrences are omitted. The schedule stores exact dates instead of an uninterrupted weekly promise, and the first/last published dates remain on the Activity row. A range is not a recurrence rule.
- Existing title/venue Activity identity remains stable across repeats. Exact items are re-cleaned on every run at zero model cost; source-level unchanged freshness refresh is deliberately avoided, because it could renew disappeared/cancelled programmes.
- Optional single-occurrence ICS parsing supports timezone conversion and HTML/date/time cross-checks. Unbounded recurrence, all-day/malformed exports and contradictions fail. ICS fetching is **not enabled** in the normal adapter: the Ealing export returned HTTP 403 during this review. HTML remains necessary for family, age and regularity evidence.
- The renderer follows no login, consent acceptance or challenge bypass. Host allowlist currently covers Ealing, Merton, Sutton and Idea Store; only Ealing detail/series markup was manually verified in this delivery. Cross-host redirects/handoffs are refused.

## Validation and evidence

All 99 existing/new Python tests passed locally, including 14 new MyLibrary regressions and 12 existing ingestion regressions. The reduced Southall fixture is transcribed from the public rendered page, not a full archived HTML snapshot. It deliberately retains Northolt's related 0–5 tag to verify that it cannot leak into Southall's missing age.

Browser inspection on 11 October confirmed Southall/Northolt detail fields and Southall full-series markup. Southall publishes 12/19 October then 2 November; 26 October must not be generated. Northolt explicitly states ages 0–5. The full-series page uses a different table ID and relative Today/Tomorrow labels; the adapter resolves a relative label only for the exact already-dated detail occurrence.

The read-only CI runner performs two normal-worker passes for reviewed Ealing Southall/Northolt, Merton and Sutton details, retaining accepted rows, rejection counters, requests, hashes and errors in a downloadable `mylibrary-source-review` artifact. It has no database credentials and runs with venue writes disabled. Two passes do not satisfy the proposed three scheduled collections over seven days.

## Remaining #39 acceptance

### Repair and owner-review preparation (11 October, latest)

This section supersedes the earlier Sutton classification gap below. Named Rhymetime/Storytime/Stay-and-Play programmes can now qualify from matching programme wording **and** a validated provider series with another published occurrence. A series/date alone still cannot classify arbitrary listings; explicit rare-event evidence remains separate. Explicit recurrence in the current description is recognised as well as header labels. Booking and parent-attendance requirements are retained.

Collection declares a 30-day window (configurable 1–90 days). Historical/out-of-window rows are excluded before checking venue/title/time conflicts; old years of programme changes do not block the current window. Every in-window occurrence detail is checked for dates, start/end time, venue, title, age and price; contradictions fail rather than borrowing today's duration or price. Cancelled/sold-out occurrences are excluded. The default request/time limits remain in effect, and a long/incomplete snapshot still fails. This qualifies the explicit window, not every future session in the operator calendar.

[Sutton two-pass live evidence](../data/ds10-sutton-live-2026-10-11.json) records one accepted Activity per pass, 14 exact published dates through 10 November, identical programme identity, 15 public-HTML requests per pass, zero model calls and zero DB writes. This local check used public requests HTML through the normal worker; the CI browser route is checked separately. All 104 Python tests pass locally. Tests cover inferred regular-programme series, historical rows, individual changed end times/cancellations and incomplete human reviews.

The owner agreed to perform the 100-item human review. [Interactive worksheet](ds10-human-review-2026-10-11.html), [CSV worksheet](../data/ds10-human-review-2026-10-11.csv) and [frozen source-balanced sample](../data/ds10-human-review-2026-10-11.json) contain 100 stored Activities across 20 sources, including stale/incomplete rows. Mark relevance/currentness/actionability for all 100, download the results JSON and validate it with `python scripts/validate_ds10_human_review.py <results.json>`. Answers remain empty until the owner reviews them. A passing quality review is not source activation or pilot breadth acceptance.

Ealing and Merton's calendar hosts still return HTTP 403 under the disclosed Dadspace bot identity. Merton's official `libraries.merton.gov.uk/events` portal is readable and offers a legitimate alternative for investigation, but its initial public event cards lack dates before JavaScript hydration; it is not yet qualified as a complete unattended feed. No access-control bypass is used. Human review, permitted unattended routes, pilot breadth, historical withdrawal and the seven-day scheduled repeat requirement remain genuine closure dependencies. #39 must not close on the strength of parser tests or two local passes.

### Unattended runner findings (11 October)

[Run 38095936148](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936148) passed the offline ingestion/calendar regressions but failed live supply validation. Both passes returned HTTP 403 for Southall, Northolt and Merton. Sutton returned `ok_zero` twice: the public Rhymetime detail lacks the explicit regularity wording required by the initial classifier. Its named series and family description are useful review evidence, but the adapter does not yet qualify that programme. This is an access/classification gap, not evidence that these libraries have no activities. The [downloadable results](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936148/artifacts/11685903516) contain the per-pass errors and counters.

The validation now requires accepted supply and stable, nonempty unique identities from **each** reviewed source on both passes, with zero recorded model calls. One working source cannot mask failed sources. No HTTP 403 bypass, source activation or production deployment is proposed. Ealing/Merton need a permitted unattended feed/route; Sutton needs independently reviewed programme regularity evidence before classification can be broadened.

The existing [events/activities baseline](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936135) also failed its Gemini-dependent collection step with `402 RESOURCE_EXHAUSTED`: the configured Gemini prepayment credits are depleted. This adapter uses no Gemini, so funding does not fix its HTTP 403/classification gaps. The baseline backup/preview passed. PR #71 remains a draft and #39 remains open.

Confirm permitted unattended collection/republishing for each operator. Validate the CI renderer and platform differences against actual returned evidence before registry changes. The parser does not certify all London calendars, all venues or a 100-item 90% human accuracy pass. Root calendars over the bounded request budget fail; use reviewed narrower programme routes or an explicit collection-window design rather than claiming full coverage.

Cancellation is excluded from the new accepted snapshot; existing stale rows expire through current freshness policy. Immediate per-item withdrawal/review is not implemented here. A future source review must address this before claiming complete cancellation handling. The public Activities mapper currently displays schedule text, not the date bounds; those bounds remain stored for provenance and future occurrence views.

Camden/Bexley/Barnet standing schedules, Hounslow rendered pagination, Better embedded timetables, wider operator discovery, canonical matching (#40), 10 activities across three categories/two providers, human quality acceptance, reviewed source activation and live repeat ingestion remain outstanding. #39 stays open. No deployment or production source activation is included in this delivery.

## Public portal qualification (12 October, latest)

This supersedes the Ealing/Merton access gap above. Their official public library portals publish structured event records in the returned React server-component document. The new opt-in `library_portal` adapter reads those published records without executing scripts or using private endpoints. Text-frame references are resolved with UTF-8 byte lengths. Calendar booking URLs remain provenance links; blocked calendar hosts are not bypassed.

The index must extend beyond the declared window and remain chronological. Ealing qualifies a 30-day window; Merton currently qualifies seven days. Private, unpublished, cancelled, full, virtual, ambiguous and conflicting-condition records are excluded with rejection counters. Exact dates and varying session times are retained. Missing ages and addresses are not fabricated. Venue matching and pilot eligibility still require separate evidence.

[Read-only two-pass evidence](../data/ds10-public-portal-live-2026-10-12.json) records Ealing six accepted programmes, Merton fourteen and Sutton one on each normal-worker pass, with stable identities and zero model calls/database writes. Sutton used public requests HTML locally; the CI browser route requires its own new run. These programme counts do not certify pilot coverage.

Sutton's published Today/Tomorrow labels now resolve against the fresh UK collection date; relative labels without an anchor fail. All 110 Python tests pass. Previous evidence and counts remain historical snapshots.

The owner worksheet remains unanswered. Closure still requires the 100-item human review at 90% quality, verified pilot breadth, scheduled collection evidence across seven days, remaining operator routes and historical withdrawal handling. Sources remain inactive; this change does not deploy or activate production collection.
