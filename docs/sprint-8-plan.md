## Sprint 8 — Activities reliability foundation (18 points)

Completed 18 October 2026: 18/18 bounded delivery points, PR #199 merged/production
verified. Current acceptance record: [sprint-8-closure.md](sprint-8-closure.md).
The plan below is retained as planning history; Sprint 9 observation remains open.

The owner approved the expanded scope and Sprint 9 observation split on 18 October 2026. This current plan supersedes the initial 8-point plan preserved below.

- #180 (5): source/run evidence; first active implementation.
- #183 (3): identity/session replay and bounded repair design.
- #181 (5): one existing adapter family, covered-item renewal only; concrete family/retention review before rollout.
- #182 (5): reproducible W3/10km/0–5 eligibility and breadth ledger, explicit unknowns.

Sequence: #180 → #183 → #181 → #182. One implementation active; no automatic stretch. 18 committed / 0 accepted. Close on immediate bounded delivery, tests, required review/release/readback. Sustained acceptance remains separately owned; no criterion is discarded for closure.

Observation tickets #125/#132/#129 (9 existing points) are provisionally assigned to Sprint 9 #197. Evidence can start as soon as stable released prerequisites qualify. Record SHA/configuration, eligible start, expected slots, required duration/events and failures/replacement decisions. No window is declared yet. #195 stays separate unestimated setup backlog, outside Sprint 8.

Current authoritative tracker: https://github.com/imransinvestments-prog/Dadspace/issues/196

---

## Historical initial plan — superseded by the 18-point plan above
**Status: Started — 18 October 2026 (Europe/London).** Authorised by Imran in chat. Engineering: Codex; acceptance owner: Imran. Review checkpoint: Friday 23 October; not a promised finish or acceptance date.

### Goal
Make Activities collection outcomes and programme identity demonstrable while preserving the real scheduled-observation gates for Deals and Originals.

### Active delivery: 8 points
- [ ] #180 — 5 points: append-only per-run/source outcomes and public readback. Start with existing collector evidence/usage artifacts; define extracted, rejected, accepted, unchanged, deferred, failed and incomplete coverage explicitly. Verify partial failures, suspicious zeroes and unchanged results without advancing freshness on failure. Reuse existing source IDs; no new schema or production write is implied.
- [ ] #183 — 3 points: bounded source-backed identity replay for renamed programmes, changed locations, distinct same-venue sessions and repeat imports. Reuse identity_key/content_hash/dedupe. Report reproduced defects and separately estimate any repair; no new identity system or historical correction included.
These existing estimates remain provisional until the first bounded fixture/source inventory. Replan explicitly if evidence changes scope; do not add work to preserve a point target.

### Carryover / observation lane — open, no guaranteed closure
- [ ] #132 — 3 existing unaccepted points, carried from Sprint 7 observation track: two consecutive normal scheduled Deals runs, stable identities/terms/expiry, public journeys and safe outage behaviour; still depends on #125.
- [ ] #125 — 3 existing unaccepted points: one shared qualifying seven-day window, every expected feed/source slot, at least three successful scheduled Activities collections, yield/freshness/public readback and every miss/recovery.
- [ ] #129 — 3 existing unaccepted points from Sprint 6: post-release daily/Friday and duplicate-safe 09:17 Originals retry plus retained runtime evidence. Friday 23 October is the next Friday opportunity, not closure.
- [ ] #195 — unestimated setup dependency: independent hosted missing-Originals alert. Begin provider/configuration discovery and prepare a concrete implementation; hosted scheduler/email setup and verified delivery remain necessary before acceptance. Preserve already authorised owner-only email intent.

8 active delivery points + 9 existing observation points are visible separately; #195 is unestimated. Accepted baseline: 0. Do not count parent roll-ups, prior deliveries or elapsed waiting as velocity.

### Execution and work in progress
1. Started: reconcile live tickets, accepted #124 targets and current workflow contracts; establish the Sprint 8 baseline and expected-slot ledger.
2. #180 first: inventory current evidence and select a bounded source cohort; reuse existing collection paths and build meaningful fixture checks. Agree coverage semantics before rollout.
3. #183 next: replay the selected source-backed identity cases. Keep one implementation story active, with at most one additional item awaiting external evidence/review.
4. Reuse the same observation ledger across #125/#132/#129. The 18 October missing/late slots remain failed historical evidence. Do not declare a passing or replacement window until configuration, full expected slots and eligibility are recorded and owner window decisions are resolved.
5. Prepare one consolidated review pack: exact changes, verification, unresolved gaps and any concrete release/configuration decisions. Preserve accepted content reviews.
6. Demonstrate/review accepted outcomes, carryover and actual points before closing the sprint.

### Known targets and constraints
Accepted #124 targets: dispatch warning after 60 minutes; completion after four hours; source-check warning after 36 hours. Daily workers: 07:17/19:17 Europe/London; Originals: 07:17/09:17, with Friday weekly slot. Use timezone-aware expected slots; record actual run SHA/event/run/job and source outcome, freshness/public readback, miss/recovery separately. Manual runs are supporting evidence only.

Sprint 7 #187 remains closed: 21/21 cumulative accepted after #131/S3 resolution; zero delivery carryover. #131/#148/#190 are not reopened or re-estimated. Earlier #146/#147 and broader #149 remain open in their existing backlog lanes, outside this sprint commitment.

Preserve W3 9LN /10km /0–5 and the discovery model. No invented ages/locations, source activation, provider switch, paid manual generation, speculative cron change, production repair or release is implied by sprint assignment. Prepare concrete changes for existing applicable owner gates. No background monitor is installed by this plan.


Tracker: https://github.com/imransinvestments-prog/Dadspace/issues/196

