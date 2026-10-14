# Read-only source evidence and review queues

Related: #70, #32, #33, #34, #39, #40, #48. Extends the first dashboard increment
documented in operations-dashboard.md. Routes: `/ops`, `/ops/review`.

Both routes are dynamic and noindex. Each evidence entry point verifies cookie
Auth with server-side `getUser()` before any read. Exact approved UUID or confirmed
email allowlists apply; anonymous users and metadata claims never authorize reads.
Signed-out visitors use existing login; nonoperators receive 404. No mutation powers.

Database evidence requires the existing server-only service-role key. Missing
configuration is unavailable, never an empty anon/RLS response. Private rows are
not placed in the shared public GitHub metadata cache. No schema, policies, new
secrets, packages, accounts, privileged RPCs or SECURITY DEFINER views are added.

Each source family is bounded to 500 records with exact-count completeness checks.
Discovery checks, successes, failures and reported listing counts are independent.
Deals show source status and verified offers; news has no stored yield/success time.
Unknown remains unknown. A 36-hour check threshold is a signal, not a source-specific
SLA or seven-day acceptance. Inactive does not mean unsuitable; zero yield does not
prove absence of supply. Raw errors, URLs, notes, rejected-map keys and payloads
never enter the rendered source model. Each query has a ten-second deadline.

Exact national totals show public venue records, current activity/upcoming event
views, hidden venues and unwithdrawn listings without a venue link. View totals
precede public display filters. Backlogs include historical records; no W3 radius
or age acceptance is implied by national counts.

Queues show 20 rows per page with stable observation-time + ID ordering and exact
totals. Hidden venues retain source/address/discovery evidence. Separate unresolved
activity/event queues retain original dates, recurrence, schedule, ages and venue
evidence. No reclassification, removal, approval or merge occurs. Links reject
executable schemes/credentials and remove query tokens while keeping bounded public
record IDs, including MyLibrary IDs. React escapes stored text; no raw HTML renders.

Configuration, transport, malformed and incomplete responses are unavailable,
not empty. Partial failures retain other sections. Out-of-range pages offer a first
page link; only a confirmed zero total says the queue is empty.

Linux checks run both operations test files, TypeScript and production build.
New tests cover auth before privileged reads, missing service configuration,
partial failure/truncation, pagination, genuine empty versus failed queues, source
zero/unknown yield, unsafe/signed links and source-grounded schedules/dates.
Authenticated populated routes, pagination, 390px overflow and keyboard navigation
need integration QA before release. Rollback is a code revert, with no data rollback.

#70 remains open for separate reviewer permissions, previewed/audited actions,
concurrency guards and rollback. Canonical venue decisions, enrichment rights,
source activation, pilot quality, seven-day acceptance and provider costs stay open.

References:
- https://supabase.com/docs/reference/javascript/auth-getuser
- https://supabase.com/docs/reference/javascript/select
