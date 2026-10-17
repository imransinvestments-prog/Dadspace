# Confirmed camp occurrences (#90)

## Boundary and evidence — 16 October 2026

Read-only production snapshot: seven rows in `tests/fixtures/camp-occurrences-90.json`.
Three short/full-title pairs represent three camps. The St Thomas More camp is
currently a singleton, unlike the original ticket's historical reproduction.
Four camps must remain visible; no cross-venue collapse is valid.

Rendered source checks:

| Identity | Organiser evidence | Dates | Stored rows |
|---|---|---|---:|
| SportsStars / Ryland multi-sport | https://sportsstars.classforkids.io/camp/49 | 27–29 October 2026 | 2 |
| SportsStars / St Thomas More multi-sport | https://sportsstars.classforkids.io/camp/51 | 27–29 October 2026 | 1 |
| PandESports / Arrow Vale multi-activity | https://pandesports.classforkids.io/camp/118 | 26–30 October 2026 | 2 |
| PandESports / Trinity football | https://pandesports.classforkids.io/camp/119 | 27–29 October 2026 | 2 |

Provider `/camps` pages confirm programme, venue and bounds. The rendered
https://classforkids.io/en-GB/classes/Birmingham listing confirms Ryland,
Arrow Vale and Trinity dates and the supplied `Morning, Afternoon` wording.
No precise start/end clock times are inferred from that coarse wording.

## Implementation and impact

`lib/events.ts` owns the shared public occurrence rule used by Events API/page,
Home nearby recommendations and similar-event suggestions. Reviewed aliases
are limited to those provider hosts, Birmingham source, exact location/postcode,
known titles and root URLs with only a matching optional `venueName` parameter.
Unknown programmes, query parameters and detail paths do not acquire aliases.
Date bounds, supplied time/age/cost and non-conflicting venue identity must agree.
The descriptive title wins deterministically; supplied canonical venue fields
are retained in the display object so distance resolution is not degraded.
Source rows and detail URLs remain stored and addressable unchanged.

The existing generic URL shortcut now also requires matching titles and full
session bounds; fuzzy matching cannot merge camps. Home's additional title-blind
filter is removed because it could hide distinct programmes after shared matching.
No API shape, schema, source activation, classification, ingestion/upsert key or
historical data changes. Preserving stored keys avoids creating replacement rows.

## Verification and release

Regressions cover seven-to-four identities, input order, repeated source-row
replay through the public read mapper, retained stored rows/canonical venue IDs,
distinct start/end/time/programme/age/price, conflicting venue IDs, unknown URLs
and sources, and Home preserving distinct programmes. Replay is offline; it does
not claim a scheduled or live collection run. No destructive ingestion merge is
required for a persistent display rule.

Before release: tests, TypeScript/build, CI, deployed Events/Home checks, and
owner preview/release decision. The review pack is four resulting camp identities
from seven source records, with three proposed collapses. Source equivalence was
confirmed by organiser pages; only new ambiguous evidence needs a factual decision.
Production readback follows approval. Rollback is an application revert; there is
no data migration, re-keying, compatibility window or irreversible data effect.
