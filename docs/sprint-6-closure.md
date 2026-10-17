# Sprint 6 review and closure — 17 October 2026

Post-closure update, same date: the owner approved single-owner maintenance access and accepted workspace usability. Production maintenance was configured and verified for that existing account only; paid manual retries remain disabled. No live action was applied. The release-state account below is historical; remaining execution/recovery and scheduled acceptance still apply. See [decision and readback](./sprint-6-review.md).

Tracker: [#185](https://github.com/imransinvestments-prog/Dadspace/issues/185). Owner approved releasing the reviewed code and requested a sprint review followed by closure. The sprint iteration closes with explicit carryover; its full acceptance goal is not claimed complete.

## Released outcome

[PR #186](https://github.com/imransinvestments-prog/Dadspace/pull/186) merged as `31b8c1fe7a99af4a5b47cd96ed022acec6ebeae0`. The release includes owner-only editorial queues, read-only previews, private future draft/failure evidence, audited maintenance implementation and the 07:17 London publication / 09:17 duplicate-safe retry schedule. Pushing code no longer generates a paid article automatically.

Live maintenance and paid manual retries remain disabled, as approved. No source activation, article hide/unpublish or paid diagnostic was performed. Existing News corrections and accepted article reviews remain settled. Vercel production and applicable main-branch checks passed; the push-triggered publishing job correctly skipped. Authenticated [production editorial readback](https://www.dad-space.co.uk/ops/editorial) shows all nine Originals and explicitly disabled live controls with missing signing/runner configuration. This is release verification, not scheduled acceptance.

## Commitment and carryover

**22 committed points; 0 acceptance points awarded; 22 original committed points carried forward.** This is acceptance accounting, not an estimate of 22 points of additional coding. Re-estimate the residual work before another sprint commitment. Code delivery, passing tests and owner release approval do not satisfy disabled live-action or future scheduled-operation criteria.

| Open ticket | Original allocation | Required before feature acceptance |
| --- | ---: | --- |
| #146 maintenance | 11 | Reconcile wider source/schedule coverage against its complete criteria; approve and configure maintenance permission/bounded retry policy; verify actual authorised normal-runner execution, audit and recovery. |
| #147 editorial upkeep | 8 | Complete owner operational usability acceptance and verified maintenance paths after their explicit activation. Historical drafts cannot be reconstructed; retained future evidence must remain honest. |
| #129 Originals reliability | 3 | Link actual daily and Friday scheduled publications, duplicate-safe 09:17 retries, failure/recovery status and public readback after the released configuration is stable. Offline rejection/revision and denial tests are already delivered. |

All three tickets remain open. #125's complete cross-feed seven-day criteria remain unchanged, including Activities. No full News epic closure is asserted. Unaccepted carryover is not silently added to the proposed 24-point Deals sprint; it must be refined and explicitly scheduled or retained as a separate observation/configuration lane.

## What went well

- Reused the existing review desk and preserved completed owner content judgments; no repeat 50-article or six-Originals review.
- Owner-only reads and separate disabled maintenance powers allowed a useful production release without activating unreviewed writes or spend.
- PostgreSQL, permission, stale-preview, duplicate-request, bounded collection and denial tests accompanied the implementation. Hosted checks and the reviewed preview deployment passed before merge.
- Signed-in browser verification covered nine Originals, the News queue's actual public/stored distinction, 19 identifiable feeds, empty draft/history states, keyboard focus and narrow-screen layout. User feedback exposed a confusing validation failure; it now preserves entries and explains invalid form input.

## What could improve

- We committed end-to-end acceptance while planning to release with live controls disabled and while scheduled evidence required real elapsed time. That made the 22-point commitment unsuitable for immediate acceptance. Separate independently acceptable read-only delivery, permission activation, live recovery verification and observation before commitment.
- Browser sign-in happened first in Edge, outside the browser available to the agent; a trailing full stop in the copied URL produced a 404. Provide a clean clickable link and identify the test browser upfront.
- Earlier testing missed form-input preservation, narrow native-select overflow and queue-specific empty messages. Include those failure paths before asking for owner review.
- A broad Python test-discovery workflow lacked News-specific dependencies. Keep those regressions mandatory in the dedicated News workflow rather than coupling unrelated collectors.

## Continue

Keep bounded scope, one consolidated decision pack, explicit unknowns, existing review reuse, exact data readback, separate permission/spend gates, reversible actions and a review after every sprint. Record accepted points only when a whole story's outcome is evidenced. Do not convert a released increment or elapsed calendar time into artificial acceptance.

Owner feedback recorded in this chat was positive and included explicit release approval. No additional detailed retrospective feedback is attributed to the owner.

## Next

Keep the proposed Deals sprint (#131/#148/#132, 24 provisional points) next in sequence; Activities remains deferred. Before committing it, refine the inherited reliability dependency and the unaccepted News maintenance work. Preserve the 25-point ceiling and avoid counting the same remaining work twice.
