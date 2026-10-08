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
- National first-page plan scanned 58,500 public records and used a top-N name/ID sort: 94.6ms execution. Preview HTTP samples: national first/deep API 0.57/0.59s, category 0.44s, text search 0.54s, nearby 0.61s; JSON payloads 9–18KB. Single samples are not percentiles. Proposed monitoring budgets for owner agreement: API p95 under 2.5s and JSON under 100KiB per 24 records; investigate regressions before adding indexes.
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

## Production rollout — 8 October 2026

Owner approved production deployment in chat. PR #54 merged as `693edc92867105ed36953764225348aa6746074f`; Vercel reports success, and the custom domain serves the new public HTML. Fresh anonymous browser reading works without a location choice. Production HTTP checks passed homepage, directory pages 1/2, Hounslow/Manchester/London pilot pages, detail routes, a hidden UUID (404), malformed routes (404) and renamed slugs (308). Production metadata is indexable where eligible; the below-threshold Manchester soft-play page remains noindex. Robots advertises the sitemap index.

The core sitemap contains 644 URLs. Sixteen venue shards contain exactly 58,500 unique URLs, matching the read-only public count, with no cross-shard duplicates, no unreleased forum routes and no tested hidden UUID. Each response is under 50MB and 50,000 URLs. The checker now examines actual URL pathnames: the legitimate `Forum Place Playground` venue must not be mistaken for the `/forum` route. It can verify an expected catalogue count and a supplied hidden UUID through environment variables.

At 390px/DPR 1, a 128px category tile selected a 256px WebP response (quality 60, 12,152 bytes, encoded 256×143). Observed srcset candidates 384/640 also returned valid WebP variants (24,138/50,070 bytes). These candidates correspond to expected DPR 2/3 selection from `sizes=144px`; actual browser selection at DPR 2/3 remains unmeasured because the available viewport control exposes dimensions only. Offscreen tiles remain lazy. No 3840px tile request was observed.

Publication eligibility is the existing canonical `public_visible` policy. The later read-only status snapshot is 55,568 public `existing`, 2,932 public `verified`, and 592 hidden `discovered`; this release does not claim a new human verification of 55,568 historical records. Keep historical quality remediation in #34 and upstream publication/review guarantees in #33.

The latest-20 news record audit and the additional homepage selections are recorded in [news-seo-audit-2026-10-08.md](news-seo-audit-2026-10-08.md). Every sampled stored URL points directly to a publisher. Editorial correctness/approval remains #35; stored relevance scores are not independent verification of a report's claims.

Three production homepage and directory PageSpeed runs are captured separately for mobile and desktop. Homepage median performance is 94 mobile / 99 desktop; median mobile LCP 3.0s, TBT 30ms, CLS 0.001. Directory median performance is 97 mobile / 100 desktop; median mobile LCP 2.6s, TBT 10ms, CLS 0.001. These are Lighthouse 13.5.0 lab results on the initial-load Moto G Power/slow-4G profile, not CrUX p75 values or INP. No CrUX data is available. Exact per-run links and pilot results are attached to #53. No reproducible pre-release production PageSpeed baseline was obtained because the initial domain-resolution/API-quota measurements failed; do not invent a before/after improvement percentage.

Pilot diagnostics identified a skipped heading level (H1 directly to card H3); add a results H2 for accessible structure. Detail share images should use matching category art when no licensed photo exists. Remaining measured diagnostics include image savings/unused JavaScript, brand-text contrast, and lab LCP render delay. The sampled slow category run's LCP element is its introductory paragraph, not a tile; prioritising additional images is not a justified fix for that finding.

Remaining acceptance: actual DPR 2/3 selections, agreed latency/payload budgets and query plans for additional filters, external schema validation, Search Console property-owner inspection/sitemap evidence, and historical/editorial quality decisions. Field observation continues when CrUX data exists. Keep #53 open until these are recorded or explicitly resolved; deployment alone does not check every acceptance box.

## Preview delivery evidence

PR #54 implements the public rendering, canonical routes, sitemap shards, launch flag and truthful source-backed states. GitHub checks run the production build, TypeScript and 22 regression tests. Removing the root loading boundary and blocking metadata for every user agent preserves 404/308 before headers are committed; this is identical rendering policy for users and bots, with a possible first-byte latency tradeoff.

Raw HTTP checks passed for homepage, national pages 1/2, three pilot category pages, a venue detail, hidden UUID 00f58c41-e2d4-4a34-b09b-24d0fb85aab7 (404), invalid routes (404), and renamed readable slug (308). Actual HTML has one H1, canonical links, valid JSON syntax in schema scripts and preview noindex. API page 2 matches HTML page 2 IDs and has no page-1 overlap. Preview sitemaps intentionally contain no venue URLs: production catalogue traversal remains a post-release check, not a claimed preview pass.

Manual Hounslow lookup and nearby results succeeded in the browser. The public catalogue remained available before selection; the automated denied-geolocation and visibility-revocation fixtures passed. At 390px/DPR 1, category images render at 128px and selected 256px optimizer URLs, with offscreen images lazy. The browser viewport capability cannot set DPR; actual DPR 2/3 and independent-session browser checks remain outstanding.

One pre-compression preview homepage lab run: [PageSpeed report](https://pagespeed.web.dev/analysis/https-dadspace-git-codex-53-public-disc-1de796-imransinvestments-6859-vercel-app/wqz1uxdcfd?form_factor=mobile), captured 8 October 2026 13:52 BST, Lighthouse 13.5.0, initial-load Moto G Power/slow 4G. Mobile performance 92, FCP 0.9s, LCP 3.2s, TBT 0ms, CLS 0.001; desktop performance 98, FCP 0.2s, LCP 0.7s, TBT 10ms, CLS 0.024. No CrUX data. SEO 69 reflects deliberately blocked preview indexing. These are single-run preview diagnostics, not production before/after medians or a field pass.

That run found 126KiB potential image savings and a 404 for the obsolete dwin2 script. Image quality 60 is explicitly allowed and used for the hero/category art; the broken script is removed. Venue attribution and affiliate offer disclosures remain. Repeat measurements on the final deployment; contrast and unused-JavaScript diagnostics remain visible follow-up work.

## Final acceptance evidence

PR #55 shipped the missing results H2 and category-matched detail share artwork. The final HTTP/sitemap verifier passed on a9ca6d7cfbb73fa428ad83622ee54edc022a9f8e. [The production PageSpeed report](pagespeed-production-2026-10-08.md) records all 24 device results across four representative routes, conditions, exact links and remaining diagnostics.

Google Rich Results Test successfully crawled the Hounslow Library detail with three valid items (breadcrumbs, Library/local business, organisation). Optional telephone, priceRange and image warnings remain unknown rather than invented. This is sampled validation, not an audit of every existing event/activity page. Search Console access is unavailable in the current account; property-owner URL Inspection and sitemap evidence are required.

Owner accepted monitoring budgets on 8 October: API p95 below 2.5 seconds; JSON below 100 KiB per 24 venue records. Single latency samples do not establish p95. The national deep-page EXPLAIN (offset 58,000, limit 24) took 549.6ms and scanned 58,500 public rows with an external merge sort (4,144KB disk). Retain first/deep/filter measurements before deciding index or paging changes.

The follow-up feed contract marks missing configuration, returned query errors and thrown transport failures as loadFailed. Successful empty supply or relevance-filtered supply is a genuine empty state. Publisher source and URL remain attached to eligible articles. Regression coverage exercises all five outcomes without writing production data.
