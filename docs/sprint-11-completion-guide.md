# Sprint 11 — step-by-step completion guide

Use with the [review pack](sprint-11-review-pack.md). Engineering and browser verification results are recorded in the [current verification report](sprint-11-verification.md). The hosted [review preview](https://dadspace-git-dev-sprint-11-reliability-imransinvestments-6859.vercel.app/ops/sprint-11) is live and signed-in owner rendering has been checked. Unchecked boxes below retain the full acceptance sequence; they are not a claim that verified engineering work is still unattempted.

## 1. Freeze the review version — engineer

- [ ] Confirm branch `dev/sprint-11-reliability`; inspect every modified/untracked file and distinguish Sprint 11 changes from other work.
- [ ] Refresh tracker #211 and child issue states; reconcile already accepted work without awarding duplicate points.
- [ ] Preserve this pack's evidence/manifest. Record exact code SHA, configuration hashes, capture times and all known gaps for the next review version.
- [ ] Check that the fixed venue cohort still contains the same 50 UUIDs. Keep changed records visible; do not substitute easier examples.

Exit: one coherent version with a complete inventory and no unexplained scope additions.

## 2. Finish venue review #34 — owner/reviewer with engineer

- [ ] On the verified signed-in preview open `/ops/sprint-11`, then the fixed venue review at `/ops/reviews/34`.
- [ ] Inspect each of the 50 records against its current official source. Record identity, location, usable source, access, factual information and image rights separately. Unknown remains unknown.
- [ ] Score joint identity/location/source passes against all 50 rows. Require at least 48 passes. Independently demonstrate zero hidden-record leakage.
- [ ] For failures, retain original evidence and create bounded before/after correction proposals with UUID, source URL/date and current fingerprint. Re-review corrected evidence; never reduce the denominator.

Exit: completed rubric, score, leakage result and exact correction queue. If below threshold, leave #34 open with failed IDs and next actions.

## 3. Review library facts #92 — owner/reviewer with engineer

- [ ] Filter/search all 105 candidates in `/ops/sprint-11`; only 20 display at once, so do not stop at the first page of results.
- [ ] Confirm each proposal points to the correct official branch/address, not only an authority directory. Check public access, hours, holiday exceptions, charges and suitability where actually evidenced.
- [ ] Inspect Hounslow Library and both restricted-access candidates explicitly. Retain archives/restricted institutions as distinct review outcomes.
- [ ] Record accept/reject/unknown per proposal with current source and before fingerprint. Use clear unknown visitor information where unsupported.
- [ ] Engineer verifies guarded edits preserve reviewed fields, reject stale/changed/hidden records, and handle repeated application safely using actual handlers/SQL. Keep the migration staged for dev review.

Exit: every candidate has a documented disposition; accepted proposals are precise and reviewable. No production application implied.

## 4. Decide pilot pages #139 — owner, then engineer

- [ ] Review exact in-pilot options: Hounslow and proposed Ealing/Brent alternatives. Keep W3 9LN / 10 km / ages 0–5 fixed; Manchester requires separate expansion scope.
- [ ] Choose the area approach in the pack's decision log.
- [ ] Engineer supplies exact page URLs, full UUID cohorts, current fingerprints and distinct copy. Resolve bounded/incomplete evidence before approval.
- [ ] Review and approve each complete cohort separately after #34/#92 evidence is usable.
- [ ] Verify approved unchanged cohorts behave as intended; unapproved, changed, thin, hidden and incomplete cases remain noindex and absent from sitemaps. Browse/detail pages must still work.

Exit: explicit page/cohort decisions and demonstrated publication gate, without inferred national expansion.

## 5. Complete engineering and preview checks — engineer

Run from the `sprint11` directory, using the installed project toolchain. Capture dated output and code SHA; resolve failures rather than marking checks assumed. Review database tests before running: use the disposable fixture database, never production.

```powershell
pnpm exec tsc --noEmit
pnpm build
node --test tests/*.test.cjs tests/*.test.mjs
python -m unittest discover -s tests -p "test_*.py"
```

- [ ] Check all applicable repository CI workflows, including guarded operations PostgreSQL 17 transaction tests in `.github/workflows/operations-review-checks.yml`. Record skips and environment limitations explicitly.
- [ ] Test actual visitor-fact edit permissions, accepted/rejected edits, stale fingerprints, repeat application and hidden/unknown records.
- [x] Create the draft PR and hosted preview; record URL and exact deployed SHA. [PR #212](https://github.com/imransinvestments-prog/Dadspace/pull/212) and signed-in preview verified. Hosted GitHub checks remain queued and are not counted as passes.
- [ ] Anonymous `/ops/sprint-11` redirects to sign-in without leaking evidence; authorised owner sees the pack; unauthorised users cannot read or mutate records.
- [ ] Owner tests mobile layout, keyboard navigation, location selection, deep pagination, venue details and useful unknown visitor information. Log each defect and verify its fix.

Exit: current verification report with real results and a usable preview, not merely local code presence.

## 6. Verify performance #141 — engineer; owner supplies access if available

- [ ] Preserve production baseline: 120 API samples and 24 lab runs. Record route/device, sample counts, conditions, SHA and raw measurements.
- [ ] Measure the preview after the install-banner change with comparable three-run mobile/desktop medians and API p95/payload checks. Inspect the existing capture scripts before choosing target configuration; do not overwrite the baseline.
- [ ] Compare against the ticket's recorded thresholds. Mobile LCP currently misses target; fix and remeasure if still failing.
- [ ] Obtain Search Console property evidence and representative field data when accessible. Otherwise record capture date, unavailable reason, responsible person and next action. Do not substitute lab TBT for field INP or close an evidence gate without its accepted criterion.

Exit: reproducible before/preview comparison and explicit outstanding external-data state.

## 7. Complete actual scheduled observation #125/#132/#129 — engineer

- [ ] Preserve the existing stable-release anchor `31b8c1f` and first-full-day basis of 18 October unless an evidenced configuration/release change requires an explicitly documented eligibility boundary. Do not silently restart or backfill the window.
- [ ] Archive existing captures, then refresh read-only scheduled metadata and recompute the ledger with the existing scripts:

```powershell
python scripts/capture_sprint11_runs.py
python scripts/sprint11_schedule_ledger.py
```

These scripts update local snapshot files. They do not by themselves prove worker/source/publication linkage. Inspect their current anchor and configuration assumptions before relying on the output.

- [ ] Resolve the latest observed failure first: Deals has an expired Matalan terms review; News had nine upstream Google RSS 503 responses. See the retained operational findings in the verification report. Do not renew review dates without current terms evidence or replace a source silently.
- [ ] For each expected Europe/London slot retain trigger occurrence, run ID/attempt/SHA, configuration eligibility, parent/child/source linkage, completion and public readback. Distinguish missing, late, skipped, failed, unknown and future-not-due.
- [ ] Apply accepted warning boundaries: dispatch 60 minutes, completion four hours, source check 36 hours. Successful jobs cannot fill multiple slots. Keep DST handling correct across 25 October.
- [ ] #125: establish all seven eligible days across feeds and three successful normal scheduled Activities collections. Reconcile every slot; date passage alone is insufficient.
- [ ] #132: prove consecutive eligible Deals runs, offer identity/freshness/terms and public readback. Explain the 17-to-19 offer delta without reopening unchanged accepted content.
- [ ] #129: retain daily and actual Friday/09:17 publication evidence, duplicate handling and genuine retained failure/recovery evidence after the stable release. Next Friday opportunity is **23 October 2026**, not a guaranteed completion date. Do not induce a production failure to manufacture evidence.

Exit: per-ticket observation conclusions supported by actual evidence. Leave failed/unknown gates open with a next action; manual reruns do not replace scheduled success.

## 8. Assemble the final review version — engineer

- [ ] Consolidate all decisions, correction proposals, test output, preview measurements, exact URLs/UUIDs, source links, hashes and observation results in the pack.
- [ ] Run the delivery plan's required ECC Blueprint adversarial review of completeness, dependencies, access/licensing, denominators and concrete owner tests; fix findings and record the outcome.
- [ ] Update review wording to distinguish engineering-ready, owner-accepted, deployed and observed. Keep points provisional until justified.
- [ ] Commit only reviewed intended changes; verify a clean branch, draft PR, required checks and preview. Record their links/SHA.
- [ ] Obtain owner acceptance of the concrete dev review and decisions. Any outstanding waiting/access items remain explicitly open; partial engineering acceptance is not full sprint closure.

Exit: reviewable dev handoff. This is the current authorised delivery endpoint.

## 9. Close or carry forward transparently — owner and engineer

- [ ] Close each ticket only when its own acceptance evidence exists; update #211 from child outcomes without parent point duplication.
- [ ] For remaining Friday/seven-day/access gates, record blocker, retained evidence, responsible person and next eligible check. Do not label the sprint fully complete while required gates remain unmet.
- [ ] If a production release is wanted, prepare a separate concrete release scope with migration/data changes, rollout, rollback and readback for approval. This guide does not authorise merge or production application.

Completion record: review date ___; code SHA ___; preview/PR ___; owner decisions ___; #34 ___; #92 ___; #139 ___; #141 ___; #125 ___; #132 ___; #129 ___; open carry-forward ___ .
