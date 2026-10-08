# MVP testing integration — 8 October 2026

Branch: `codex/mvp-testing`. Starting head: `a0e5327`.
Main baseline included: `9876fea`.

## Added in this integration

| Change | Source | Testing status |
| --- | --- | --- |
| Architecture, data flows, worker roles and operations | PR #45, head `8aca16a` | Merged into testing |
| Locality-aware news filtering and classification, ONS geography validation and regression checks | PR #27, head `492c779` | Merged into testing; production SQL remains staged |
| Vercel Web Analytics | PR #19, head `e3b9bf7` | Merged into testing; newer layout and AWIN tag retained |

The existing Speed Insights integration is retained. PR #8's implementation is already present; an old open PR does not establish a missing feature.

## Previously included in testing

- All current main developments, including stronger family-deal evidence and source checks (#46), one strongest offer per item type (#47), original publisher news links, session location changes, identifier-first venue photo matching, public library reference imports, event/activity collection and NCT loading.
- Testing homepage: Local Places reel, news cards with summaries, nearby weekend events, recurring activities and shared live deal selection.
- Rules-only parent-value deals processing, canonical taxonomy, source-health monitoring and reviewed source data.
- AWIN activation/integration and Publisher MasterTag (#49 merged into testing), plus read-only baby advertiser/offer discovery trials.
- Reviewed Shopify merchant sources and eight-category coverage evidence, including variant age, GBP currency, stock, delivery and value checks, with bounded retries for transient server errors.

## Release boundaries

This integrates code into testing, not main. Existing production PRs remain open and retain their release decisions. No SQL, collector dispatch or database write is performed by this integration.

`COMING_SOON=false` and the preview's saved test location remain testing-specific. Main retains its launch gate. News locality's corrected `news_locality.sql` is not applied here; see [release notes](news-locality-release.md) for the primary-only feed and production approval requirement. Analytics ingestion also depends on deployment and the Vercel project setting.

## Documentation baseline

The imported architecture, data-flow and operations documents describe the historical main baseline from 5 October. For this testing branch, the following supersede their older statements:

- The homepage uses live deals through `lib/deals.ts`, with shared quality, freshness and item diversity selection; sample content can remain in other fallback sections.
- `news.yml` uses `news_worker_locality.py`, wrapping the existing worker with conservative geographic classification. The client filters supported district/county/region evidence and retains legacy nation fallback.
- The two-day UK-time orchestration starts deals independently from the gate. News → civic → activities remains a success-dependent chain; venue references are independent.
- The testing app is enabled; the production holding-page description applies to main.
- Deals collection includes reviewed direct/Shopify sources and AWIN handling. No paid model call is assumed required for the rules-only deals path.

## Validation

- 67 Python deals/AWIN/Shopify regression tests passed.
- Nine Python news locality tests passed.
- Frontend/API news locality regression checks passed.
- All 16 JavaScript deal-selection tests passed.
- TypeScript `tsc --noEmit` passed locally.
- The local production build stopped before app compilation because Windows denied native SWC access to the checkout's canonical path. Local dependencies were reused from the prior checkout after sandbox realpath/symlink errors prevented a fresh pnpm install; GitHub checks perform the authoritative frozen-lockfile install and production build.

`.github/workflows/mvp-testing-checks.yml` runs these offline regression checks and a production build on testing-branch pushes without database secrets or collector execution. Its result is recorded in the final delivery summary. Database and live-feed rollout are separate from these checks.
