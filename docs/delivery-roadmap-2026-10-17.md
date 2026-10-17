# Proposed delivery roadmap — 17 October 2026

## Current sequencing — Sprint 6 approved

After Sprint 5 closure, the owner requested News and Deals before Activities and approved starting News first. Sprint 6 [#185](https://github.com/imransinvestments-prog/Dadspace/issues/185) commits #146 (11), #147 (8), #129 (3): **22 points**. See [Sprint 6 plan](./sprint-6-plan.md). Deals follows with #131 (13), #148 (8), #132 (3), subject to refinement and its scheduled evidence dependency. The old numbered slots below are historical and superseded for ordering; they are not current commitments.

Activities engineering remains queued. #125 retains all seven-day cross-feed criteria, including Activities collections; News-specific evidence can be captured and reused without claiming #125 closure. Wider #149 and #44 handover remain outside Sprint 6. No new provider/source activation or paid run is authorized by this sequencing.

## Delivery update after Sprint 5

The owner approved this roadmap through PR #177. Sprint 5 (#178) is complete: 24 committed /24 accepted /zero remaining, following the recorded sprint review. See [closure](./sprint-5-closure.md). New, separately estimated Activities foundation stories #180 (5), #181 (5), #182 (5), #183 (3) were refined during discovery and remain provisional backlog outside Sprint 5. They must be sequenced and reconciled with source qualification/matching before the old Slot 7 final Activities acceptance; later slot numbers below remain conditional placeholders, not commitments. No next sprint is started.

The initial 207-point known backlog plus 18 refined residual points, less 24 accepted in Sprint 5, leaves **201 provisional known remaining points**, including the previously deferred estimated items. This excludes unestimated Morning Brief implementation and further source/Activities findings; it is not a calendar forecast. The initial proposal below remains an auditable planning snapshot.

Status: proposal for owner review; no new sprint or implementation has been started. Replaces earlier delivery forecasts for planning purposes; historical issue notes remain an audit trail.

## What recent delivery tells us

| Closed sprint | Accepted points | Evidence |
| --- | ---: | --- |
| Small discovery / Sprint 2 | 11 | [#169](https://github.com/imransinvestments-prog/Dadspace/issues/169): #94, #95, #96, #98, #140 |
| Places data / Sprint 3 | 5 | [#171](https://github.com/imransinvestments-prog/Dadspace/issues/171): #162, #100 |
| Discovery assurance / Sprint 4 | 20 | [#174](https://github.com/imransinvestments-prog/Dadspace/issues/174): #33, #89, #137, #138 |

These 36 accepted points are evidence of completed scope, not a weekly velocity. The periods, risks and human review loads differ; much delivery happened within 16–17 October. Earlier #87/#88 and the #91/#93/#90/#97/#102/#103 batch must not be retrospectively counted as committed scope in these three sprints.

Sprint 4 retrospective: Imran reported a good plan, all goals achieved, no scope creep and minimal intervention. Continue bounded goals, autonomous routine decisions and one consolidated owner review. Earlier ECC setup and review-interface preparation took too long; prepare evidence and plain-language review tasks during refinement. Hold a sprint review after every closure, before committing the next sprint.

A larger sprint should increase coherent scope, not uncertainty. Use a **25-point planning ceiling**, with no automatic stretch commitments or padding. Do not convert points to dates until we have comparable cadence and know the Activities work.

## Backlog accounting

The pre-refinement snapshot contains **46 open issues**, including **34 positive-estimate delivery tickets totalling 204 provisional points**. Parent/epic rollups are excluded. Some estimates cover partly delivered scope and need re-estimation (#126 in particular); #157 implementation is unestimated.

New bounded discovery [#176](https://github.com/imransinvestments-prog/Dadspace/issues/176) adds 3 provisional points: **47 open issues and 207 known provisional points** after its creation. This is not an estimate of all remaining delivery: additional Activities engineering, Morning Brief implementation and newly discovered work remain unknown.

## Roadmap and proposed sprint slots

Only Sprint 5 is proposed for commitment now. Asterisked slots are dependency-based ordering placeholders, not fixed dates or approved commitments. If #176 finds more Activities engineering, insert explicitly estimated Activities sprints before its acceptance stage and renumber subsequent slots. Independent places/deals work can move forward while external access or reliability evidence is pending.

| Slot | Outcome | Tickets / story points | Total |
| --- | --- | --- | ---: |
| 5 | Evidence, thresholds and current content | [#176](https://github.com/imransinvestments-prog/Dadspace/issues/176) (3), [#122](https://github.com/imransinvestments-prog/Dadspace/issues/122) (5), [#123](https://github.com/imransinvestments-prog/Dadspace/issues/123) (2), [#124](https://github.com/imransinvestments-prog/Dadspace/issues/124) (3), [#127](https://github.com/imransinvestments-prog/Dadspace/issues/127) (3), [#126](https://github.com/imransinvestments-prog/Dadspace/issues/126) (3), [#130](https://github.com/imransinvestments-prog/Dadspace/issues/130) (5) | 24 |
| 6* | Controlled source operations and qualified Activities supply | [#146](https://github.com/imransinvestments-prog/Dadspace/issues/146) (11), [#104](https://github.com/imransinvestments-prog/Dadspace/issues/104) (3), [#133](https://github.com/imransinvestments-prog/Dadspace/issues/133) (3), [#134](https://github.com/imransinvestments-prog/Dadspace/issues/134) (8) | 25 |
| 7* | Activities correctness and sustained reliability | [#40](https://github.com/imransinvestments-prog/Dadspace/issues/40) (8), [#135](https://github.com/imransinvestments-prog/Dadspace/issues/135) (5), [#136](https://github.com/imransinvestments-prog/Dadspace/issues/136) (5), [#125](https://github.com/imransinvestments-prog/Dadspace/issues/125) (3), [#129](https://github.com/imransinvestments-prog/Dadspace/issues/129) (3) | 24 |
| 8* | Trusted places and local discovery | [#34](https://github.com/imransinvestments-prog/Dadspace/issues/34) (8), [#92](https://github.com/imransinvestments-prog/Dadspace/issues/92) (5), [#139](https://github.com/imransinvestments-prog/Dadspace/issues/139) (5), [#141](https://github.com/imransinvestments-prog/Dadspace/issues/141) (5) | 23 |
| 9* | Useful priority deals and maintenance | [#131](https://github.com/imransinvestments-prog/Dadspace/issues/131) (13), [#148](https://github.com/imransinvestments-prog/Dadspace/issues/148) (8), [#132](https://github.com/imransinvestments-prog/Dadspace/issues/132) (3) | 24 |
| 10* | Editorial operations and discovery handover | [#147](https://github.com/imransinvestments-prog/Dadspace/issues/147) (8), [#149](https://github.com/imransinvestments-prog/Dadspace/issues/149) (8), [#44](https://github.com/imransinvestments-prog/Dadspace/issues/44) (5) | 21 |
| 11* | Provider comparison and production efficiency | [#66](https://github.com/imransinvestments-prog/Dadspace/issues/66) (8), [#145](https://github.com/imransinvestments-prog/Dadspace/issues/145) (8), [#143](https://github.com/imransinvestments-prog/Dadspace/issues/143) (5), [#144 S1](https://github.com/imransinvestments-prog/Dadspace/issues/144) (2) | 23 |
| 12* | Qualified deterministic adapter delivery | [#144 S2](https://github.com/imransinvestments-prog/Dadspace/issues/144) (5) | 5 |
| Community A | Architecture, persistence and moderation foundations | [#41](https://github.com/imransinvestments-prog/Dadspace/issues/41) (8), [#42 S1](https://github.com/imransinvestments-prog/Dadspace/issues/42) (5), [#43 S1](https://github.com/imransinvestments-prog/Dadspace/issues/43) (5), [#43 S2](https://github.com/imransinvestments-prog/Dadspace/issues/43) (5) | 23 |
| Community B | Reconnect, operational safeguards and accepted beta | [#42 S2](https://github.com/imransinvestments-prog/Dadspace/issues/42) (5), [#43 S3](https://github.com/imransinvestments-prog/Dadspace/issues/43) (3), [#42 S3](https://github.com/imransinvestments-prog/Dadspace/issues/42) (3) | 11 |
| Deferred | Owner-deferred scope | [#101](https://github.com/imransinvestments-prog/Dadspace/issues/101) (2), [#158](https://github.com/imransinvestments-prog/Dadspace/issues/158) (2) | 4 |

The allocation totals 207 points, including deferred items. Whole-ticket allocations include their existing component stories exactly once. #144, #42 and #43 are split explicitly above. The five-point adapter slot is conditional on a qualified candidate, not a promise to fill a sprint; pull it forward when dependencies and capacity permit. Community's 34 points remain conditional on an explicit decision to start.

## Sprint 5 proposal — trustworthy evidence and a realistic Activities plan

**Goal:** establish agreed quality evidence, improve existing News/Deals and expose the true Activities reliability scope. **24 provisional points**, leaving one point unallocated.

Sequence #122's frozen cohort and evidence pack → #123's unresolved thresholds → #130's Deals acceptance. Run #124 monitoring investigation, #127 News corrections and #176 Activities discovery alongside that work where independent. #126 closes on existing accepted News evidence plus targeted fixes; refresh its remaining estimate rather than repeating completed work. Freed capacity is not automatically new scope.

Done means: stable sample manifests and review instructions; documented thresholds/denominators; tested late/missing-run signals; bounded News correction evidence; Deals acceptance or clearly recorded failed criteria; an Activities decomposition with estimates, unknowns and proposed gates. A failing quality gate keeps its ticket open rather than being waived to finish the sprint.

## Activities is an existing epic, not a five-point fix

Use [#114](https://github.com/imransinvestments-prog/Dadspace/issues/114) as the epic. #176 maps source → extraction → programme/session identity → venue matching → persistence → freshness/cancellations → public results. It distinguishes proven failures from hypotheses and produces bounded vertical stories with repeat-import tests, rollback needs, dependencies and reviewer workloads.

Reuse #90/#91/#93; do not rebuild already accepted schedule and card behaviour without evidence. Source qualification (#104/#133/#134), matching (#40), historical cleanup (#135) and final acceptance (#136) are distinct deliverables. #120 source-inventory and coverage work must be explicitly costed, not hidden in a zero-point parent.

The current #136 estimate funds acceptance of a **100-record Activities cohort**, not all pipeline engineering. The proposed 10 distinct actionable activities / three categories / two providers breadth gate still needs agreement in #123. If discovery finds new identity, extraction, scheduling, cancellation or migration work, add it and revise the roadmap before committing implementation. Do not promise that all Activities work fits Slots 6–7.

Preserve W3 9LN / 10km / ages 0–5 as the pilot contract, useful national/wider-age supply, and unknown facts. Source access failures are not evidence that content is unsuitable. No consent/robots/403 bypass; source activation and paid extraction remain explicit decisions.

## Dependencies and release evidence

- #124 precedes #125. Start the real seven-day reliability window only when the relevant fixes and collection configuration are stable. Keep an expected-slot ledger with extraction, accepted/rejected counts and public readback. Manual runs cannot replace scheduled evidence.
- Reuse one qualifying evidence window across #125/#129/#132/#136/#44 rather than demanding four separate weeks. Each ticket still needs its own acceptance evidence: e.g. at least three successful scheduled Activities collections and two consecutive scheduled Deals runs. Changes/failures require an explicit new or extended window; waits may straddle sprints.
- #40 precedes #135 and #136. Preserve useful unmatched/private-location listings. Keep the 19-record/201-proposal historical subset separate from the wider 191-record queue; larger cleanup is not included by implication.
- #34 follows the sampling/rubric work and delivered #33; #139 follows validated venue coverage and an agreed geographic scope. Resolve Hounslow plus two areas versus the fixed pilot before publishing expansion pages.
- #141 requires representative performance evidence and owner Search Console access where needed. Lab/API checks can finish before sufficient field data exists; report the outstanding field gate without inventing historical baselines or instant indexing.
- #149 follows the delivered desk plus #40/#146/#147/#148; #44 follows accepted discovery quality and upkeep evidence. Disabled Community does not block discovery handover.
- #66 rollout follows #145 quality/cost evidence. Keep Gemini until a switch is approved; no unapproved paid benchmark runs or spending-cap changes. #144 requires a real qualifying deterministic source, not JSON-LD alone.
- Inspect/reuse existing draft PRs #84 (Hounslow), #69 (providers) and #8 (Speed Insights) under their owning tickets. They are evidence/work in progress, not additional points or automatic merge approvals.

## Human review and decision budget

Collect decisions into one clearly indexed pack at each sprint's preview, with recommended defaults, exact rows/links, before/after effects and rollback notes. Ask early only for a genuine blocker or required external authorization.

| Area | Existing evidence and expected human work |
| --- | --- |
| Sampling #122 | Prepare fixed IDs/fingerprints: 50 venues, 100 Activities, up to 100 Deals or the actual smaller agreed pool. Preparation is not a demand to review 250 records in Sprint 5. Stage reviews with each owning feature. |
| News #126/#127 | Preserve the completed 50-record review and its 46/50 relevance, 48/50 working destinations. Review only ambiguous/changed records from the existing 18-record correction register; publish the exact changed subset. No repeat full 50. |
| Deals #130 | Review the agreed published sample and top 20 (or smaller agreed pool). Reuse overlapping rows once. Confirm truthful terms, availability, expiry and value; do not lower the denominator silently. |
| Activities #176, then #136 | Sprint 5 reviews the failure analysis and proposed breakdown, not 100 final records. Publish exact discovery cohort size before asking for labels. Later reuse the frozen 100-record cohort, with targeted changed-row rechecks. |
| Venues #34/#92 | Use the shared 50-venue cohort; validate every newly proposed publication and source/photo rights. Additional library-specific changes get their own bounded manifest. Preserve previous owner approvals. |
| Historical corrections #135 | Review the frozen 19-record subset and explicit proposals, not an unexplained 191-record queue. |
| Originals #129 | Keep the existing approval of six articles; validate scheduled operation, not another editorial re-score. |
| Operations/security | Reviewer access remains owner-only. Maintenance powers are separate: approving a review role does not authorize activation, retries, paid calls or administrative powers. |
| Community | Explicit go/no-go, access model, moderator capacity, costs and beta safeguards before implementation/release. |

Sprint 5's consolidated decisions: unresolved quality thresholds and smaller-pool rules; ambiguous News corrections; Deals judgments; freshness expectations; Activities decomposition and its next-sprint scope. Final record counts depend on the frozen manifests and changed-row sets, and must be stated before user review.

## Parent coverage and deferred work

- #29 programme: close only when the explicitly agreed programme outcome and handover are accepted; this roadmap does not silently remove deferred scope.
- #113 trusted places: #34/#92/#139/#141; #119 SEO tracks #139/#141 alongside already closed work.
- #114 Activities: #176, #104/#133/#134, #40/#135/#136 and additional discovery-created work. #120 tracks source coverage; #121 tracks identity/schedule/card work, including remaining #101/#135 and already delivered #90/#91/#93.
- #48 Deals: #130/#131/#132 and related maintenance #148.
- #115 News/Originals: #126/#127/#129 and related maintenance #147.
- #70 operations: #122/#123/#124/#125/#146/#147/#148/#149, with #44 handover.
- #116 AI efficiency: #66/#143/#144/#145.
- #117 Community: #41/#42/#43, after discovery stability and an explicit owner choice.
- #101 remains owner-skipped. #158 Morning Brief discovery remains deferred; #157 implementation is unestimated until a solution is selected. Neither is included in an active sprint. No email sends, service purchases or subscriptions are implied.

## How we will track delivery

At commitment freeze the scope/story points and dependencies. Record accepted remaining points after each acceptance event, with timestamps; show scope additions separately. The ideal burndown needs actual agreed sprint dates. Do not draw a fabricated smooth historical burndown or treat code completion as acceptance.

At closure review outcomes versus the original goal, defects, carryover, reviewer effort, real elapsed waits and owner feedback. Update remaining estimates and the roadmap, then commit the next sprint. Re-plan when Activities discovery changes size, quality gates fail, a source cannot be accessed lawfully, or required field/operational evidence is unavailable.
