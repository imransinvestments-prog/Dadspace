# Dadspace discovery model

Owner clarification: Imran Tajuddin, 10 October 2026. Apply this model to future requirements, source audits, ingestion, classification, venue matching and public discovery.

- **Venues are places** parents may want to know about, from playgrounds to theme parks, including museums, libraries and family centres. A venue belongs in the directory independently of whether any activities or events are known there.
- **Activities are regular opportunities** for families, such as recurring storytimes, rhyme times, workshops or family-centre sessions. Collect these into Activities and link to a canonical venue where supported by evidence.
- **Events are infrequent or relatively rare occasions.** They may take place at a known venue and may also be discoverable alongside relevant activities. Not every venue hosts events, and a venue relationship is not required to retain a useful listing.

## Development implications

Current pilot: **W3 9LN, children aged 0–5 inclusive**, including family activities evidenced as suitable for children in that range. This supersedes the earlier TW4 6AY pilot centre. The 10 km working radius remains provisional. Preserve useful wider-age and national supply outside the pilot; a 7–11 programme is not pilot coverage, but its source can still be useful.

An inactive source is not an unsuitable source. Cookie consent, JavaScript, redirects and detail-page navigation may hide valid programmes from basic HTTP extraction. Before proposing pause/replace for missing content, check the actual operator host, family/detail pages and a supported rendered route. Keep access/republication checks separate from usefulness; record consent-related limitations explicitly.

Classify the opportunity itself, using evidence of regularity and frequency. A calendar date, ticket link, booking requirement or museum/library source does not by itself make a listing an Event. A dated occurrence can belong to a regular Activity. Preserve occurrence dates as well as any evidenced recurring schedule. Do not invent a numeric frequency threshold; ambiguous cases need review.

Keep place identity separate from the opportunities hosted there. Reuse canonical venue identities without duplicating the place for each session. Missing venue matches must not discard otherwise useful activities or events. Do not require a venue to supply activities/events before it is useful directory content.

Coverage reports must distinguish venue inventory, regular activity supply and rare-event supply. No linked activities is a discovery or matching gap, not evidence that the venue has no activities. Source-registry categories and adapters do not determine listing type.

Events appearing in activity discovery does not erase their underlying classification or provenance. The exact shared-display behavior remains a requirement to design; this clarification does not itself change routes, schemas, visibility gates or production data.

Existing historical classifications should be audited against this model. In particular, do not reclassify NCT sessions as Events solely because their records have individual dates; determine whether each represents a regular programme or a rare occasion.
