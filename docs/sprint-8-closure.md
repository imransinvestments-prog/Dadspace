# Sprint 8 review and closure — 18 October 2026

**18 committed / 18 delivered and accepted / zero committed delivery carryover.**
Tracker: [#196](https://github.com/imransinvestments-prog/Dadspace/issues/196).
The owner requested completion of the bounded sprint. Closure records verified
engineering delivery under that instruction; no separate owner content scores,
inspection decisions or retrospective feedback are invented.

## Released outcome
[PR #199](https://github.com/imransinvestments-prog/Dadspace/pull/199) merged as
`d270ad255431ad951257080dc6b182c16410b618`. Production Vercel deployment succeeded.
The tested PR head was `255d1d73215a862215b082a4ab48602ed84246d5`; its source tree
exactly matches the merge tree. Unrelated existing workspace edits were excluded.

| Ticket | Points once | Closure evidence |
|---|---:|---|
| #180 | 5 | Append-only selected-source/run evidence, explicit deferred tail, validation/save/health/public-view separation, honest empty selection and inconsistent counters. Nine evidence/run-loop checks and real read-only ledgers. |
| #183 | 3 | Real repository SQL identity/trigger replay from recorded Cardiff rows: repeat, changed schedule, rename, move and distinct sessions. Bounded repair proposal #198; no identity rewrite or production repair was included. |
| #181 | 5 | Bounded MyLibrary detail coverage and accepted-row-only renewal evidence. Four adapter checks and a real SQL freshness-trigger check; live Sutton passes retain the same programme identity. Unseen/partial/failed/cancelled candidates are not automatically refreshed or withdrawn. |
| #182 | 5 | Full 495-row current-view snapshot and exact query, repeatable age/location ledger, existing-identity deduplication, explicit unknowns, provider/category evidence and fixed seven-record diagnostic cohort. No final pilot-quality acceptance claimed. |

## Verification
- Final local Python suite: **264 run; 251 passed; 13 skipped**.
- Node: **179 distinct checks passed** (178 full-suite checks plus the added SQL renewal check).
- TypeScript and production webpack build passed.
- Final hosted head: Activities foundation [39148283274](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39148283274),
  MyLibrary [39148283379](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39148283379),
  Deals [39148283257](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39148283257),
  SEO [39148283546](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39148283546),
  Gemini controls [39148283448](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39148283448):
  all successful, plus Vercel.
- Live Sutton: two real read-only passes, one accepted programme each, stable key
  `8bc6d342072a2ecbf94f35816ad6013e74561000`, zero model calls / database writes.
  Page hashes differ; same-hash/no-blanket-renewal behaviour is separately proved
  by fixtures and the real SQL trigger test, not fabricated as a live hash match.
- Three live files preserved under `artefacts/data/sprint8-live-read-only/`.
  Original artifact 12143653705; ZIP SHA256
  `05f8aaeed1e8e4f48ed68908d7af68d6546ac980fa685a1edd336beaa9d90e09`.
- Post-release public detail reload verified NCT Brentford's stored age/location/source
  evidence. SQL readback at 17:15 UTC: 495 current Activities; Sutton remains inactive.
  Public-view membership and browser visibility are distinguished from source truth.
  See `artefacts/data/sprint8-production-readback.json`.

## Findings retained outside this delivery
The diagnostic has **20 candidate rows / three categories / two recorded providers**;
380 rows have unresolved location and 281 unresolved age (overlapping sets).
These are not 20 certified distinct actionable opportunities: the identity replay
and seven-record cohort expose real-world-distinctness and link-quality questions.
#136 retains final pilot quality/breadth acceptance, and #135 historical corrections.

#198 is a separate provisional five-point identity repair proposal, not added to
Sprint 8 velocity or automatically committed to Sprint 9. #134 retains Ealing/Merton
HTTP 403 qualification evidence. MyLibrary-only changes now verify that bounded
family; portal/shared-quality code changes and manual full validation still check
all three source routes. The earlier failed broad checks remain historical failures.

#125/#132/#129 remain open in planned Sprint 9 #197. Live read-only checks are not
scheduled collections; no seven-day window, Friday acceptance or future dispatch is
claimed. #195 remains separately unestimated setup backlog.

## Review and improvements
What went well: the agreed observation split allowed four finite outcomes to finish;
source IDs and existing identity/refresh rules were reused; evidence and unknowns
were retained without production experiments or expanding into historical repair.

Improve: qualify source availability and CI family boundaries before committing.
The initial MyLibrary candidate was inactive, and unrelated portal 403s initially
failed a broad live check. Inspect candidate links and real-world duplication before
presenting numerical breadth as useful supply. Isolate the branch before testing;
the original workspace contained unrelated prior-sprint changes.

Continue: one bounded outcome at a time, exact review cohorts, source-backed replay,
honest external dependencies, reversible releases and one shared observation ledger.
The expansion from eight to 18 points was explicitly agreed; this short iteration
does not establish weekly velocity.

## Boundaries and rollback
No source, provider, credential, permission or production schema was activated or
changed. No automatic withdrawal, historical correction or paid model diagnostic
was performed. Existing 60-day public freshness filtering remains. Source-truth
and sustained-operation acceptance remain with their existing tickets.
Reverting #199 removes the new reporting/diagnostics; no data/schema rollback is
needed. Existing evidence remains historical.

Automatic approval review rejected sending snapshot postcodes to an external
geocoder. No such transmission occurred. The report uses already-held visible
public-venue coordinates and conservative exact-postcode evidence; remaining
locations are unknown. No geocoder permission remains necessary for this scope.

