# Sprint 11 verification — 19 October 2026

Status: local engineering checks passed; hosted preview and owner acceptance pending.

- `node --test tests/*.test.cjs tests/*.test.mjs`: **189 passed**, including actual disposable PGlite visitor-fact SQL, permissions, stale edits/import preservation and rollback. [Output](../artefacts/documentation/sprint11-node-tests.txt).
- Python suite: **282 run, 11 optional skips**, zero failures including seven schedule-attribution/DST tests. Local Python 3.15 uses workspace-local dependencies. [Output](../artefacts/documentation/sprint11-python-tests.txt).
- `node node_modules/typescript/bin/tsc --noEmit`: passed.
- `node node_modules/next/dist/bin/next build --webpack`: passed. Shared node_modules symlink prevents Turbopack resolving this local worktree; hosted build uses normal installation. [Output](../artefacts/documentation/sprint11-build.txt).
- Blueprint adversarial review found two issues, both fixed: reviewed authoritative slot attribution input with no fabricated historical matches, and field-specific visitor review provenance rather than a broad verification badge.
- [Slot evidence format](sprint-11-slot-evidence.md) supports future retained evidence. Parent slot coverage is separate from source/feed/publication acceptance.
- Supabase function changes retain security invoker, service-role-only execution and public projection of source/date/reviewed field names only. Checked current [Supabase function documentation](https://supabase.com/docs/guides/database/functions) and changelog; no production migration or correction applied.

## Hosted review

Preview URL: pending deployment.
Exact deployed SHA: pending.
Anonymous sign-in redirect: pending.
Signed-in owner rendering: pending actual authenticated session.
PostgreSQL 17 hosted transaction checks: pending PR checks.
Preview lab/API comparison: pending.

## Acceptance gaps

The refreshed ledger contains four post-stable daily-worker runs and two Originals runs. Historical missing trigger attribution stays unknown. Seven-day feed acceptance, actual current Friday/recovery evidence, human venue quality labels, library factual decisions and exact area/cohort decisions remain open. Field data and Search Console property evidence remain unavailable as of this review. #147/#149 readiness still has owner usability/retained recovery dependencies; no additional points are counted.

This report does not close child issues or authorise a merge, production release, mutation, paid generation or schedule change.
