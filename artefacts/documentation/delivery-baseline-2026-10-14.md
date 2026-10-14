# Delivery baseline — 14 October 2026

Owner accepted the delivery sequence in chat: baseline/reliability, operations UI,
W3 discovery, deals/public journeys, pilot acceptance, then community.
Pilot is W3 9LN, 10 km, ages 0–5 inclusive. Keep useful wider supply separately.

## Current evidence

Main: `bfd3b3c61a066dccd1ee2b8a3cebb7d1b068a3c7`.
21 open issues: #29–#37, #39–#44, #48, #53, #63, #65, #66, #70.
#38 is closed; #61/#62 are delivered. #71 is merged and its follow-up deployed,
despite older issue-body paragraphs describing a draft. #69 remains draft.

- [Morning scheduled workers](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38525167188):
  news, venue reference, civic and activities jobs succeeded. Deals failed with
  15 regression import errors before self-test or collection. The job installed
  only requests but ran the entire suite, including Beautiful Soup imports.
  Its health report shows 0 eligible published offers, 0 groups/providers and
  missed source refreshes. The historical 18-offer MVP pool is not current supply.
- [Originals](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38524416785):
  successful generation, editorial review and `Published daily 2026-10-14` in the
  publish job. Historical billing and 123-word failures are not current blockers.
  First generated content still needs owner editorial acceptance/public verification.
- [Shadow comparison](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38527193152):
  both variants rejected incomplete output. Four attempts/60,000 tokens and 3,000
  output tokens per variant remain the limits; do not increase them automatically.
  Successful connectivity/empty outputs are not quality equivalence.
- Civic depends on news success; activities depends on civic success. This leaves
  unrelated feed outages able to suppress refreshes. Deals/reference are independent.
- Deals expansion exists on MVP with shared database sources; branch parity and a
  scheduler/release package remain required. Do not merge the entire older branch.
- Ealing/Merton GitHub runner access remains unqualified (HTTP 403). #39 still needs
  human scoring, canonical matches, historical follow-ups and local coverage evidence.
- Latest #65 audit: 62 listing sources checked; 0 qualified for immediate complete
  structured-parser activation. Deterministic source work must precede savings claims.

This is a repository/run baseline, not a complete fresh database quality sample.
Job success does not prove all sources succeeded or records were useful.

## First repair package

Install worker requirements plus jsonschema before the complete deals regressions;
retain all tests. Make scheduled and manual civic/activities independent. Preserve
failed shadow sample identity/settings/usage and a safe exception type in the
artifact; stop without retry/fallback and keep incomplete output rejected.
Production provider, source flags, paid caps and release gates are unchanged.

## Remaining delivery register

| Stage | Tickets | Next evidence / dependency |
| --- | --- | --- |
| Baseline/scope | #29 #30 #31 | Refresh production sample scorecard; reconcile accepted scope and superseded issue text. |
| Reliability | #32 #63 #65 | Release these repairs; verify scheduled recovery, freshness, bounded usage and seven days without silent missed targets. |
| Operations | #70 #33 #40 | Authenticated read-only dashboard/process map, then previewed/audited decision queues and relationship-preserving actions. |
| Pilot discovery | #34 #39 #40 | Permitted local source routes, provenance, canonical matching, stable repeat ingestion and scored quality samples. |
| Deals/public journeys | #35 #36 #37 #48 #53 | Reconcile MVP changes; useful fresh supply, priority group gaps, shared selection, truthful failure states and remaining SEO checks. |
| Acceptance | #44 | Per-feature scorecards, recovery/rollback, observation and owner-reviewed release. |
| Community | #41 #42 #43 | Agreed rooms/access and named moderator; authenticated, resilient messaging and moderation tests. |
| Alternative providers | #66 / PR #69 | Wider validation impact review, representative same-snapshot comparison, owner decision before activation. Defer DeepSeek initially. |

Human decisions should be batched: quality labels/policy exceptions; concrete
source/provider/release changes; final pilot acceptance. Routine engineering and
evidence gathering can proceed independently. Seven-day observation cannot be
replaced by repeated manual runs. No automatic source activation or issue closure.
