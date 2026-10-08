# Production launch — 8 October 2026

The owner approved releasing the integrated MVP and replacing the holding page with the homepage.

Release candidate is based on testing commit `8e8ec4bc52d13251ba92e03071128652133ab766`, containing all current main changes, the homepage and Local Places reel, nearby events/activities, article summaries, shared live deals, rules-only deal collection, reviewed Shopify sources, AWIN integration, news locality and Vercel analytics.

`COMING_SOON=false` enables the homepage and ordinary routes. The production location provider is retained: each browser session starts with location permission, and users can select a destination afterwards. The preview's hardcoded TW4 postcode is not used in production.

The staged `news_locality.sql` is applied as part of this release after inspecting the live view, column order, table RLS and grants. Public clients retain SELECT access to the filtered feed; mutation privileges are revoked. No article backfill or deletion is required. The live view already contains primary-story filtering and geographic columns; the permission correction completes the staged release.

The integrated regression suite and production build passed on testing. Branch checks repeat the offline suite and build for the release candidate and main. Vercel deploys main to production; successful deployment and live page/API checks establish the final release result.

This release supersedes the pending-production statements in earlier testing, Shopify and news-locality release notes. Their historical test evidence and operational limits still apply. Architecture/operations documents dated 5 October are historical; see the [testing integration corrections](mvp-testing-integration-2026-10-08.md#documentation-baseline) for current ingestion and read behavior.

Rollback: revert the launch/release commit if needed, or set the launch flag true for a deliberate hold. Keep additive news columns, primary-story filtering and public read-only permissions. Sources use the shared database; reverting application code does not undo collector writes or disable sources.
