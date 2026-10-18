# Sprint 8 commencement — 18 October 2026

## Completed — 18 October 2026

PR #199 merged and production verified. #180/#183/#181/#182 delivered their bounded
scope: 18/18 accepted, zero committed carryover. Final Python 251 passed/13 skipped,
179 distinct Node checks, TypeScript/build and all five final hosted workflows pass.
Two actual read-only Sutton passes accepted the same programme identity at zero
model/database writes. Evidence files are preserved. Current closure and limits:
[sprint-8-closure.md](sprint-8-closure.md). Earlier pending checkpoints below are historical.

Sprint 9 #197 still owns real observation; #198 identity repair and #134 source
qualification stay separate. No unprovided owner content review is claimed.

---

## Current delivery completion checkpoint

All four bounded implementations/evidence packs are prepared on the isolated
`sprint/8-activities-foundation` branch from main b0a9a0f. Unrelated workspace edits
were excluded. Review: [sprint-8-review.md](sprint-8-review.md).

- #180: append-only evidence, explicit source-tail coverage and bounded readback;
  unknown item completeness stays unknown.
- #183: actual SQL/trigger replay; repeat/schedule/move/distinct programme checks;
  rename/session defects reproduced and separately estimated under #198.
- #181: MyLibrary detail coverage, withheld/cancelled/partial evidence; adapter and
  real SQL renewal checks demonstrate unseen rows are not renewed on accepted or
  failed snapshots. Existing public 60-day filter unchanged. No source activated.
- #182: frozen 495-row production snapshot and exact query; 20 evidenced candidate
  rows / 3 categories / 2 providers, with 380 unknown-location and 281
  unknown-age rows retained (overlapping sets). Fixed review cohort: seven IDs.

Local verification: Python 261 run, 13 skipped (248 passed); Node full suite 178
passed before the additional real SQL renewal test, which also passes (179 total
distinct Node checks). TypeScript and production webpack build pass. New dedicated
hosted checks cover collection/renewal/eligibility/identity and normal build.

External geocoding was rejected by automatic approval review; no postcodes were
sent. Reused coordinate evidence already held for visible public venues at the
same complete postcode. No hidden venue coordinate is included in the snapshot.
Free-text/outward-only/ambiguous/boundary locations stay unknown. This alternative
fully preserves the diagnostic scope; no further geocoder approval is required.

Still required before ticket acceptance: hosted checks, concrete owner release /
MyLibrary conservative-retention / diagnostic decisions and applicable production
or read-only verification. No observation gate has been weakened. #196 remains
open at 18 committed / 0 accepted until acceptance evidence is recorded.

### Engineering self-evaluation

Accuracy 4/5: offline and live read-only data support the claims; future scheduled
behaviour is not verified. Completeness 3/5: code/evidence prepared, owner/release
and production gates remain. Clarity 4/5: one seven-record review pack separates
diagnostics from pilot acceptance. Actionability 4/5: exact release/policy scope
and rollback are ready. Conciseness 4/5: detailed evidence stays in artefacts.
Overall 3.8/5. Priorities: finish hosted checks, obtain the concrete remaining
owner decision, then verify release and close only qualifying tickets. The user
would likely agree with implementation readiness, not an unsupported closure claim.

---

## Current scope and first implementation checkpoint

Owner approved 18 points: #180 (5) → #183 (3) → #181 (5) → #182 (5). Sprint 9
tracker #197 is planned for existing #125/#129/#132 observations. #195 is separate
unestimated backlog. These assignments supersede the initial 8-point baseline below.

#180 now has a local append-only selected-source manifest/outcome ledger, explicit
unprocessed tail, separate validation/save/health/public-view evidence and bounded
20-key public-view readback. The Activities workflow uploads the evidence even on
failure and runs the new regressions. Details: activities-collection-evidence.md.

Eight new evidence/run-loop tests pass. Full local Python suite: 253 run, 13 skipped,
exit 0; 240 passed. Existing Activities ingestion (15) and Gemini controls (11) also
pass independently. No hosted check, release, production run or browser acceptance
is claimed. Existing unrelated workspace edits were preserved. 18 committed / 0
accepted; all four delivery tickets remain open.

---

## Historical initial commencement baseline

Tracker: [#196](https://github.com/imransinvestments-prog/Dadspace/issues/196). Started; 8 active delivery points, 0 accepted. Observation: 9 existing points; #195 unestimated.

## First work completed
Reconciled live #187/#124/#125/#129/#132/#180/#183/#195, preserved original acceptance, assigned current Sprint 8 lanes and linked the Sprint 7 observation handoff. #180 is the first active implementation story; #183 is next.

Inspected daily-workers.yml, original-content.yml and collect-activities.yml. Activities executes events_worker.py with shared worker.py, separately from civic. The normal scheduler calls it at 07:17/19:17 London, with a source limit of zero (all selected sources), four detail pages and a 60-minute collector bound. The workflow uploads activities-usage-{run_id}-{run_attempt}, but missing usage artifacts only warn. An orchestration success therefore cannot alone prove source coverage or item outcomes.

Existing clean_events statistics, source health, usage report and source-backed Sprint 5 failure cohort are the first reuse targets for #180. Existing identity_key/content_hash/dedupe triggers are #183's baseline. Selected initial investigation cohort: the existing eight-record Sprint 5 failure cohort, bounded by its actual source IDs; this is not a new pilot quality sample or current source verification.

## Next implementation
Trace usage-report fields through events_worker.py/worker.py, map missing per-source outcome/coverage fields, then implement the smallest append-only evidence addition with partial-failure, suspicious-zero and unchanged fixtures. Finalise coverage semantics before rollout. Record source cohort IDs from the existing artefact rather than inventing them.

## Observation baseline
No new live scheduled-run audit was performed in this commencement. Prior 18 October missing dispatch evidence remains dated historical evidence, not a current live status claim. No qualifying seven-day window or acceptance start is declared.

Expected-slot contract from inspected workflow configuration:
- Daily workers, including Activities and Deals: daily 07:17 and 19:17 Europe/London.
- Originals: daily 07:17 and 09:17 retry, including weekly publication on Fridays.
- #124 accepted targets: dispatch +60 minutes; completion four hours; source-check age 36 hours.
- Slot evidence must include workflow SHA, scheduled event identity, expected slot, actual run/job, per-source yield/coverage, freshness and public readback, plus failure/recovery. Unavailable fields remain unknown.

Friday 23 October is a review checkpoint and next weekly Originals opportunity. A complete qualifying seven-day window may extend beyond it. #125/#132/#129 remain open until their full criteria pass.

