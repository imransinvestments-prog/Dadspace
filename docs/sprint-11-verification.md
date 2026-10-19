# Sprint 11 verification — 19 October 2026

Status: local engineering and hosted sign-in/browser checks passed; owner factual acceptance and scheduled observation remain pending.

- `node --test tests/*.test.cjs tests/*.test.mjs`: **189 passed**, including actual disposable PGlite visitor-fact SQL, permissions, stale edits/import preservation and rollback. [Output](../artefacts/documentation/sprint11-node-tests.txt).
- Python suite: **284 run, 11 optional skips**, zero failures including nine schedule-attribution/runtime-fingerprint/DST tests. Local Python 3.15 uses workspace-local dependencies. [Output](../artefacts/documentation/sprint11-python-tests.txt).
- `node node_modules/typescript/bin/tsc --noEmit`: passed.
- `node node_modules/next/dist/bin/next build --webpack`: passed. Shared node_modules symlink prevents Turbopack resolving this local worktree; hosted build uses normal installation. [Output](../artefacts/documentation/sprint11-build.txt).
- Blueprint adversarial review found two issues, both fixed: reviewed authoritative slot attribution input with no fabricated historical matches, and field-specific visitor review provenance rather than a broad verification badge.
- [Slot evidence format](sprint-11-slot-evidence.md) supports future retained evidence. Parent slot coverage is separate from source/feed/publication acceptance.
- Supabase function changes retain security invoker, service-role-only execution and public projection of source/date/reviewed field names only. Checked current [Supabase function documentation](https://supabase.com/docs/guides/database/functions) and changelog; no production migration or correction applied.

## Hosted review

Preview URL: [Sprint 11 review](https://dadspace-git-dev-sprint-11-reliability-imransinvestments-6859.vercel.app/ops/sprint-11). Draft [PR #212](https://github.com/imransinvestments-prog/Dadspace/pull/212).
Measured and browser-verified deployed SHA: `d67f269882096192488138e7c0e9cf2246b96ea0`. Vercel deployment passed. Later evidence-only commits are recorded separately; measurements remain bound to this SHA.
Anonymous sign-in redirect: verified to `/auth/login?next=%2Fops%2Fsprint-11`; no protected review evidence exposed.
Signed-in owner rendering: verified after the owner signed in to the preview. Protected workspace, 105 library candidates, restricted filter (two results), source details, venue review rubric and configured review-saving readiness render. Current venue rubric progress is 0/50; no owner approvals were submitted by the agent. Guarded database decision page explicitly read-only; no database apply action available to this session.
PostgreSQL 17 hosted transaction checks: queued at GitHub, not passed. Nine PR workflows were still queued when inspected; Vercel deployment succeeded. Do not conflate deployed preview with passing hosted checks.
Preview API: all six cases / 120 samples passed. Worst case p95 899.37 ms and largest payload 18,324 bytes, below 2,500 ms / 102,400 bytes. [Raw results](../artefacts/data/sprint11-preview-api-performance.json). Preview lab comparison: all 24 runs completed with three valid samples per route/device. [Condensed raw results](../artefacts/data/sprint11-preview-performance.json); [full Lighthouse reports](../artefacts/documentation/sprint11-preview-lighthouse-reports.zip). The late install-banner change improves several sampled medians, but mobile LCP remains above 2.5 seconds. This is a measured post-release baseline comparison, not reconstruction of missing historic pre-release data.

Browser checks: category and Hounslow detail render at 390px without horizontal overflow; category is noindex/nofollow and absent from sitemap; sitemap excludes ops and personal coordinates. Page 3 preserves its canonical query. Hounslow shows explicit unknown visitor facts because staged proposals have not been applied. Signed-in keyboard Tab reaches the location control. No claim of completed owner usability acceptance.

### Preview lab results

| Route | Device | LCP ms | CLS | TBT ms |
|---|---|---:|---:|---:|
| / | mobile | 3517 | 0.001 | 74 |
| / | desktop | 1037 | 0.0254 | 0 |
| /venues | mobile | 2565 | 0.0027 | 38 |
| /venues | desktop | 722 | 0.0304 | 0 |
| /venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a | mobile | 3030 | 0.001 | 30 |
| /venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a | desktop | 845 | 0.0247 | 0 |
| /places/hounslow/libraries | mobile | 7001 | 0 | 47 |
| /places/hounslow/libraries | desktop | 872 | 0.0247 | 0 |

## Latest operational failure

[Retained findings](../artefacts/data/sprint11-operational-findings.json): scheduled run 39258943242 failed in Deals (expired Matalan terms review) and News (nine upstream Google RSS 503 responses). Partial saved rows do not establish successful feed acceptance. Fresh source/terms review and actual scheduled recovery remain required. No terms dates were extended and no source or schedule was changed.

## Acceptance gaps

The refreshed ledger contains four post-stable daily-worker runs and two Originals runs. Historical missing trigger attribution stays unknown. Seven-day feed acceptance, actual current Friday/recovery evidence, human venue quality labels, library factual decisions and exact area/cohort decisions remain open. Field data and Search Console property evidence remain unavailable as of this review. #147/#149 readiness still has owner usability/retained recovery dependencies; no additional points are counted.

This report does not close child issues or authorise a merge, production release, mutation, paid generation or schedule change.
