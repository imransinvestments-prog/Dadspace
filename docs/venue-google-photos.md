# Google Places venue photos

The bulk script searches all categories in `public.venues`, validates the venue
name and UK location, and adds a Google place ID for missing photos. It excludes
all playground categories before any billable request and preserves
existing Wikimedia photos and skips ambiguous results, unnamed venues, closed
businesses and distant branches. Coordinates must be within 300 metres (2 km for
large parks/zoos); without coordinates an exact postcode is required. Searches
use coordinates as a location bias and a concise name/postcode query. A Google
Maps URL containing an explicit place ID is resolved directly, with location
verification. Official website URLs are compared with Google's website field:
an exact branch path can identify a renamed venue, while a shared chain homepage
still requires name and location evidence. Arbitrary website URLs are not treated
as Google place IDs or scraped for unverified photos.

The `websiteUri` field is requested only for records with an eligible website.
Google bills these lookups at the corresponding higher field tier; the request
cap still applies. Reports record the match method and rejection reasons, so a
low match count can be diagnosed without repeating the entire batch.

Google photos are retrieved only when a public venue card enters the viewport.
The server fetches fresh photo metadata, a current photo URL, the direct source
photo link and author attributions. API keys stay server-side. Photo names, image
URLs and author metadata are not saved to the database or a persistent cache.
If Google is unavailable or the place has no photo, category artwork remains.
Matching a place therefore does not guarantee a photo for every venue.

## Configuration

Set these in a private local `.env` file and in the hosting server environment:

* `GOOGLE_PLACES_API_KEY` (Places API New enabled; server key).
* `NEXT_PUBLIC_DADSPACE_SUPABASE_URL`.
* `DADSPACE_SUPABASE_SERVICE_ROLE_KEY` (never a NEXT_PUBLIC variable).

The CLI also accepts the existing workflow aliases `SUPABASE_URL` and
`SUPABASE_KEY`, and Explorehalal's `GCP_API_KEY_2`/`GCP_API_KEY` aliases.
Google lookup and photo requests are billable; set Google Cloud quotas/budget
alerts before running large batches or enabling photo serving. Publish Terms
of Use and Privacy Policy incorporating Google's required terms before launch.

## Run

For a browser-only run, open GitHub Actions → **Match missing venue photos with
Google Places** → **Run workflow**. Leave the limit at 100 for the initial batch.
Set `GOOGLE_PLACES_API_KEY`, `SUPABASE_URL` and `SUPABASE_KEY` as repository
secrets first. The Google key must also exist in Dadspace's hosting environment
for cards to resolve their photos. The workflow only runs manually and downloads
an ID-only report as an artifact. It never prints credentials.

```sh
pnpm install --frozen-lockfile
node --env-file=.env.local scripts/backfill-venue-photos.mjs --limit=100 --max-api-calls=100
node --env-file=.env.local scripts/backfill-venue-photos.mjs --apply --limit=100 --max-api-calls=100
```

The first command previews decisions; only `--apply` writes image fields.
Both use billable Text Search calls. Reports contain venue IDs, place IDs and
decisions only. A write uses `image_url IS NULL` to preserve concurrent changes.
`--limit` caps rows inspected; `--max-api-calls` separately caps billable searches.

Use the final `resumeAfter` value as `--after=<UUID>` on the next batch, with the
same report path. After previewing, omit `--after` when applying that preview's
range. On quota/credential errors the script stops before advancing the failed
row. Network/database failures also stop rather than silently skipping records.

For a full pass, deliberately set both caps high enough for your table after
checking costs. Completed rows with photos are skipped on future runs. To revisit
unmatched records later, start without `--after`.

The database stores `google-places:<place-id>` in `image_url`; this is a provider
reference, not a remote image address. The updated VenuePhoto component resolves
it through `/api/venues/<venue-id>/photo`. Deploy the UI before applying the bulk
updates. No schema migration is needed.

## Verification

```sh
node scripts/test-google-venue-photos.mjs
node scripts/test-venue-photo-backfill.mjs
node --experimental-strip-types scripts/test-venue-images.mjs
pnpm exec tsc --noEmit
pnpm build
```

References: https://developers.google.com/maps/documentation/places/web-service/place-photos
and https://developers.google.com/maps/documentation/places/web-service/policies
