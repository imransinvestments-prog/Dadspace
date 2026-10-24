# Council discovery

Owner request, 22 October 2026: make sure there are enough places for every UK postcode by finding the top 10 dad-and-kid-friendly weekend spots in each council, keeping only places that are not already in `venues`, output as a strict JSON array, as part of the venue worker.

**Changed by owner decision, 23 October 2026 (#243):** there is no cap, so every new place is kept. Parks and playgrounds are left out because they rarely change, and attractions, castles, arts centres, planetariums, high ropes, trampoline parks, mini golf and mazes are added. Every type is published, and only flagged places are reviewed first (see Outputs). AI notes are drafted for the top 10 per council only.

`venue_council_discovery.py` does this. It runs from the venue reference loader (`venue_reference_loader_v2.py`) once its source is activated, or on its own for one council. The ranking measures how notable and well documented a place is in OpenStreetMap, not how good it is for families, so public copy must not call these places "top" or "best".

## What it does, per council

1. **Councils** come from `geography_areas` (`kind = 'council'`) in the latest `geography_releases` row: 361 councils in the ONS May 2026 release. The 11 Northern Ireland councils (`N…` codes) are excluded for now (owner decision, 22 Oct, #243), which leaves 350.
2. **Places** come from OpenStreetMap via Overpass. The query is scoped to the council's boundary using `ref:gss`, the ONS code. It covers named museums, zoos and petting farms, aquariums, theme parks, planetariums, water parks, indoor play, trampoline parks, high ropes courses, mazes, mini golf, nature reserves, castles, arts centres and tourist attractions. It drops unnamed and generic names and private or disused places.
   - **Attractions** (`tourism=attraction`) must have a website or Wikidata entry. Single rides and zoo enclosures (`attraction=roller_coaster`, `animal` and similar) are dropped, because they are parts of another place. A maze tagged as an attraction is listed as a Maze.
   - **Castles** (`historic=castle`) must have a website or opening hours, because most castle tags are ruins and earthworks.

   **Not discovered here** (owner decisions, #243): libraries (23 Oct; the Public Library Open Data reference source covers them), and parks and playgrounds (23 Oct; they rarely change).
3. **Ranking** is deterministic. It weighs category, Wikidata notability, website and opening hours, and facility evidence (`changing_table`, `toilets`, `wheelchair`, `baby_feeding`), plus size for nature reserves. Every new place is kept, and ties break on the OSM id. The rank decides which places get AI notes.
4. **New only.** A place is skipped when `venues` already holds the same OSM element (in `source_url` or `discovered_source_url`). Existing venues are loaded in pages ordered by `id`. Every candidate's OSM URL is also checked directly against `venues`, so a stored place can't come back as new even if the bulk load misses a row; that happened with Hanwell Zoo in the first dry run, 22 Oct. A place is also skipped when a similar-named venue (ratio 0.75 or more) sits inside its outline, or when the shared `choose_match` rules in `venue_reference_worker.py` find it:
   - same name and postcode;
   - same postcode and a similar name;
   - within 80 m and a similar name.

   The check runs twice: before the postcode is known, and again with the resolved postcode, so the postcode rules can fire. Places that are near (within 150 m or inside the outline) and only partly similar are kept as **possible duplicates**: they are inserted hidden, with the possible match named in the review reason. Duplicates within a run are skipped.
5. **Postcodes** come from OSM `addr:postcode`, or from postcodes.io as the nearest postcode (`postcode_source = reverse_nearest`).
   - **Inferred postcodes are never stored on the venue.** They stay in the JSON and the provenance payload as a reviewer hint, and the review reason says so.
   - A **point** whose postcode is in a neighbouring council is kept and flagged (`council_check = postcode_other_council`).
   - An **outline** (park, reserve) whose postcode is in a neighbouring council only crosses the boundary, and the neighbour's own run returns it. In the 22 Oct Ealing run this was Gunnersbury Park, Minet Country Park and others, so it is left to that council (`other_council` count).
   - Northern Ireland skips postcode geography, per the Sprint 10 licence decision.
6. **Notes.** For the top 10 places per council only, one structured LLM call per council (`VENUE_DISCOVERY_*` provider settings, Gemini by default) drafts a 2-sentence dad-focused description and typical peak busy times **from the OSM tags only**. A draft is discarded (`note_rejected`) when it:
   - mentions a facility (baby changing, toilets, café, step-free access, parking, feeding room), an age band (toddlers, under-5s) or a price ("free", admission) without the matching tag;
   - vouches for the place ("safe", "vetted", "verified", "best", awards).

   Busy times are a general pattern for that kind of place, not measured data. Both notes are always `claims_status: "unverified"`. If the LLM fails or its budget runs out, the places are still kept with empty notes.

## Outputs

- **JSON array:** `review/council-discovery/<run-id>.json`, uploaded as the `council-discovery-<run>` workflow artifact. Each item has `name`, `category`, `address`, `description` and `peak_busy_times`, plus the council, `postcode` and `postcode_source`, coordinates, OSM id and URL, `claims_status`, `evidence_tags`, `rank`, `possible_duplicate_of`, `council_check` and `note_rejected`.
- **Venues** (not in dry runs), `licence = 'ODbL'`. Existing venues are never updated.
  - **Published** (owner decisions, 23 Oct, #243): every type, including attractions, castles and arts centres, goes live like the main OSM import. They get `public_visible = true`, `discovery_status = 'existing'` and no review reason. Only OSM facts reach the venue; the AI notes stay in provenance.
  - **Hidden for review**: any possible duplicate, or point whose postcode is in a neighbouring council. They get `public_visible = false` and `discovery_status = 'discovered'`, and wait in `/ops/review`. The review reason names the council, the unverified notes, any inferred postcode, any neighbouring-council postcode and any possible duplicate.
  - A new public museum or soft play centre inside an approved `/places` cohort changes that cohort, so the page drops out of the sitemap until it is re-approved.
  - The draft notes, OSM tags, postcode source and checks are kept in `venue_sources.source_payload` (`source_name = 'osm-council-discovery'`), not in venue columns, so nothing unverified becomes a venue fact.
- **Run log:** `venue_council_discovery_runs`. Each run takes the next councils without a successful run in the last 180 days (`COUNCIL_DISCOVERY_REFRESH_DAYS`). At 10 per run and two scheduled runs a day, all 350 GB councils would be **queried** within about 18 days. Since 24 Oct 2026, the Supabase timer `dadspace-council-discovery-timer` (migration `20261024120000_council_discovery_timer.sql`) also dispatches a council-only batch (`council_discovery_only=true`) every 15 minutes. That takes about a day for every council. It stops dispatching once every GB council has an ok or no_boundary run within 180 days; stop it early with `select cron.unschedule('dadspace-council-discovery-timer');`. Being queried does not mean a council has good coverage. A council whose boundary was not found is retried after 7 days.

## Why OpenStreetMap, not Google Places

Google's terms limit storing Places content beyond the place ID, and caching Google data is an owner terms decision (PRODUCT.md). OSM data is ODbL, so it can be stored with attribution ("© OpenStreetMap contributors"), and it already backs about 54,000 existing venues. Using Google here would need an owner terms review first.

## Activating it (owner steps)

1. Apply migration `20261022210000_venue_council_discovery_runs.sql`.
2. Try one council as a dry run: Actions → *Sync venue reference data* → `council = E09000009`, `dry_run = true`. Check the JSON artifact.
3. Add the source row:

   ```sql
   insert into sources (name, url, category, kind, source_role, source_adapter, active)
   values ('OpenStreetMap council discovery', 'https://www.openstreetmap.org/',
           'venue_reference', 'event_listing', 'venue_reference', 'osm_council_discovery', true);
   ```

   The scheduled loader then runs 10 councils each time. It publishes new places and inserts flagged ones hidden for review.
4. Optional repository variables:
   - `COUNCIL_DISCOVERY_PER_RUN`
   - `COUNCIL_DISCOVERY_MAX_LLM_CALLS`
   - `COUNCIL_DISCOVERY_TOKEN_BUDGET`
   - `VENUE_DISCOVERY_LLM_PROVIDER` / `VENUE_DISCOVERY_LLM_MODEL`
   - `OVERPASS_URL` (a hosted Overpass instance if the public one rate-limits)

Push-triggered dry runs never call the LLM.

## Owner decisions (22 Oct 2026, #243)

- **Northern Ireland is excluded for now.** No OSM administrative boundary carried an `N09…` `ref:gss` code, so NI would need a name-based or alternative boundary source. To include it later, remove `"N"` from `EXCLUDED_COUNCIL_PREFIXES`; the NI postcode-licence handling is already in place.
- **Libraries are not discovered** (23 Oct). The library reference source covers them (see step 2 above).

## Known limits

- Places tagged in OSM as something else (for example a museum tagged as a park) keep their OSM category.
- Busy times are typical patterns, not observations. They must never reach a public field without being rewritten and checked.

## Checks

- `tests/test_venue_council_discovery.py` runs in `places-data-checks.yml`.
- Real-data dry runs on 22 Oct 2026, without the LLM:
  - Ealing, Cornwall, Cardiff and Highland each returned 10 spots, and Belfast returned `no_boundary`.
  - After review fixes, Ealing returned 10 in-council places, with 4 boundary-crossing outlines left to their own councils.
  - Checked against live `venues`, the Ealing results match the OSM-sourced Transport Museum Depot and Pitzhanger Manor, which a live run skips as existing.
  - The first workflow dry run (22 Oct) offered Hanwell Zoo, which was already stored as `way/221351281`. The venue load paged without a fixed order and could skip rows. That is fixed by ordered paging plus the direct OSM URL check.
