# Sprint 7 — implementation and verification

17 October 2026. [Tracker #187](https://github.com/imransinvestments-prog/Dadspace/issues/187), [PR #188](https://github.com/imransinvestments-prog/Dadspace/pull/188). Current consolidated recommendations are in [sprint-7-decisions.md](sprint-7-decisions.md).

## Implemented

Owner-protected Deals desk: exact public offer membership, canonical aliases/groups, stock/expiry/value/comparison evidence, merchant/affiliate readiness and Deals audit history. Bounded 20-row paging; unknown and unavailable states explicit. Owner-only policy unchanged; registration grants no Operations access. Source pause/activate/restore reuses shared signed intent, atomic audit, concurrency/stale guards and readback. Preview writes remain disabled.

Coverage artefacts map 932 canonical items, 294 active, 308 active/priority rows. The baseline selector's 17 offers preserve the accepted Sprint 5 material evidence.

Approved Natural Baby Shower route released separately in PR #189, source #42 activated through production signed maintenance, normal collector run 39070828554 succeeded, deal #1994 verified in production. Actual allowed activation/audit/readback workflow is established; no repeat live experiment required.

Matalan #190: one-product / one-size public adapter with 6 MB bound, strict URLs, no redirects or JavaScript execution, variant JSON plus JSON-LD corroboration, delivery/promotion validation, conservative campaign cutoff and independent exact re-fetch. Normal classifier maps to existing canonical #160. Read-only trial kept one offer with zero writes and zero AI. One new owner content decision, plus its concrete source route and code release, remain requested together. The accepted car seat remains visible for context.

## Checks completed locally

- Full Node regression: 177 passed, zero failures.
- Full Python discovery: exit 0, including six new Matalan tests and existing Shopify/collector regression.
- TypeScript: passed.
- Production build: passed with webpack. Hosted deployment uses its normal configured build.
- Fourteen focused Deals/maintenance/access checks passed, including real PostgreSQL-compatible atomic pause/stale/idempotency/restore rehearsal.
- No standalone lint script configured; diff whitespace reviewed. No new credentials, paid service, account changes or broad URL fetching.

## Hosted review

The previous hosted session verified owner sign-in, 17 displayed offers, alias filtering, empty audit state, disabled preview apply, source decision preview and invalidation after editing the record. Owner accepted workspace usability. New uniform snapshot and final hosted checks are pending deployment of this update; record their results below before recommending release.

## Remaining gates

1. Final hosted tests and deployed browser review of the new Matalan snapshot.
2. Owner's single new offer / source-route / release decision pack.
3. After approval, fresh Matalan validation, audited source registration/activation, normal collector and public readback. Do not count the trial as publication.
4. Account-side AWIN MasterTag investigation: exact owner-confirmed URL still 404. Official publisher documentation confirms format; no replacement URL guessed or plugin activated. #131 remains open until actual delivery is established.
5. #132/#125 scheduled observation: known dispatch misses remain failures, manual runs do not count and no seven-day window is accepted. Outside Sprint 7 delivery points.
6. Sprint review after release/acceptance; retain unaccepted feature criteria explicitly.

Committed 21 / accepted whole features 0 / remaining 21. No ticket closed in this implementation checkpoint.
