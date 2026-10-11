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

### Unattended runner findings (11 October)

[Run 38095936148](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936148) passed the offline ingestion/calendar regressions but failed live supply validation. Both passes returned HTTP 403 for Southall, Northolt and Merton. Sutton returned `ok_zero` twice: the public Rhymetime detail lacks the explicit regularity wording required by the initial classifier. Its named series and family description are useful review evidence, but the adapter does not yet qualify that programme. This is an access/classification gap, not evidence that these libraries have no activities. The [downloadable results](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936148/artifacts/11685903516) contain the per-pass errors and counters.

The validation now requires accepted supply and stable, nonempty unique identities from **each** reviewed source on both passes, with zero recorded model calls. One working source cannot mask failed sources. No HTTP 403 bypass, source activation or production deployment is proposed. Ealing/Merton need a permitted unattended feed/route; Sutton needs independently reviewed programme regularity evidence before classification can be broadened.

The existing [events/activities baseline](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38095936135) also failed its Gemini-dependent collection step with `402 RESOURCE_EXHAUSTED`: the configured Gemini prepayment credits are depleted. This adapter uses no Gemini, so funding does not fix its HTTP 403/classification gaps. The baseline backup/preview passed. PR #71 remains a draft and #39 remains open.

Confirm permitted unattended collection/republishing for each operator. Validate the CI renderer and platform differences against actual returned evidence before registry changes. The parser does not certify all London calendars, all venues or a 100-item 90% human accuracy pass. Root calendars over the bounded request budget fail; use reviewed narrower programme routes or an explicit collection-window design rather than claiming full coverage.

Cancellation is excluded from the new accepted snapshot; existing stale rows expire through current freshness policy. Immediate per-item withdrawal/review is not implemented here. A future source review must address this before claiming complete cancellation handling. The public Activities mapper currently displays schedule text, not the date bounds; those bounds remain stored for provenance and future occurrence views.

Camden/Bexley/Barnet standing schedules, Hounslow rendered pagination, Better embedded timetables, wider operator discovery, canonical matching (#40), 10 activities across three categories/two providers, human quality acceptance, reviewed source activation and live repeat ingestion remain outstanding. #39 stays open. No deployment or production source activation is included in this delivery.
