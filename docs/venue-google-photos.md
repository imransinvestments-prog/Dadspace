# Google Places venue photos

The bulk script enriches missing venue photos without using venue names as the primary identity signal. It excludes all playground categories before any billable request, preserves existing Wikimedia/open-licensed images, and skips ambiguous, closed or geographically inconsistent results.

## Identifier-first matching

Matching priority is deliberately based on concrete venue identifiers:

1. **Explicit Google Place ID** extracted from `google_maps_url`, `maps_url`, or an eligible Google Maps URL already stored in a venue URL field. The Place ID is resolved directly and still checked against location evidence where available.
2. **Coordinates + postcode**. For rows with coordinates, the worker performs a Nearby Search centred on the stored latitude/longitude. Normal venues must be within 150 m; large destination venues such as zoos/theme parks may use a wider tolerance. An exact postcode match provides additional confirmation.
3. **Coordinates only**. A very close Google result can be accepted when the Google postcode is absent, provided the result has an expected venue type and is the only viable match.
4. **Postcode only**. When coordinates are unavailable, an exact postcode match plus venue type is required.
5. **Official branch website** is only a tie-breaker between otherwise valid identifier matches. A shared chain homepage is never enough to identify a branch.

Venue names are not used to decide whether a candidate is the same place. This avoids false negatives caused by abbreviations, renamed venues, punctuation differences and inconsistent source naming. Names remain display data only.

The worker requests Google place `types`/`primaryType` and uses Dadspace category-to-place-type mappings (for example library → `library`, museum → `museum`/`art_museum`/`history_museum`) to avoid attaching a nearby but unrelated business. Google Nearby Search supports Table A place-type filters. Ambiguous nearby matches are recorded as `ambiguous` for review rather than choosing the first result.

## Search behaviour

Rows with valid coordinates use Places API Nearby Search with a 2.5 km discovery radius and distance ranking. The final acceptance radius is intentionally much tighter than the discovery radius. Rows without coordinates fall back to Text Search using category + postcode/address rather than a venue-name query.

The `websiteUri` field is requested only when a venue has an eligible official website because it can be used as a branch-level tie-breaker. Reports record only Dadspace venue IDs, Google Place IDs, match methods and rejection reasons; Google names, photo resources and API payloads are not persisted.

## Photo delivery and licensing

Google photos are retrieved only when a public venue card enters the viewport. The server fetches fresh photo metadata, a current photo URL, the direct source-photo link and author attributions. API keys stay server-side. Photo names, image URLs and author metadata are not saved to the database or a persistent cache.

Existing venue images are never overwritten. The intended fallback order is therefore:

1. existing open-licensed/Wikimedia image;
2. verified Google Places venue photo reference;
3. Dadspace category artwork when no verified venue-specific photo is available.

Arbitrary Google Search images or third-party website photos are not scraped or copied. This avoids copyright and attribution problems while still providing broad venue coverage through the Places photo service under Google Maps Platform terms.

## Configuration

Set these in a private local `.env` file and in the hosting server environment:

* `GOOGLE_PLACES_API_KEY` (Places API New enabled; server key).
* `NEXT_PUBLIC_DADSPACE_SUPABASE_URL`.
* `DADSPACE_SUPABASE_SERVICE_ROLE_KEY` (never a NEXT_PUBLIC variable).

The CLI also accepts the existing workflow aliases `SUPABASE_URL` and `SUPABASE_KEY`, and Explorehalal's `GCP_API_KEY_2`/`GCP_API_KEY` aliases.

Google lookup and photo requests are billable. Set Google Cloud quotas/budget alerts before running large batches or enabling photo serving. Publish Terms of Use and Privacy Policy incorporating Google's required terms before launch.

## Run

For a browser-only run, open GitHub Actions → **Match missing venue photos with Google Places** → **Run workflow**. Leave the limit at 100 for the initial batch. Set `GOOGLE_PLACES_API_KEY`, `SUPABASE_URL` and `SUPABASE_KEY` as repository secrets first. The Google key must also exist in Dadspace's hosting environment for cards to resolve their photos. The workflow only runs manually and downloads an ID-only report as an artifact. It never prints credentials.

```sh
pnpm install --frozen-lockfile
node --env-file=.env.local scripts/backfill-venue-photos.mjs --limit=100 --max-api-calls=100
node --env-file=.env.local scripts/backfill-venue-photos.mjs --apply --limit=100 --max-api-calls=100
```

The first command previews decisions; only `--apply` writes image fields. Reports contain venue IDs, Place IDs and decisions only. A write uses `image_url IS NULL` to preserve concurrent changes. `--limit` caps rows inspected; `--max-api-calls` separately caps billable searches.

Use the final `resumeAfter` value as `--after=<UUID>` on the next batch, with the same report path. After previewing, omit `--after` when applying that preview's range. On quota/credential errors the script stops before advancing the failed row. Network/database failures also stop rather than silently skipping records.

For a full pass, deliberately set both caps high enough for your table after checking costs. Completed rows with photos are skipped on future runs. To revisit unmatched records later, start without `--after`.

The database stores `google-places:<place-id>` in `image_url`; this is a provider reference, not a remote image address. The VenuePhoto component resolves it through `/api/venues/<venue-id>/photo`. No schema migration is required for this matcher change.

## Verification

```sh
node scripts/test-google-venue-photos.mjs
node scripts/test-venue-photo-backfill.mjs
node --experimental-strip-types scripts/test-venue-images.mjs
pnpm exec tsc --noEmit
pnpm build
```

References: Google Places API Nearby Search, Place Types, Place Photos and Google Maps Platform policies.
