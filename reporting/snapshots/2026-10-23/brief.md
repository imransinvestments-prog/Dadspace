# Morning Brief

23 October 2026 · Europe/London · Brief generation occurred after the 07:30 target.

## Key items
- **High — Timer starts now have real on-time evidence:** Today's workers and Originals timer-slot runs were created at 07:17:01 London; the Originals retry at 09:17:02. Workers succeeded. Retain these as timer-driven slot evidence, separate from ordinary manual runs and late cron backups; one day does not complete the shared observation period. [#125](https://github.com/imransinvestments-prog/Dadspace/issues/125).
- **High — Friday publication recovered after a retained rejection:** The 07:17 Originals job rejected both drafts and published nothing. The 09:17 retry logged both daily-2026-10-23 and weekly-2026-10-23 as published. Preserve the failed first attempt and verify public readback; no extra paid catch-up is needed from reporting. [#129](https://github.com/imransinvestments-prog/Dadspace/issues/129).
- **High — Review the first live council-discovery batch:** The venue worker logged 84 inserted records across 10 GB councils. This is not 84 public or human-accepted places. Under current owner-approved rules, supported types may publish while possible duplicates/neighbouring-council conflicts remain hidden; AI notes stay unverified provenance. Check actual review/public outcomes and area-cohort gates, without repeating already-settled activation decisions. [#243](https://github.com/imransinvestments-prog/Dadspace/issues/243).
- **Medium — Acceptance status moved forward:** Deals scheduled acceptance #132, pilot venue audit #34, library details #92, area pages #139 and mixed-age filtering #101 are complete; PR212 merged. Retire yesterday's 0/50 venue-label blocker. Deals' current timer run saved 120 rows and reported 18 offers across 8 groups/10 providers; separate remaining #125/#129 and project gates. [#132](https://github.com/imransinvestments-prog/Dadspace/issues/132).
- **Medium — Usage is partial; source failures persist:** Measured civic/activity/news subtotal: 357,501 tokens across 29 calls; thinking included. Council discovery separately logged 10 LLM calls with unknown token usage, and Originals/shadow totals remain unavailable. Civic had 12 route failures and 3 robots exclusions despite job success; no national/county public-quality percentage is established. [#136](https://github.com/imransinvestments-prog/Dadspace/issues/136).

## Project summary
**40 open issues · 3 open PRs · 59 completed issues · 132 merged PRs · 12 closed without completion.** All 246 repository items reconciled across three pages. Hierarchy counts are not unique deliverables; superseded closures are not completion. Board-only draft cards/status fields unavailable.

## Open work by feature
- **Places and local discovery (3):** [#243](https://github.com/imransinvestments-prog/Dadspace/issues/243), [#113](https://github.com/imransinvestments-prog/Dadspace/issues/113), [#40](https://github.com/imransinvestments-prog/Dadspace/issues/40)
- **Navigation and interface (1):** [#232](https://github.com/imransinvestments-prog/Dadspace/issues/232)
- **Programme and pilot readiness (3):** [#211](https://github.com/imransinvestments-prog/Dadspace/issues/211), [#44](https://github.com/imransinvestments-prog/Dadspace/issues/44), [#29](https://github.com/imransinvestments-prog/Dadspace/issues/29)
- **Geography reference and coverage (2):** [#207](https://github.com/imransinvestments-prog/Dadspace/issues/207), [#206](https://github.com/imransinvestments-prog/Dadspace/issues/206)
- **Activities and source coverage (10):** [#201](https://github.com/imransinvestments-prog/Dadspace/pull/201), [#198](https://github.com/imransinvestments-prog/Dadspace/issues/198), [#136](https://github.com/imransinvestments-prog/Dadspace/issues/136), [#135](https://github.com/imransinvestments-prog/Dadspace/issues/135), [#134](https://github.com/imransinvestments-prog/Dadspace/issues/134), [#133](https://github.com/imransinvestments-prog/Dadspace/issues/133), [#121](https://github.com/imransinvestments-prog/Dadspace/issues/121), [#120](https://github.com/imransinvestments-prog/Dadspace/issues/120), [#114](https://github.com/imransinvestments-prog/Dadspace/issues/114), [#84](https://github.com/imransinvestments-prog/Dadspace/pull/84)
- **News and Originals (4):** [#195](https://github.com/imransinvestments-prog/Dadspace/issues/195), [#147](https://github.com/imransinvestments-prog/Dadspace/issues/147), [#129](https://github.com/imransinvestments-prog/Dadspace/issues/129), [#115](https://github.com/imransinvestments-prog/Dadspace/issues/115)
- **Operations and feed reliability (7):** [#158](https://github.com/imransinvestments-prog/Dadspace/issues/158), [#157](https://github.com/imransinvestments-prog/Dadspace/issues/157), [#149](https://github.com/imransinvestments-prog/Dadspace/issues/149), [#146](https://github.com/imransinvestments-prog/Dadspace/issues/146), [#125](https://github.com/imransinvestments-prog/Dadspace/issues/125), [#104](https://github.com/imransinvestments-prog/Dadspace/issues/104), [#70](https://github.com/imransinvestments-prog/Dadspace/issues/70)
- **AI ingestion and providers (6):** [#145](https://github.com/imransinvestments-prog/Dadspace/issues/145), [#144](https://github.com/imransinvestments-prog/Dadspace/issues/144), [#143](https://github.com/imransinvestments-prog/Dadspace/issues/143), [#116](https://github.com/imransinvestments-prog/Dadspace/issues/116), [#69](https://github.com/imransinvestments-prog/Dadspace/pull/69), [#66](https://github.com/imransinvestments-prog/Dadspace/issues/66)
- **SEO and performance (2):** [#141](https://github.com/imransinvestments-prog/Dadspace/issues/141), [#119](https://github.com/imransinvestments-prog/Dadspace/issues/119)
- **Community (4):** [#117](https://github.com/imransinvestments-prog/Dadspace/issues/117), [#43](https://github.com/imransinvestments-prog/Dadspace/issues/43), [#42](https://github.com/imransinvestments-prog/Dadspace/issues/42), [#41](https://github.com/imransinvestments-prog/Dadspace/issues/41)
- **Deals (1):** [#48](https://github.com/imransinvestments-prog/Dadspace/issues/48)

## Delivery plan today
1. Retain today's timer dispatch, initial rejection and retry/publication evidence in the shared ledger; verify the actual daily and weekly public articles without new generation.
2. Review only the first live council batch's duplicate/adjacent-council exceptions and resulting public/area-cohort status. Do not equate inserts, source access or real OSM provenance with accepted quality.
3. Reconcile accepted venue/library/area/Deals tickets and merged PR212; stop carrying superseded review blockers forward. Keep remaining observation and performance evidence separate.
4. Measure council-note/Originals usage when artifacts expose it; preserve configured budgets, fixed W3 9LN /10 km /ages 0–5 and existing source/provider/release gates.

## Later / FYI
- [On-time workers](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39910547507) · [Originals rejection](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39910547430) · [Daily/weekly retry](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39923556295).
- Geography point baseline remains frozen at 18 October: 28 GB lookup/venue samples, 10 Activity and 6 Event samples nonempty, 2 NI withheld. Today's 10-council discovery is new collection evidence, not a national/county census. Historical access matrix remains 10–11 October.
- UI/accessibility/weather changes merged; broad UI/UX review #232 remains open. Do not infer full product acceptance from deployment.

[Usage/feed dashboard](operations.html) · [Source/geography dashboard](sources-coverage.html) · [Evidence JSON](data.json).
