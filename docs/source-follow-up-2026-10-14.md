# Source follow-up — 14 October 2026

Investigation for #39 and #48. No source activation, registry/listing writes,
provider changes or paid AI. Snapshots are not sustained runner qualification
or permission to republish.

## Babipur

Live run 38584684904 reported HTTP 500 while accepting other merchants. The
adapter correctly discards failed product batches and renews no freshness.
A later local run of the unchanged approved adapter passed: Atom collection and
seven product pages returned `ok`, yielding 23 variants. No alternate host or
bypass. This suggests transient failure; normal runner recovery and public quality
remain unverified. Next: normal worker dry run, then live verification if successful.
Keep quality gates and failure reporting unchanged.

Follow-up: normal GitHub worker dry run 38596955353 passed with 23 Babipur
variants, 542 overall fetched and 120 kept, zero AI/tokens/writes. The health report
correctly still showed old database source failure because dry runs do not update it.

One subsequent normal live collection, 38597533405, passed. Database readback:
Babipur status `ok`, zero consecutive failures, fresh check/success at
2026-10-14 16:24 UTC and 19 verified offers. This establishes recovery for this
run, not sustained reliability or the complete deal/pilot acceptance criteria.

## W3 supply gaps

Ealing's active council-events source reports zero listings. Its official library
page links to a separate Bookshelf events portal, which returned 403 in this check.
Prior local MyLibrary success versus runner 403 remains unresolved. Seek permitted
feed/hosting or source-supported access; no access bypass or activation.

- Provenance: https://www.ealing.gov.uk/libraries
- Linked route: https://libraries.ealing.gov.uk/events

Hounslow's inactive source is the council library hub. The current official hub
links to Hounslow Connect's Local Libraries directory with branch routes. The older
search-indexed council timetable is not sufficient current evidence. Follow the
current official route, check robots/terms and programme detail in the normal
worker, preserve dates/term-time/ages, validate canonical venues and W3 distance,
repeat on runner, then request reviewed activation.

- Provenance: https://www.hounslow.gov.uk/libraries
- Linked directory: https://hounslowconnect.com/pages/local-libraries

Local normal-worker HTTP/robots probes passed for this directory and its Chiswick
branch, but the branch HTML contains only `Loading results` and no JSON-LD events
or programme detail links. Static extraction is therefore not qualified: check
permitted rendered content with the browser worker before proposing an adapter.

The permitted in-app rendered page subsequently exposed nine service links,
including Storytime. Its detail page gives ages 0–5, Tuesday 11:00–11:30, term-time
only, required booking and explicit October/Christmas holiday exclusions, with
Chiswick Library W4 2AB provenance. This is a regular activity, not a one-off event.
It is a strong candidate but still needs source terms, normal browser-worker
repeat checks, canonical matching and pilot-distance review before activation.

- Detail: https://hounslowconnect.com/services/storytime-at-chiswick-community-hub-and-library

Acton Depot's active source points to museum-wide what's-on and has ten 403
failures. The official booking domain advertises Depot family tours as a candidate
route. Museum-wide events do not establish an Acton location or ages 0–5 fit.
Confirm permitted access, individual dates, ages and venue before replacement.

- Candidate: https://bookings.ltmuseum.co.uk/

Local normal-worker HTTP/robots checks passed on the booking homepage, but plain
HTML supplied no event JSON-LD or programme links. Rendered detail qualification
is still required. Access to this candidate does not cure the active route's 403.

Sutton is outside the W3 10km pilot: earlier runner checks inform the adapter but
do not fill this local gap. Inactive status/access failure alone is not unsuitability.
