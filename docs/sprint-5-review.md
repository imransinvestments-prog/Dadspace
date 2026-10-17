# Sprint 5 — consolidated review

## Current status — 17 October 2026, after owner decisions

**18/24 accepted; six remain.** #122, #123, #124, #130 and #176 are closed. #126/#127 remain open for three held News location revisions and final targeted acceptance. The 16 approved News corrections committed at 15:30 UTC, with exact readback and no unintended selected-field changes; three held rows plus the Monmouthshire no-op were unchanged. Fresh Deals readback confirmed the same 17 selected offers, all owner-scored passes. Freshness targets and diagnostic Activities interpretation are explicitly approved.

New follow-up #180 (5), #181 (5), #182 (5), #183 (3) are refined, provisional backlog stories outside Sprint 5. They do not promise a complete Activities epic or start a new sprint. See [final News proposals](./sprint-5-remaining-news-decisions.md) and the timestamped `artefacts/data/sprint5-burndown-ledger.json`.

The initial review packet below is retained as history. Its references to pending decisions, unapplied corrections and zero accepted points describe the pre-review state, not current status. The update also refreshes the operator status copy; its additional county-filter fix requires review before release/application.

## Initial review packet (historical)

Started 17 October 2026, tracker [#178](https://github.com/imransinvestments-prog/Dadspace/issues/178). Committed 24 points; **accepted 0, remaining 24** until applicable human, release and data-readback gates pass. Scope is #122 (5), #123 (2), #124 (3), #127 (3), #126 (3), #130 (5), #176 (3). No deadline or ideal historical burndown has been invented.

## Owner decisions, together

The protected preview entry point is `/ops/sprint-5`; the usual owner account is required. This pack does not ask for another general News review or all 150 venue/Activity rows now.

1. **Smaller Deals pool — recommend all 17, reviewed once.** The capture contains 198 stored Deals, 160 live-status rows and 138 fresh active-taxonomy quality candidates. All 138 pass the current eligibility predicate; the exact shared selector collapses equivalent items/links to 17 public offers across nine merchants and seven groups. Require at least 16/17 useful, accurate and actionable for both pool and available top subset; zero known expired/unavailable offers or unsupported savings remains mandatory. Record six explicit checks per offer at `/ops/reviews/130`. No scores have been invented. Current merchant facts must be checked because these snapshots will age.
2. **Activities breadth — recommend 10 distinct actionable opportunities / three categories / two independent providers** within W3 9LN, 10km, ages 0–5. Existing 90% quality gates remain. The 100-row diagnostic cohort is not 100 pilot-qualified Activities: 16 have a linked in-radius venue, 70 have unknown distance in this capture. Public postcode/location fallback may locate more. Agree the target, not a claim it has already passed.
3. **Freshness warnings — recommend dispatch after 60 minutes, completion after four hours, source checks after 36 hours.** The dashboard now compares the most recent expected London slot independently of eventual job success. It distinguishes missing dispatch, delayed dispatch, failed/cancelled/skipped work and unavailable evidence; existing source checks show failures, unknown/zero yield separately. Warnings appear on dashboard reads (public metadata cached up to ten minutes); this is not proactive email/push alerting or proof of useful public supply. Record target/escalation agreement on #124.
4. **News — recommend the explicit 16 proposed changes, retain Monmouthshire, hold three location conflicts.** `/ops/reviews/127` shows all 20 before/proposed records: 18 requested changes plus two negative geography checks (#306/#453) that included nationwide instructions despite an overall approval. Proposals preserve the recorded nation: England-wide is not UK-wide. Confirm that interpretation. #909 is already Monmouthshire; do not narrow it to Monmouth town without evidence. Hold #736 (Port Glasgow versus Glasgow), #739 (Cheshire versus a supported county/district target), #855 (Maldon source URL versus Colchester instruction). Existing approved geography checkboxes do not override conflicting notes. No production corrections have been applied.
5. **Activities follow-up — recommend refining four additional engineering slices before committing later sprints.** The discovery document proposes 18 provisional points, with overlap explicitly reconciled against #40/#135/#146 before any addition to the roadmap. This is not a reliable all-in epic estimate. Source qualifications remain #104/#133/#134; final quality/scheduled acceptance remains #136. No source activation, paid extraction or date/age deletion is included.
6. **Release this preview after review, then apply only approved News changes through the guarded batch.** No merge or content mutation is assumed from sprint commencement. Recheck time-sensitive Deals and News fingerprints immediately before acceptance/application. Held corrections and any failed scoring keep the affected tickets open.

## Engineering and baseline evidence

- Frozen 50 category-balanced published venues from 1,054 unmerged in-radius candidates; 100 Activities across 23 recorded sources; all 17 public Deals in exact shared selection order. Capture timestamp, SQL, eligibility method, whole-manifest and per-row SHA-256 fingerprints are retained. Queries freeze membership; rerunning against a changed database is a new capture, not the same sample.
- Review UI now reads these fixed snapshots instead of changing live queues. Operator gates run before returning material. The original 50-row News manifest and decisions remain unchanged. Saved Deal checks bind the owner, exact snapshot and issue version; unknowns do not count as passes and repeated decisions count once.
- News paging and Home retrieval now add an ID tie-breaker after publication date; this prevents date ties from moving unpredictably across offset pages. Existing locality/legacy fallback, attribution, category, empty/configuration/query/transport and London/DST checks are retained. Offset paging is still a live feed: newly inserted articles can move offsets; this is not a cursor snapshot guarantee.
- `sprint5-news-correction-rehearsal.sql` contains only the 16 changed proposals, checks captured fields and locks rows, aborts the entire transaction on stale/missing evidence, reads back proposals and **always rolls back**. PostgreSQL rehearsal verifies both no committed changes and a late-batch concurrency conflict. It is not a production apply script or completed audit/readback.
- Historical run [38727867813](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38727867813): expected 15 October 07:17 BST (06:17 UTC); created and started 12:30:50 BST (11:30:50 UTC), a 5h13m50s gap. Gate ran 12:30:53–55 BST; workers began 12:30:57–58. The delay precedes visible execution; the unexposed GitHub dispatch cause is **unknown**. Slot association is inferred from the configured schedule, not an API-provided scheduled-slot ID.
- Collector isolation is unchanged: News, venue reference, civic, Activities and Deals depend on the gate separately. New monitoring is read-only and cannot refresh last-seen or cancel collectors. The actual seven-day ledger and scheduled acceptance remain #125, not accelerated by this sprint's tests.
- [Activities investigation](./sprint-5-activities-discovery.md) records source-to-public architecture, confirmed view/renewal mechanisms, an eight-record diagnostic subset and source-retrieval limitations. Existing schedule/card delivery is reused. No missing relationship is treated as grounds to discard a useful listing.

## Validation and limits

156 Node tests pass, including fixed-cohort access/pagination/fingerprints, Deal score trust/unknown/supersession rules, expected-slot/DST/manual-run/failure independence, stable News ordering, existing regression coverage and two real PostgreSQL correction rehearsals. `node scripts/test-news-locality.mjs` passes; TypeScript passes. A webpack production build completes successfully outside the sandbox. Default local Turbopack fails during CSS build-process spawning, including outside the sandbox; hosted Linux/default build evidence is still required before release.

The first build also exposed one pre-existing Windows-1252 smart quote in `components/venues/venues-json-ld.tsx`. It is re-encoded as UTF-8 with the same intended playground key; this minimal build repair has no new story points. Full regressions pass after the repair.

No database/schema mutation, source/provider activation, paid benchmark run, permission change or external notification has been made. Read-only Supabase captures and public GitHub/source evidence are used. Source error text is redacted from the published baseline. Source-web results can be cached; inaccessible research-tool pages are not treated as HTTP failures or proof of unsuitability.

## Closure and estimate accounting

| Ticket | Prepared evidence | Still required before closure |
| --- | --- | --- |
| #122 | Frozen manifests, source inventory, supply/unknown summaries, programme refresh | Owner agrees any sample interpretation; accept baseline/readback. No fabricated pilot eligibility. |
| #123 | Two unresolved threshold choices with actual Deals examples | Owner decision and links to affected gates. |
| #124 | Dispatch reconstruction, slot warnings, failure/independence regressions | Owner targets/escalation, hosted preview/release evidence. |
| #127 | 20-row reconciliation, stable paging, rollback-only 16-row rehearsal | Resolve held locations; approve/apply exact changes, audit/readback and targeted re-review. |
| #126 | Existing 50 decisions/rubrics preserved | #127 remediation and public readback; no new general 50-row pass. |
| #130 | Exact 17-offer frozen selector output, six-check UI/progress | Smaller-pool agreement, 17 human judgments, current merchant/link/terms checks and remediation/readback. |
| #176 | Architecture, 488-row aggregate baseline, eight diagnostic examples, bounded proposed slices | Owner accepts decomposition/unknowns; later source qualification and engineering remain separate. |

The approved programme baseline remains 207 known provisional direct points before any newly accepted scope. The possible 18 Activities points must not be added automatically: first remove overlap/re-estimate and obtain the planning decision. Preserve deferred #101/#158/#157 and conditional Community. Final closure includes the mandatory sprint review before another sprint commitment.
