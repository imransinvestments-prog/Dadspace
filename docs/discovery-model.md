# Dadspace discovery model

Owner clarification: Imran Tajuddin, 10 October 2026. Apply this model to future requirements, source audits, ingestion, classification, venue matching and public discovery.

- **Venues are places** parents may want to know about, from playgrounds to theme parks, including museums, libraries and family centres. A venue belongs in the directory independently of whether any activities or events are known there.
- **Activities are regular opportunities** for families, such as recurring storytimes, rhyme times, workshops or family-centre sessions. Collect these into Activities and link to a canonical venue where supported by evidence.
- **Events are infrequent or relatively rare occasions.** They may take place at a known venue and may also be discoverable alongside relevant activities. Not every venue hosts events, and a venue relationship is not required to retain a useful listing.

## Development implications

Classify the opportunity itself, using evidence of regularity and frequency. A calendar date, ticket link, booking requirement or museum/library source does not by itself make a listing an Event. A dated occurrence can belong to a regular Activity. Preserve occurrence dates as well as any evidenced recurring schedule. Do not invent a numeric frequency threshold; ambiguous cases need review.

Keep place identity separate from the opportunities hosted there. Reuse canonical venue identities without duplicating the place for each session. Missing venue matches must not discard otherwise useful activities or events. Do not require a venue to supply activities/events before it is useful directory content.

Coverage reports must distinguish venue inventory, regular activity supply and rare-event supply. No linked activities is a discovery or matching gap, not evidence that the venue has no activities. Source-registry categories and adapters do not determine listing type.

Events appearing in activity discovery does not erase their underlying classification or provenance. The exact shared-display behavior remains a requirement to design; this clarification does not itself change routes, schemas, visibility gates or production data.

Existing historical classifications should be audited against this model. In particular, do not reclassify NCT sessions as Events solely because their records have individual dates; determine whether each represents a regular programme or a rare occasion.
