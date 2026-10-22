# Owner decisions — 22 October 2026

Everything open that is waiting on you, in the order that unblocks the most. Each item says what you are deciding, what I recommend, exactly how to act, and what it unblocks. Recommendations are defaults, not decisions: nothing below has been actioned for you.

**How to reply:** comment on the linked ticket starting with `Decision:` (for example `Decision: option B`). One line is enough; I'll pick it up from there.

## At a glance

| # | Decision | Ticket | Recommendation | Your time |
|---|---|---|---|---|
| 1 | Switch on the weather card | #223 | Create the Met Office key | 10 min |
| 2 | Fix late and missing scheduled runs | #124 #158 #157 #195 | Supabase timer (option A) | 15 min + token |
| 3 | Sprint 11 review | #212 #34 #92 #139 | Do the review screen | 1–2 h |
| 4 | Blocked council sites (Ealing, Merton) | #134 #201 | Record as gaps; ask operators | 5 min |
| 5 | Teen events exclusion bug | #101 | Un-skip and fix | 1 min |
| 6 | NCT refresh cadence | #104 | Weekly, after #201 | 1 min |
| 7 | Search Console and real-visitor speed | #141 | Grant access; check Speed Insights | 10 min |
| 8 | Geography in production | #206 #207 | Apply GB reference; keep NI out | 5 min |
| 9 | Activities quality scoring | #135 #136 #40 | After #201; schedule a session | 2 h, later |
| 10 | AI provider and cost work | #66 #145 #143 #144 | Defer | 1 min |
| 11 | Hounslow library activation | #133 | Decide after qualification | 1 min, later |
| 12 | Community beta | #41 #42 #43 #117 | Stay deferred | 1 min |
| 13 | Next engineering sprint | #146 #147 #149 | Commit after 2 and 3 | 10 min |

---

## 1. Switch on the weather card (#223, PR #224)
Built and merged, but switched off until a key exists.
1. Register at https://datahub.metoffice.gov.uk and subscribe to **Site Specific (Global Spot)** on the **free** plan.
2. Copy the API key. In Vercel → Project → Settings → Environment Variables, add `MET_OFFICE_DATAHUB_API_KEY` for Production and Preview, then redeploy.
3. Check the DataHub terms for the exact attribution wording. The card currently says "Forecast: Met Office"; tell me if it must say something else.

**Unblocks:** #223 acceptance. **Cost:** free (360 calls/day; the code shares forecasts per area for 3 hours to stay inside it).

## 2. Fix late and missing scheduled runs (#124, #125, #129, #158, #157, #195)
**Problem:** since 15 October, GitHub has started every scheduled run 2.5–7 hours late, and the Originals 07:17 slot never runs (evidence on #124; check any time with `python scripts/schedule-ledger.py --days 7`). This blocks every seven-day reliability gate, and the Morning Brief has the same root problem.

| Option | How it works | Trade-offs |
|---|---|---|
| **A. Supabase timer (recommended)** | `pg_cron` in your existing Supabase database calls GitHub's "run workflow" API at the exact slot times. The token is kept in Supabase Vault. | No new vendor; precise timing; both extensions are available but not yet installed. Needs a GitHub token with **Actions: write on this repository only**. |
| B. External cron service | A service such as cron-job.org calls the same GitHub API. | Quick, but a third party holds the token. |
| C. Accept the lateness | Relax #124's 60-minute dispatch target. | No work, but the evidence and brief stay late; Originals keeps missing 07:17. |

**Decided 22 Oct: option A.** Built in #226; the setup runbook is [scheduled-dispatch-timer.md](./scheduled-dispatch-timer.md). The original outline, for reference:
1. GitHub → Settings → Developer settings → Fine-grained tokens → create a token with repository access to **Dadspace only** and the permission **Actions: Read and write**. Expiry: 90 days.
2. Reply `Decision: option A` on #124. I'll prepare a migration that installs `pg_cron`/`pg_net`, a Vault secret placeholder and the slot schedule, plus the ledger check. You paste the token into Vault yourself (Supabase → Project → Vault → New secret); I never see it.
3. While both triggers exist, a late GitHub run would queue behind the timer's run (the concurrency group queues; it doesn't cancel). The migration therefore adds a "slot already ran" check, and once the timer has been proven for a week we remove the GitHub `schedule:` triggers.

**Unblocks:** #124, #125, #129, #132 timing; it also gives #157/#158 a delivery route and #195 an independent overdue check from the same timer.

## 3. Sprint 11 review (#212 → #34, #92, #139)
The protected review screen is live on the #212 preview at `/ops/sprint-11` (sign in as owner). It needs:
- **50-venue rubric labels** (#34): mark each sampled venue as correct, wrong or unsure on identity, location and evidence.
- **105 library-detail proposals** (#92): accept or reject each sourced fact (official link, opening hours, access).
- **Area/category publication** (#139): choose which candidate pages may be published.

Do them in that order; saved decisions are kept if you stop part-way. **Unblocks:** most of Sprint 11's 32 provisional points.

## 4. Blocked council sites — Ealing and Merton (#134, #201)
Both return HTTP 403 to the hosted collector. Bypassing that is off the table.
- **A (recommended).** Record Ealing and Merton as explicit access gaps, release #201's other work, and ask each library service for permission or a feed. I can draft the emails for you to send.
- **B.** Keep #201 blocked until access is granted.

**Unblocks:** #201 (identity, matching and safety gates) and with it #104, #135, #136 and #40.

## 5. Teen events exclusion bug (#101)
`lib/events.ts` drops any event mentioning "teen", including mixed-age family events, even though the Events page has a 12+ filter. It was skipped on 16 October. It's a 2-point fix with tests; only genuinely ambiguous cases would come back to you.
**Recommendation:** `Decision: un-skip`.

## 6. NCT refresh cadence (#104)
NCT supplies about 96 activities but only refreshes when run by hand.
**Recommendation:** weekly (Monday morning, through the timer in item 2), once #201's occurrence-preserving writer is released. Reply with the cadence you want.

## 7. Search Console and real-visitor speed (#141)
- Search Console: add the property for `dad-space.co.uk` (if it isn't already) and add read access for whoever records evidence.
- After a few days of traffic, open Vercel → Speed Insights → Mobile and send me the LCP p75 figure (or a screenshot). The lab mobile result is unreliable (bimodal, 3–9 s); real-visitor data decides #141.

## 8. Geography in production (#206, #207)
The UK geography reference (ONS May 2026, Sprint 10) is released in code, but its database migration has not been applied to production, so #206 cannot start.
- **Recommendation:** approve applying the migration with the existing GB sample, keeping Northern Ireland postcode data out until there is an authorised basis (as you agreed on 19 October). Wider postcode coverage (#207) stays backlog until its licence terms are checked.
- Reply `Decision: apply geography migration` on #206.

## 9. Activities quality scoring (#135, #136, #40)
These wait for #201 (item 4). When ready, they need one scheduled session from you: the 19-record historical correction cohort (#135), scoring the 100-activity sample (#136) and the breadth target of 10 actionable activities across 3 categories and 2 providers per area (#136/#123). Nothing to do today; this is a heads-up to book the time.

## 10. AI provider and cost work (#66, #145, #143, #144)
These need paid evaluation runs and your choice of provider. Gemini stays the default.
**Recommendation:** defer until scheduling (item 2) is fixed, so that cost measurements come from reliable scheduled runs. Reply `Decision: defer` on #145.

## 11. Hounslow library activation (#133)
The adapter qualification is in draft PR #84. Activation is your separate yes/no once its evidence is current. No action today.

## 12. Community beta (#41, #42, #43, #117)
34 points, needing a named moderator.
**Recommendation:** stay deferred until the discovery pilot is accepted. Reply `Decision: stay deferred` on #117.

## 13. Next engineering sprint (#146, #147, #149)
These are design-ready engineering tickets: source and worker maintenance actions (11 points), editorial queues (8) and upkeep acceptance (8).
**Recommendation:** commit them as the next sprint once items 2 and 3 are done, so their acceptance can use reliable scheduled evidence.

---

## Not waiting on you
- **Observation windows:** #125, #129 and #132 need real scheduled runs, so they gather evidence automatically. #132 should start passing now that Matalan is paused.
- **Parent and tracking tickets:** #29, #48, #70, #113–#121, #197, #198 and #211 close when their children close.
- **Housekeeping:** an untracked `.clauderules.md` appeared in the repository on 22 October. I did not create it and have left it untouched. Tell me whether to commit it or ignore it.
