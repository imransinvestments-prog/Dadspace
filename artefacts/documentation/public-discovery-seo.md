# Public discovery SEO — ticket #53

## Architecture decision

The public catalogue renders in Next.js server components. Location selection is optional and adds nearby ordering through the existing API; it never replaces public content. Do not detect crawlers or serve a separate bot experience.

`lib/venue-discovery.ts` reads the existing canonical venues table with an explicit public projection and `public_visible=true`. React cache deduplicates identical reads within a request, not across visitors. Public discovery routes deliberately use dynamic rendering while publication/removal handling is established: a fresh request sees a visibility change immediately. No new database, schema, source or service was introduced. Existing service-role access stays server-only; its public visibility predicate is mandatory because that role bypasses RLS. Personal API responses remain private/no-store.

Venue URLs contain a readable name and immutable UUID. A renamed record redirects to its current slug. Unpublished/deleted/unknown IDs return 404; operational failures throw instead of masquerading as missing records. The existing venue-review workflow remains responsible for merge redirects; a deleted old ID currently returns 404 rather than inventing a replacement.

The curated pilot is Hounslow, Manchester and London × libraries, museums and soft play. Only combinations with at least three published records are linked/indexable. This is an editorial pilot, not an all-town/category Cartesian product. Broader validation of historical directory rows remains #33/#34; public visibility is not a claim that every historical venue has received a new human review.

The venue first page contains 24 public projections and seeds the existing client pagination. Normal browse pages also expose HTML next/previous links. Search/filter variants are noindex; arbitrary location coordinates do not enter canonical discovery URLs. `VERCEL_ENV=preview` stays noindex even during a production build.

The sitemap index points to the core sitemap and 16 disjoint UUID-prefix venue shards. Each shard uses ordered keyset batches of 1,000; no default database response cap silently truncates the catalogue. Shards enforce 50,000 URL / 50MB limits and fail visibly if splitting is required. Venue lastmod is omitted because the current table has no authoritative content-update timestamp. Core event/activity coverage retains the existing scope; full expansion of those catalogues is separate work.

## Verification baseline — 8 October 2026

- Production main baseline: `15d8250295e343e27e1be8d46ceb8a46589f5a2f`.
- Browser reached the custom domain and showed only the location screen in a fresh session. Subsequent HTTP access returned 200; venue HTML was 467,015 bytes despite the gate. Initial shell failures therefore did not establish a public outage.
- PageSpeed Insights UI accepted the homepage URL and returned **Unable to resolve https://www.dad-space.co.uk/**. Its API separately returned HTTP 429 / RESOURCE_EXHAUSTED for the unauthenticated quota. These are failed measurements; no score or CWV result is claimed. Repeat the UI test after rollout; attach exact failures if Google still cannot resolve the host. Do not change working DNS based solely on this result.
- DNS observed: www CNAME to `1e96257083513e22.vercel-dns-017.com`; apex A `216.198.79.1`. Browser and HTTP reachability work.
- Read-only database count: 58,500 public-visible / 591 hidden records. Sixteen UUID shards contain 3,479–3,744 rows each and sum to 58,500.
- Pilot supply: Hounslow libraries 11; Manchester museums 30/libraries 28; London museums 272/soft play 28. Manchester soft play has one, so its page is noindex and omitted from discovery links/sitemap. London libraries and Hounslow museums/soft play have no eligible supply in the audited query.
- Hounslow/library first-page EXPLAIN used `venues_town_city_idx`, 11 rows, about 20ms execution. No index was added without evidence.
- Latest 20 news records have direct publisher URLs, not Google News wrappers. Existing `news_links.py` performs upstream resolution with original-link fallback. No public-render redirect resolution was added. No article accuracy or current publisher availability is inferred from the stored URL alone.
- Editorial audit: IDs 471 (parent rights), 490 (Child Benefit), 465/468 (child product safety), 374 (school readiness) and 378 (safeguarding) have strong family utility; other sampled stories have broader/area-specific relevance (score 3). Homepage now selects existing relevance ≥4, prioritises strongest evidence and does not pad with weaker stories. Safety stories have a sensitive-topic label and a distinct news section separated from the joke area. This is an agent assessment of stored summaries, not human editorial approval or medical/legal advice.

## Release verification and operations

1. Run TypeScript, production build, `node --test tests/venue-seo.test.mjs tests/public-discovery.test.cjs tests/deals-selection.test.mjs`.
2. Run `DADSPACE_CHECK_URL=<deployed origin> node scripts/check-public-discovery.mjs`; retain JSON alongside ticket evidence. Inspect raw visible HTML, canonicals, JSON-LD and no-JS reading, including venue/town/category pages and next-page links.
3. Use two fresh browser contexts for manual locations, denied/unavailable geolocation and location changes. Confirm no previous-location cards survive a change. Confirm navigation, anonymous reading and authenticated actions retain expected behavior.
4. Inspect mobile at 390px and DPR 1/2/3: category tiles are 128–144px with `sizes=144px`; record `currentSrc`, network bytes, encoded width and layout. Offscreen images stay lazy; only measured LCP assets should be prioritised.
5. Check hidden UUID reads and a reversible publication/revocation fixture in an isolated environment; hidden UUIDs must not appear in pages, JSON-LD, endpoints or sitemaps. No production data should be changed merely to run this test.
6. Capture three mobile/desktop PageSpeed or equivalent Lighthouse runs per representative route; attach medians and exact URLs/commits. Distinguish lab LCP/CLS/TBT from CrUX p75 LCP/INP/CLS. Field targets are LCP ≤2.5s, INP ≤200ms, CLS ≤0.1. No field-data availability means no immediate field pass.
7. Attach Search Console URL Inspection and sitemap evidence when property access is available. Indexing and ranking are observations, not guaranteed acceptance outcomes.

Rollback: revert the delivery PR and redeploy the previous production commit. No database rollback is required. Keep community disabled until its feature/moderation acceptance. Monitor public route status, sitemap counts/errors, query latency and broken external links. Removal SLA for a fresh dynamic response is immediate after the canonical visibility update; already-open browser pages may remain until navigation/reload.

Ticket #53 stays open until deployment/live checks and recorded outstanding acceptance decisions are complete. Preserve PageSpeed failures honestly rather than manufacturing a score.
