# Hounslow programme qualification

The current council hub links to Hounslow Connect. Rendered categories expose
programme links, but basic category HTML only has `Loading results`. The reviewed
Storytime **detail** route contains complete programme/location evidence in normal
HTTP, so a narrowly scoped zero-model adapter can avoid incomplete category scraping.

- Council provenance: https://www.hounslow.gov.uk/libraries
- Reviewed detail: https://hounslowconnect.com/services/storytime-at-chiswick-community-hub-and-library
- Source terms for reviewer decision: https://hounslowconnect.com/terms-and-conditions

`hounslow_programme` accepts only this exact reviewed HTTPS route. It uses normal
worker HTTP/robots, semantic section boundaries and fail-closed validation. Required:
unique title, source age bounds, postcode/venue, actionable repeating weekday/time,
and complete supplied term-time/holiday exceptions. Related results cannot provide
missing evidence. A missing/changed/oversize schedule fails; no fresh-empty fallback.

Output is a regular Activity, ages 0–5, Tuesday 11:00–11:30, term-time only, free,
booking required, retaining every holiday exclusion. No occurrence dates or programme
date range is generated from recurrence or holiday boundaries. Existing canonical
Chiswick Library W4 2AB is a public exact-name/postcode candidate; identity and W3
distance/coverage still require source/venue review, not automatic acceptance.

The adapter passes through the existing normal worker cleaner, identity, venue and
public quality pipeline. It re-cleans each fetched programme, avoiding source-level
unchanged refresh of absent/cancelled listings. The qualification script performs
two normal-worker passes, stable source hash/dedupe identity, zero model calls and
zero DB writes. No database credentials, source registration or activation are used.
The dedicated Linux workflow repeats the same check and publishes review artifacts.

The existing inactive Hounslow source remains unchanged. Activating this programme
requires an explicit source/republishing decision and approved registry route; the
adapter alone does not authorize that decision. This single programme is not full
Hounslow branch or W3 coverage. Ealing's denied library portal and Acton's event-route
access remain separate qualification gaps. No access workaround is introduced.
