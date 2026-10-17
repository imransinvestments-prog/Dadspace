# Sprint 7 — implementation and evidence

17 October 2026. Tracker: [#187](https://github.com/imransinvestments-prog/Dadspace/issues/187). This is progress, not acceptance or release approval.

## Coverage baseline

The read-only database snapshot contains 932 canonical items, 294 active items and 25 configured sources. The reproducible coverage report maps all active items and the bounded priority inactive set (308 rows). Item/source history, configured candidate routes and current displayed supply are distinct facts.

The exact public selector replay at the snapshot's latest verification time returns 17 offers across seven public groups. Those groups are not the five priority categories. Car seats, uniforms, holidays and tuition are not established as currently covered. Bicycle supply exists through Halfords. Existing accepted reviews are retained; no new owner acceptance is inferred.

Latest normal collector source counters: car-seat RSS fetched 30, verified 0; uniform RSS fetched 30, verified 0; bicycle RSS fetched 30, verified 0; Halfords direct fetched 3, verified 2; AWIN fetched 10, verified 0. Source success does not imply accepted supply.

Historical AWIN membership evidence remains dated 6 October in docs/awin-baby-api-trial.md. A new current membership check and independent MasterTag delivery verification are still required. Neither existing source activation nor generic network campaigns prove those criteria.

## Implemented workspace

Owner-protected /ops/deals: paged offers, canonical taxonomy/aliases, source yield/readiness and Deals-specific action history. Actual public selector membership distinguishes displayed from stored offers. Unknown prices, expiry and eligibility evidence stay explicit.

Source pause/activate/restore reuses the existing signed intent, identity, atomic audit and stale-state controls. Pause stops future collection; it does not immediately hide existing offers. No taxonomy-writing API, source activation, paid retry or live offer mutation has been performed. Preview deployments remain unable to apply actions.

## Validation

Four queue/access/error tests and one real PostgreSQL-compatible Deals pause/stale/idempotency/restore rehearsal passed, together with the existing seven maintenance/access regressions (12 checks). TypeScript passed. Initial workspace production build passed using webpack; subsequent form refinements require final hosted checks and browser QA.

## Further progress

Hosted owner sign-in succeeded. Verified 17 displayed offers, canonical alias filtering, the genuine empty action history, disabled preview writes, a Deals source preview and invalidation after editing its record ID. No Deals maintenance audit entries were created. Current AWIN audit and scheduled dispatch misses are recorded in sprint-7-decisions.md.

Natural Baby Shower's narrow car-seat collection was read without database credentials or writes; one exact variant passed the existing normal classifier/value/verifier functions and is frozen in sprint7-new-offers.json. Its candidate route is allowlisted in code but no database source exists or is active. It remains unaccepted/unpublished and does not fulfil the three-group requirement.

Full Node regression suite: 177 passed before the final display-title reuse. Full Python discovery passed after supplying the existing Beautiful Soup dependency to the isolated local test directory; initial import failures were environmental. Focused Shopify suite: 23 passed. Hosted checks passed at 24b50e8; later trial changes need their own hosted checks.

## Remaining before release

- Qualify missing priority supply with exact current merchant evidence and permitted normal collector routes; do not publish search snippets or old seasonal campaigns.
- Refresh AWIN membership/yield and verify MasterTag delivery.
- Verify hosted owner UI, narrow-screen/keyboard/error states and source preview without executing a live action.
- Freeze genuinely new/materially changed offers and state exact review count; retain unchanged Sprint 5 approvals.
- Present concrete source/alias/policy decisions with release recommendation in one consolidated pack.
- #132 remains dependent on real scheduled evidence and #125; no observation points accepted.

Committed 21 / accepted 0 / remaining 21. No ticket closed.
