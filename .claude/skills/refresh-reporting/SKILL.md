---
name: refresh-reporting
description: Regenerate the Dadspace daily operations/sources reporting snapshot under reporting/ following the daily generation contract.
disable-model-invocation: true
argument-hint: "[YYYY-MM-DD, defaults to today Europe/London]"
---

# Refresh daily reporting

Target date: $ARGUMENTS (if blank, use today in Europe/London).

`reporting/README.md` is the authoritative contract. Read it in full first, plus `docs/discovery-model.md`. The rules below summarise it but don't replace it.

## Gather evidence (read-only)
1. All repository issues and PRs, paginated (`gh issue list --state all --limit 1000`, `gh pr list --state all --limit 1000`), plus project-board items if available. Count completed issues separately from merged PRs. Closed but unmerged is not completed.
2. The latest **scheduled** collector runs (`gh run list --event schedule`), not just CI status. Use bounded usage logs and artifacts for per-worker totals and source outcomes. Include failures, zero yield, cache hits and missing usage. Don't invent billing rates or project-wide totals from partial usage.
3. The current source matrix and reconciliation, and approved production metrics when available.
4. The previous snapshot in `reporting/snapshots/`, to compare against.

## Write
- Keep venues, regular Activities and infrequent Events as separate coverage lines.
- Flag missing county boundary or coordinate joins, unknown mapping, unverified public visibility or quality, and stale evidence. County-named route yield is not county coverage. Don't give a UK coverage % without a documented denominator and a validated numerator.
- Show access timestamp, source decision, operational activation and acceptance separately. Keep direct citations and the observed timestamp.
- Save `reporting/snapshots/<date>/{operations.html,sources-coverage.html,brief.md,data.json}`. If that directory already exists, write to a timestamped subdirectory instead of overwriting. The HTML must be self-contained with no external scripts.
- Only after generation succeeds, update the top-level `reporting/operations.html`, `sources-coverage.html`, `brief.md`, `data.json` and `latest.json`. On failure, leave the watermark where it is and report what failed.

## Finish
- Commit only the reporting files, with a message like `Refresh <D Month> reporting` and a short clause naming any notable failure (e.g. "and flag expired-terms Deals failure").
- Don't send the email from this skill. Record delivery in a later commit only after Sent or delivery state confirms it.
- Don't activate sources, change providers, close tickets or merge unrelated changes.
