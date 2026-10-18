# #129 closure readiness — 18 October 2026

Scope: verify sustained Originals publication and bounded recovery. This is evidence, not acceptance or a new paid publishing run.

## Completed verification

- Existing owner content approvals are retained. Production has nine Originals, zero duplicate cadence/date slots and zero retained attempt rows at 10:21 BST.
- All **13 Originals tests** and **4 maintenance-runner tests** pass. They exercise one revision/two-draft stop, independent review, rejection/no-write, denial/no-retry, dry-run/no-write, duplicate/no-model, evidence-store failure and historical-slot rejection.
- Added a meaningful uncertain-insert recovery regression: the article commits, its response is lost, failure status is retained, and the next run finds that slot. Exactly one article exists and the recovery makes zero model calls. This is a fixture, not production publication.
- [17 October morning scheduled run](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39025653264) published daily-2026-10-17. [Evening run](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39067197795) explicitly skipped the same slot.
- [16 October Friday scheduled run](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38892860271), publish job 116946524036, logged both daily-2026-10-16 and weekly-2026-10-16 as published.
- Public browser readback confirmed [the daily article](https://www.dad-space.co.uk/originals/daily-2026-10-17) and [Friday guide](https://www.dad-space.co.uk/originals/weekly-2026-10-16). This verifies availability; existing content judgments are not reopened.

## Dispatch investigation

The workflow is enabled: its GitHub options offer “Disable workflow”, and the page lists actual scheduled history. Current default-branch YAML uses cron `17 7,9 * * *` with `timezone: Europe/London`. This is valid according to [GitHub's current schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). There is no demonstrated syntax or disabled-workflow defect to repair.

The stable Sprint 6 release was committed at **17 October 20:33:40 UTC** as 31b8c1fe7a99af4a5b47cd96ed022acec6ebeae0. The latest scheduled run was created at 20:33:09 UTC on the earlier SHA, so even that successful duplicate skip cannot be relabelled as a test of the newly released configuration.

At the **18 October 10:21 BST** snapshot:

| Intended London slot | UTC slot | Observed scheduled run |
| --- | --- | --- |
| 18 October 07:17 BST | 06:17 UTC | None observed; over 60 minutes overdue |
| 18 October 09:17 BST | 08:17 UTC | None observed; over 60 minutes overdue |

GitHub documents that scheduled events may be delayed or dropped under load. That is a possible explanation, not a confirmed diagnosis of these missing runs. The evidence does not identify GitHub's internal dispatch cause. Changing an already-correct cron or moving the expected time would not prove reliability.

The workflow-specific API URL is not exposed by this session's GitHub Fetch tool; repository schedule-run API results were cross-checked against the signed-in workflow UI instead. No account credential or workflow setting changed.

## Exact closure gates still open

1. Observe real scheduled daily publication and the duplicate-safe **09:17 retry** on the stable configuration. Reconcile intended slot, workflow SHA/run/job, retained stages, unique database article and public readback. A missed dispatch is distinct from a failed worker.
2. Observe the real Friday daily+weekly opportunity on that configuration. The next Friday is **23 October 2026**; this is the earliest next Friday opportunity, not a promised closure date.
3. Reconcile actual retained runtime status/recovery with the same observation ledger used by #125. There are currently no attempt rows, so future evidence must not be backfilled or fabricated. Existing offline failure/recovery proof is complete; do not deliberately break production or pay to manufacture a failure.
4. Declare a passing window only from complete evidence. Today's missing slots remain failures of the dispatch allowance; no qualifying shared seven-day window is claimed. #125's wider cross-feed/Activities criteria are separate and are not closed by this report.

## Human involvement and scope

No repeat approval of unchanged articles is required. Existing routine scheduled publication remains configured. A separate concrete decision would be needed for a new paid manual diagnostic/retry, credentials/spend changes or publishing-policy changes. No such action was performed. The original **3 points remain unaccepted**; this is not a fresh estimate of three points of coding.

Machine-readable snapshot: [originals-129-readiness-2026-10-18.json](../artefacts/data/originals-129-readiness-2026-10-18.json).
