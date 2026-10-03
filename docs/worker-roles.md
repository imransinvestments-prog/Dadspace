# Dadspace worker roles

The worker boundary is based on **business responsibility**, not only fetch technology.

## Civic / event collector

Workflow: `.github/workflows/collect-civic.yml`

Purpose: collect dated family events from councils, heritage/park sources and ordinary server-rendered venue/event pages.

Typical fetch path: `requests`.

It owns **what is happening and when** for event-oriented sources. It may resolve a venue for an event, but it does not own authoritative venue registries.

## Activities collector

Workflow: `.github/workflows/collect-activities.yml`

Purpose: collect recurring or directory-style family activities/classes/groups, especially JS-rendered listings.

Typical fetch path: browser/Playwright.

NCT belongs to this business role because its useful records are parent/baby/family groups and events. NCT should use a dedicated `nct_group_finder` adapter when an approved data-access route is available, rather than treating the postcode landing page as a generic single-page source.

## Venue reference worker

Workflow: `.github/workflows/venue-reference.yml`
Worker: `venue_reference_worker.py`

Purpose: reconcile authoritative/reference facility datasets against the canonical `venues` table.

Initial adapters:
- Sport England Active Places (`active_places`)
- Public Library Open Data-compatible feeds (`library_open_data`)

Rules:
1. Existing Dadspace venues are canonical.
2. Match before insert, with postcode + normalised name as the strongest routine signal and coordinates as supporting evidence.
3. Enrich existing venue fields only when they are missing.
4. Same-postcode/fuzzy-name uncertainty goes to review rather than creating a duplicate.
5. Only clearly new venues are inserted, and they start with `public_visible=false` and `discovery_status='discovered'`.
6. Every accepted reference relationship is stored in `venue_sources`, allowing one venue to have multiple authoritative/discovery sources.
7. Reference-data failures must not block event/activity collection.

## Source metadata

`public.sources.source_role` describes responsibility:
- `event_listing`
- `activity_listing`
- `venue_reference`

`source_adapter` identifies source-specific handling where a generic page collector is insufficient.

Fetch method remains an implementation detail. A source's role should not change merely because its website moves from HTML to JavaScript or an API.
