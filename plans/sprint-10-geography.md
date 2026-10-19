# Sprint 10 — UK geography and coverage

Authorised 18 October 2026; tracker #202. Dedicated branch `dev/geographic-coverage` from main 0edd2c3. Stop at development delivery for owner testing; no production schema/data/source changes or merge. Sprint 9 remains independent. Estimates are relative complexity, not capacity promises or elapsed time.

## Construction sequence

1. **#203 — Reference catalogue, 5 points.** Context: existing `news_geography.json` pins an ONS May 2026 administrative lookup; location APIs use Postcodes.io. Fetch the official lookup's codes and names, preserve its edition/provenance, and model versioned administrative edges independently of postal hierarchy. Add an unapplied RLS-protected database migration, validated release/seed SQL generator and streaming ONSPD CSV adapter. Seed a small GB pack only; NI postcode data requires an authorised licence. Test actual PostgreSQL-compatible constraints, role denial and repeat release imports. Exit: reproducible isolated catalogue with explicit sample scope and no inferred county/town ancestry. Rollback: dev database disposal; production would retain data and roll back the app independently, never silently drop history.
2. **#204 — Postcode test pack, 5 points, depends on #203.** Context: current lookup, regional news and distance selectors already exist and must be reused. Build 30 deliberate scenarios plus negative cases, source-verified GB postcode mappings and explicit NI licence-blocked cases. Run deterministic checks through actual code; provide an optional bounded read-only live checker against the dev app that records successful empty supply separately from request failure and untested quality. Exit: versioned pack, test results and reproducible commands; no fabricated content fixtures published to live feeds. Rollback: remove new test tooling/fixtures without changing existing location behaviour.
3. **#205 — Coverage workspace/review, 5 points, depends on #203/#204.** Context: `/ops` is owner protected; public feeds have existing eligibility and failure semantics. Add `/ops/geography` with a pinned baseline derived through those reads and reference/sample denominators. Include national applicability for Deals/Originals without attributing it to every council. Include review decisions and manual feature checklist, report unknowns honestly, and validate type/build/integration/access/mobile behaviour. Exit: all work on dev branch with draft PR/preview and owner review pack; no accepted points or release claimed. Rollback: revert added route/nav; no effect on public lookup or content.

Total committed delivery: **15 provisional points**. One implementation story active at a time; no automatic stretch. Consolidated owner review is included in #205, with no duplicate test/documentation credit.

## Observation identified before start

#206 (2 provisional points) belongs to the next sprint after approved release, not this commitment. Record the exact release, reference version, pack hash and future expected scheduled slots; compare after at least two normal collection cycles. Waiting and manual checks cannot substitute for scheduled evidence. Reference refresh/termination testing is isolated until review.

## Decisions and boundaries

Use official codes with edition-scoped relationships. Administrative and postal structures are linked, not forced into one UK county tree. Store coordinates as postcode representative points, not exact address locations. Keep existing public selectors and pilot unchanged. Small reference seed does not mean all UK postcodes imported; one sampled postcode does not establish full council coverage. No national coverage threshold is invented. NI postcode commercial licence is unresolved; withhold restricted geocodes and show blocked tests. Full national licensed import and broader one-per-council sampling remain explicit expansion steps, not hidden acceptance claims.

## Validation and review

ECC Blueprint adversarial plan review, actual isolated SQL forward/constraint/role tests, deterministic reference validation, feature test harness, existing relevant regressions, TypeScript, production build, diff/security check and browser inspection. Attach exact command results and branch SHA. Tests should cover partial/error responses, terminated postcodes, bad relationships, missing geocodes, national versus local content, unavailable services, unauthorised review access and honest zero supply. A green fixture test is not observed production coverage.

## Adversarial review refinements

The ECC Blueprint review identified five material refinements, incorporated without adding stories: provide an actual persistent isolated PGlite development catalogue and explicit bootstrap/status commands; test official-code compatibility with the current name-based News handlers; retain point/radius/time/eligibility/endpoint completeness on every coverage observation; enforce NI postcode withholding in Python validation, SQL generation and database constraints; distinguish deterministic checks from manual persisted-location/permission/browser acceptance. The protected workspace states that it reads bundled snapshots, not that development database.

Broader sampling/national-scale licensed import is explicitly #207; the streamed CSV reader is an adapter foundation, not a national production importer or automatic acquisition service. #206 remains the subsequent sprint's scheduled observation. A 15-point estimate is not a claim of an optimal eight-point sprint or a date guarantee. No activities points or previous delivery credit is reused.
