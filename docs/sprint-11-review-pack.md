# Sprint 11 review pack

Prepared 19 October 2026. Status: **draft for review; acceptance pending**.

This pack describes local work on `dev/sprint-11-reliability`, tracker [#211](https://github.com/imransinvestments-prog/Dadspace/issues/211). It is based on frozen repository evidence, not a live GitHub or production audit. Engineering verification has now been run: 189 Node tests passed; 282 Python tests ran with 11 optional skips; TypeScript and the production webpack build passed. Hosted preview and factual acceptance are tracked separately below. The local build used webpack because this worktree shares node_modules outside the Turbopack filesystem root.

Start with the [step-by-step completion guide](sprint-11-completion-guide.md). The protected review workspace is `/ops/sprint-11` on the eventual preview; no verified preview URL is recorded here.

Engineering detail and preview results: [verification report](sprint-11-verification.md).

## Scope and current acceptance

35 provisional scope points. These are not an estimate of remaining effort or points earned. Sprint 10 is recorded as released. #206 geography observation and #207 national expansion remain outside Sprint 11. Previously accepted content and parent issues receive no duplicate credit.

| Ticket | Prepared evidence/work | Required before acceptance | Current status |
|---|---|---|---|
| #34 — 8 points | Fixed 50-venue cohort, dated current snapshot and review rubric | Review every fixed row; at least 48/50 jointly pass identity, location and usable primary source; zero hidden leakage; retain failed/unknown rows and bounded corrections | Human review and gate evidence pending |
| #92 — 8 points | 105 published library-category candidates, official-source proposals and record fingerprints | Confirm branch identity/address, public access, sourced visitor facts and holiday-sensitive hours; explicitly resolve restricted/unknown candidates; protect reviewed fields and test stale edits | Proposals prepared; unapplied |
| #139 — 5 points | Area/category candidates and explicit publication gate | Owner chooses actual W3 pilot areas; exact complete UUID cohorts pass quality review; approve distinct copy; demonstrate noindex/sitemap exclusion for unapproved or changed cohorts | Area/cohort decisions pending |
| #141 — 5 points | 120 production API samples and 24 lab runs recorded; dev install-banner layout change | Verify preview mobile LCP and regressions; preserve baseline/preview SHA and raw three-run medians; obtain Search Console/representative field evidence or retain dated unavailable states | Mobile LCP target unmet in baseline; preview verification pending |
| #132 — 3 points | Two scheduled Deals jobs reported 19 published offers each | Prove eligible consecutive slot timing, retained offer identity/terms/freshness and public readback; reconcile delta from accepted 17-offer review | Scheduled acceptance unproven |
| #129 — 3 points | Latest daily duplicate skip retained | Actual daily/Friday/09:17 evidence and retained genuine failure/recovery evidence after stable release; demonstrate idempotency | Friday/recovery outstanding |
| #125 — 3 points | London-time expected-slot ledger, runs/configuration metadata and explicit attribution gaps | Seven-day eligible cross-feed evidence with every expected slot accounted for, source/publication linkage and three successful scheduled Activities collections | Seven-day acceptance unmet |

Ticket links: [#34](https://github.com/imransinvestments-prog/Dadspace/issues/34), [#92](https://github.com/imransinvestments-prog/Dadspace/issues/92), [#139](https://github.com/imransinvestments-prog/Dadspace/issues/139), [#141](https://github.com/imransinvestments-prog/Dadspace/issues/141), [#132](https://github.com/imransinvestments-prog/Dadspace/issues/132), [#129](https://github.com/imransinvestments-prog/Dadspace/issues/129), [#125](https://github.com/imransinvestments-prog/Dadspace/issues/125).

## Review decisions to record

| Decision | Concrete choice to review | Acceptance record |
|---|---|---|
| Venue corrections | Per-record before/after, current official source, reviewer rubric and fingerprint; retain unknowns | Pending |
| Library visitor facts | Branch proposals, especially Hounslow Library and restricted candidates; distinguish public libraries from archives/restricted collections | Pending |
| Pilot area approach | Inspect Hounslow and the proposed Ealing/Brent alternatives within W3 9LN / 10 km; broad London needs precise scope; Manchester is outside this pilot | Pending; no area recommended as approved |
| Publication cohorts | Exact URLs, full eligible UUID set, current evidence and distinct page copy; count alone is insufficient | Pending |
| Engineering acceptance | Verified preview, test report, access checks and mobile performance comparison | Pending |
| External evidence | Search Console access/field data availability; unresolved scheduled evidence with explicit next action | Pending or dated unavailable; never a pass |

Use the decision log below once the concrete preview and full cohorts are ready. Do not interpret approval of a general area approach as approval of every record.

| Date/time Europe/London | Ticket / record / exact URL | Decision and scope | Reviewer | Evidence / current fingerprint | Follow-up |
|---|---|---|---|---|---|
| Pending | | | | | |

## Evidence index

All links are relative to this pack. The [SHA-256 manifest](../artefacts/documentation/sprint11-review-manifest.json) freezes the source evidence used for this version; later captures must get a new manifest rather than being represented as unchanged evidence.

- [Authorised delivery plan](../plans/sprint-11-delivery.md) and [Sprint 10 review](sprint-10-review.md).
- [Fixed sample](../artefacts/data/sprint5-review-pack.json), [current venues](../artefacts/data/sprint11-venues-snapshot.json), [venue labels](../artefacts/data/sprint11-venue-labels.json). Labels alone are not completed quality checks.
- [Library proposals](../artefacts/data/sprint11-library-review.json), [library snapshot](../artefacts/data/sprint11-libraries-snapshot.json), [provenance](../artefacts/data/sprint11-library-provenance.json).
- [Area/category candidates](../artefacts/data/sprint11-area-candidates.json). Bounded/incomplete sets cannot be approved as full cohorts.
- [API measurements](../artefacts/data/sprint11-api-performance.json), [lab measurements](../artefacts/data/sprint11-performance.json).
- [Schedule ledger](../artefacts/data/sprint11-schedule-ledger.json), [scheduled runs](../artefacts/data/sprint11-scheduled-runs.json), [run readback](../artefacts/data/sprint11-run-readback.json), [Originals snapshot](../artefacts/data/sprint11-originals-snapshot.json).
- [Review workspace source](../app/ops/sprint-11/page.tsx), [database CI checks](../.github/workflows/operations-review-checks.yml).

## Verification report — engineering checked; acceptance pending

| Check | Result in this pack | Evidence required |
|---|---|---|
| Manifest source files exist and hashes recorded | Checked during pack generation | Manifest |
| TypeScript, build, Node and Python regressions | Passed locally; see linked verification report for final counts | Dated output and exact reviewed commit |
| Guarded visitor-fact transactions and access | Disposable PGlite transactions passed, including field-specific evidence | Real PostgreSQL CI and browser readback pending |
| Hosted preview, signed-in/anonymous browser checks | Not verified | Preview URL/SHA, screenshots and findings |
| Mobile LCP improvement | Not verified | Comparable preview measurements |
| Factual venue/library acceptance | Pending | Completed per-record rubric/source review |
| Scheduled observation | Incomplete in frozen evidence | Updated attributed ledger and publication readback |

## Release boundary and rollback

Current authorised endpoint: clean dev branch, draft PR, review pack and preview for owner testing. Merge, production migration, production corrections, source activation, paid services and public expansion require a separately scoped release decision. This pack does not request that decision yet.

Before review, preserve record fingerprints, source snapshots, accepted-work history and immutable observation evidence. Dev rollback is a reviewed revert of Sprint 11 changes, including visitor-fact UI and publication gates; retain historical evidence. A future production release needs its own exact migration/data rollback plan and readback. Do not run inverse SQL, delete records or reset observation windows as part of this pack.
