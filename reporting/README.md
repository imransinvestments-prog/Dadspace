# Dadspace daily reporting

## Schedules
- Weekday Morning Brief: Monday–Friday, 07:30 Europe/London.
- Dadspace Daily Brief Email: every day, 09:00 Europe/London; authorized recipient configured in the task, not this public report.
- The 9 AM task generates a same-day snapshot if the 7:30 task did not (including weekends).

## Review
Download/open operations.html and sources-coverage.html in a browser; GitHub's file page shows HTML source rather than a hosted dashboard. brief.md is readable directly in GitHub. The HTML snapshots are self-contained, printable, and use no external scripts. JSON includes source evidence and item states.

## Daily generation contract
Read all repository issues and PRs with pagination, and available project-board items when supported. Count completed issues separately from merged PRs; closed/unmerged is not completed. Group open items by feature. Preserve direct citations and the observed timestamp. Read latest scheduled collector jobs, not just CI status; bounded usage logs/artifacts provide per-worker totals and source outcomes. Include failures, zero yield, cache hits and missing usage. Thinking is included in output; avoid double-counting. Do not invent billing rates or project-wide totals from partial usage.

Read updated source matrix/reconciliation and approved production metrics when available. Display access timestamp, source decision, operational activation and acceptance separately. Apply docs/discovery-model.md: venues, regular Activities and infrequent Events need separate coverage. Explicitly flag missing county boundary/coordinate joins, unknown mapping, unverified public visibility/quality and stale evidence. County-named route yield is not county coverage. Do not report a UK coverage percentage without a documented denominator and validated numerator.

Save immutable daily snapshot files at reporting/snapshots/YYYY-MM-DD/{operations.html,sources-coverage.html,brief.md,data.json}. Update top-level dashboard/brief/data files and latest.json after successful generation; do not advance the successful watermark on failures. If rerunning the same day, preserve previous evidence by using a timestamped subdirectory rather than overwriting an existing snapshot. Email the current day's report at 9 AM; check Sent and delivery state for duplicates, then record confirmed success. Do not send stale snapshots without an explicit stale-data notice.

## Minimal-intervention plan
Routine read-only evidence gathering and reporting commits are authorized. Batch human labels/policy decisions/operator provisioning into one review. Preserve existing paid limits and source/provider/release gates. Do not activate sources, change providers, merge unrelated changes, close tickets or launch production merely because a report is generated.

## First snapshot limitations
14 October: 79 repository issues/PRs reconciled. Board-only draft cards/status fields unavailable. Source matrix dated 10–11 October. Latest morning run logs supply real civic/activity usage, while news/Originals/shadow usage and monetary totals remain unavailable. Full UK county accepted-supply measurement requires additional geographic and public-quality evidence.
