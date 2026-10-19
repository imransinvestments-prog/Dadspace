# Sprint 10 — geography development review

## Current release status — 19 October 2026

Owner accepted all review-pack decisions and then explicitly authorised production release. PR #208 merged as `5b0a5258d8dbfc2e5e929b74d2c347d6166699b1`; Vercel production deployment succeeded. Live `/ops/geography` was verified in the existing signed-in owner session, showing the reference, sample table and licence gates. Anonymous requests receive 307 to login without reference data. Homepage, Places, Activities, Events and W3 postcode lookup passed live readback. The follow-up release record updates the page's proposal labels to approved/released, without changing reference data or public selectors.

Approved: reference structure, initial 30-case scope, NI data withholding, quarterly manual checking, evidence-led future targets and staged database rollout. NI commercial data rights remain unresolved; numeric national quality targets are not invented. No production geography schema/seed import, source activation or postcode lookup cutover occurred. Manual content/browser checks are retained below and are not asserted individually completed by the owner's general decision approval. #206 remains post-release observation; #207 remains national expansion. Earlier development-only and pending-review text below is preserved as the original review pack, superseded by this release status.

Tracker: [#202](https://github.com/imransinvestments-prog/Dadspace/issues/202). Stories: reference #203 (5), test pack #204 (5), coverage workspace/review #205 (5). **15 provisional delivery points; zero accepted so far.** This is a separate sprint from #197. Engineering is staged on `dev/geographic-coverage`; stop for owner testing before merge or production. Estimates describe relative effort and uncertainty, not an optimal velocity or fixed completion date.

## What you can review

Open **`/ops/geography`** on the development preview and sign in with the existing owner account. Operations links to the workspace. It is read-only, owner protected and noindex. Filter the sample by nation; search the official council catalogue; inspect visible supply versus empty, unavailable and licence-blocked cases; review the decisions below. The page reads committed snapshots, not a production geography database. The local development database is real but separate, and its connection status is not misrepresented by this page.

The reference contains **361 councils, 4 nations, 9 English regions and applicable administrative counties** from the app's existing pinned ONS May 2026 lookup (395 administrative areas overall). The separately linked postal hierarchy is generated from **28 verified Great Britain postcode samples**. The frozen 30-location manifest also contains two NI postcode cases whose geocodes were not requested, stored or imported. Postal points are representative locations, not property coordinates or precise boundary membership. Keep the original W3 9LN / 10 km / ages 0–5 pilot unchanged.

The initial live API baseline was captured against `https://www.dad-space.co.uk`, before this feature's release. All 28 GB location lookups passed; 28 samples returned venues, 10 returned Activities, and 6 returned Events. The other successful Activity/Event requests returned empty arrays. Venue first-page counts are lower bounds; Event completeness is not established. These are point observations through existing public selectors, **not** reviewed age suitability, fresh actionable supply, complete council inventories or nationwide launch acceptance. NI requests were not made. National Deals are observed separately; News locality and Originals content retain explicit manual review rather than fabricated per-council counts.

## Decisions for Imran

| Decision | Concrete proposal | Effect now |
|---|---|---|
| Area model | Official codes and release-scoped relationships; administrative ancestry separate from postal area/district/sector/unit | Development reference only; existing location/news APIs unchanged |
| Sample size | Start with 30 deliberate locations; all nine English regions, Scotland/Wales, explicit NI blocks, cities, smaller/rural destinations, coastal/island and border-vicinity cases | A regression sample, not a statistical national coverage claim |
| NI data | Keep public ONS administrative codes/names; withhold postcode geocodes until a valid commercial data licence or authorised alternative is recorded | No purchase, restricted-data import or silent omission from the review |
| Reference refresh | Propose a quarterly manual release check with edition, licence, hash and compatibility validation | No new scheduled collector or refresh job enabled |
| National content thresholds | Agree after reviewing the baseline and source quality; retain current pilot criteria | No invented target, automatic ranking or source activation |
| Rollout | Review dev first; later stage an approved reference import/cutover independently of public content collection | No production migration/import, deployment, merge or source-table change |

Postcodes.io documents that commercial NI postcode use requires an NI Land & Property Services licence: [licences](https://postcodes.io/docs/licences/). GB attribution is retained in the reference, database provenance and review page. Administrative source: [official ONS lookup](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/WD26_LAD26_CTYUA26_RGN26_CTRY26_UK_LU/FeatureServer/0), Open Government Licence v3.0. This development pack does not resolve the app's pre-existing provider-wide licensing arrangements.

## Test steps

1. Sign in as the owner; open `/ops/geography`. Confirm the reference scope, frozen observation time and 28 qualified / 2 blocked split. Filter Northern Ireland and confirm no empty/green result is substituted for the licence block.
2. Search a council by official code and name, including a Scottish, Welsh and Northern Irish council. The UK council catalogue should remain available even where postcode tests are blocked.
3. In the normal app, choose W3 9LN and then a verified Scottish/Welsh postcode from the pack. Check label, distances, results and persistence after refresh. Start another browser session and confirm no previous visitor location is inherited.
4. Deny geolocation permission and choose a postcode manually. Verify invalid input, clear lookup-unavailable messaging and an honest empty area. These browser flows are manual acceptance; helper/route tests do not mark them reviewed.
5. Inspect a populated Activities/Events sample. Review source/detail and booking links, ages, regularity, occurrence dates and venue location. A returned listing is not automatically suitable for ages 0–5.
6. Check News nation/local selection, national Deals and Originals, keyboard navigation and mobile layout. The automated pack preserves current news mappings and radius boundary behaviour; content judgement is yours.

## Reproduce the development database and checks

Use the repository's Node/Python dependencies; no production database environment variables are needed:

```powershell
python scripts/geography_catalogue.py
node scripts/build-geography-dev-db.mjs
python -m unittest discover -s tests -p 'test_geography*.py' -v
node --test tests/geography-database.test.mjs tests/geography-features.test.cjs
pnpm exec tsc --noEmit
pnpm build
pnpm dev
```

The first command produces `review/geography-seed.sql`; the second creates/preserves the PostgreSQL-compatible local database in `review/geography-dev-db` and writes `review/geography-dev-db-status.json`. Identical release imports are idempotent; changed content requires a new release ID. Schema changes during development require a fresh disposable catalogue, not a silent change to a previously installed one. Nothing connects this command to Supabase production.

The additive migration is `supabase/migrations/20261018224639_uk_geography_reference.sql`. Tables store release provenance/hash, administrative/postal areas/relationships and postcodes. Public roles have no access; the service role is read-only; administrative imports are transaction-bound, versioned and immutable. Invalid hierarchy/council/nation/sector mappings and BT postcode rows fail. The empty-installation inverse refuses to delete any imported history. For a future production rollback, revert the app/cutover and retain historical releases; do not run a destructive inverse on populated data.

The streaming `read_onspd` adapter parses a supplied, filtered GB ONSPD CSV and preserves termination months. It is a tested foundation, **not** a complete national acquisition/resumable import service. Broader sampling, full importer/resource limits, licence readiness and national-scale qualification are #207, outside this sprint.

To capture another bounded read-only snapshot without changing the committed baseline:

```powershell
python scripts/check_geography_coverage.py --base-url https://YOUR-DEV-PREVIEW --output review/geography-dev-observation.json
```

It runs at most two locations concurrently, no retries/challenge handling, and at most 113 ordinary public API reads for the full GB sample plus national Deals. It records centre/radius/time/status/completeness and does not reclassify counts as content quality. A frozen report is tied to the logical manifest hash and reference release; mismatch withholds the report. An unauthenticated protected preview may return unavailable—do not relabel that as empty content or bypass deployment protection.

## Delivery, observation and remaining scope

Execution plan and ECC adversarial-review refinements: `plans/sprint-10-geography.md`. Dedicated checks include actual PostgreSQL 17 in disposable CI, PostgreSQL-compatible local schema/permission/inverse tests, reference/CSV validation, existing location/news handlers, radius rules and protected page access/rendering. No linter is configured in this repository; type/build/tests/diff review provide the relevant checks rather than an invented lint pass.

#206 is identified before release and belongs to the **next sprint after approved release**: record exact reference/pack/release boundaries, compare after at least two normal scheduled collection cycles, retain failures and unknowns, and validate a reference refresh in isolation. #207 is uncommitted national expansion. Their points are not included in Sprint 10 and manual API snapshots cannot satisfy their scheduled criteria.

Sprint 9 Activities identity/canonical/NCT work and #134 Ealing/Merton access remain separate. No previous observation window is restarted by this dev work. No production postcodes, visitor locations, listings, sources, providers or paid-service settings were changed. Owner acceptance and any release remain pending.

Verification also exposed #209, an existing Matalan test that used two different clocks and failed when the real review cutoff passed. Its fixture now fixes both clocks and verifies expiry at the exact cutoff. This is a test-only readiness repair, with no production date extension or extra sprint points.
