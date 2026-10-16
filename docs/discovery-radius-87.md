# Radius-bounded discovery — #87

## Behaviour

Activities, events and the places directory share a validated 10 km default,
explicit 25/50/100 km expansion and a separate unknown-distance view. Online
opportunities are separate from local matches; physical places do not offer an
online filter. Distances are straight-line, not travel estimates.

Places filter public visibility, usable names, category, free entry, text,
location, radius and distance scope before counting and pagination. The narrow
eligible set is ordered by distance, name and ID before the requested page is
joined to full records. The public API maps only the existing public venue
fields plus the server-calculated distance. Neither SQL nor the API changes
venue publication decisions, canonical identities or records.

The directory's explicit national-browse action preserves the server-rendered
national page and its ordering, including directly linked national pages.
The return-to-nearby action uses the currently selected location. Category-tile
totals are explicitly UK-wide. The separate result
count follows the current filters and radius. National event hero totals also
remain explicitly UK-wide. No unsupported venue age/time/indoor/outdoor filter
is invented; applicable event age/time/free filters remain in the event explorer.

Search changes hide the previous rows and count immediately, abort superseded
requests and isolate errors by request URL. Late first-page or load-more
responses cannot replace the new search. Surprise selections also belong to
their original search URL and disappear immediately when that URL changes.

## Verification

S1 release: PR #159, merged `52b711a00e0f5256c3c51ddb24d6daa8b639e905`.
Owner accepted the S1 preview and release on 16 October 2026. The owner later
requested S2 be brought forward to complete and close the whole ticket,
replacing #88 in the same 8-point sprint scope.

S2 targeted suite: 28 checks across `venue-radius`, `directory-page`,
`discovery-explorers`, `public-discovery`, `discovery-radius` and
`discovery-feed-states`. PostgreSQL SQL tests use pinned PGlite, isolated
fixtures and the actual migration. They cover inside/outside radius, paging,
unique IDs, free/category/text filters, empty local supply, missing/invalid
coordinates, hidden/nameless exclusions, national inventory, malformed inputs,
permissions and the public API projection. Hook tests defer responses to check
out-of-order searches, stale load-more results, error isolation and retry.
Explorer tests cover radius/scope wiring, national ordering, surprise reset,
and matching event totals/cards after age/time/free/text changes.

Read-only production query checks on 16 October 2026 (dated inventory examples,
not guaranteed supply counts):

| Point and scope | Eligible places |
|---|---:|
| Cardiff 51.48, -3.18; 10 km | 264 |
| Same, museums | 55 |
| Same, explicitly free | 2 |
| W3-area 51.51, -0.27; 10 km | 1,088 |
| Same, 25 km | 4,627 |
| Separate missing/invalid coordinates | 15 |
| National published inventory | 56,745 |

First-page unique-ID counts and maximum distances were checked. An actual
`service_role` transaction returned the two Cardiff free places and rolled
back. No venue fixtures or data corrections were written to production.
Existing security-advisor findings were unchanged; none references the new
function. Preview and release evidence is recorded in the delivery PR and #87.

## Database rollout and recovery

Migration `20261016135627_discovery_venue_radius.sql` is additive and was applied
as `discovery_venue_radius`. It introduces `discovery_venue_page`, uses
`SECURITY INVOKER`, fixes the search path and grants execution only to the
existing service role. Anonymous and authenticated callers have no execution
grant. The previously deployed `nearby_venue_page` remains intact so migration
deployment does not alter the old application's behaviour.

Release the app only after this migration exists. Roll back the app release
first if necessary; the unused new read function can safely remain, or be
removed separately after confirming no deployed caller uses it. There are no
venue-data changes to reverse. Parent closure requires release/readback of S2
as well as the already accepted S1; #88 and duplicate-place remediation #89
remain separate work.
