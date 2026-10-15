# Human review desk

## Fixed news acceptance sample

#126 uses the immutable 50-record snapshot in `artefacts/data/news-quality-sample-2026-10-15.json`, frozen from 163 public feed records on 15 October 2026. The manifest records category/geographic-scope strata and selection method: proportional allocation with coverage of each available stratum, deterministic source round-robin/MD5 ordering, and carry-over of two already reviewed records. This is a bounded quality review, not a statistically representative national survey. Feed refreshes cannot change its rows, order, IDs or denominator.

Stored scope/nation/region/admin area/locality accompany each record. Missing metadata stays unknown; locality relevance is judged for that locality. The screen does not assert actual audience delivery from stored metadata alone. Article checks independently record usefulness, attribution, working destination and geographic targeting; unknown is not a pass. Targets are 45/50 jointly relevant/correctly attributed and 48/50 working destinations. Geographic correctness is reported separately, with no invented numeric threshold.

Progress counts distinct frozen-record decisions from repository-owner audit comments with matching SHA-256 snapshots. Duplicate comments count once and the latest matching decision wins. Previous two record decisions accept only their exact legacy fingerprints and carry no inferred rubric scores. Overall task approvals, other commenters and mismatched records do not advance progress. Reviewed items collapse with an update option, and Continue points to the next unreviewed record. All 50 decisions do not automatically close the issue or satisfy individual quality gates.

Validation: 34 targeted tests plus TypeScript; includes immutable sample paging, carry-over and deduplication, exact fingerprint/author matching, missing geography, explicit rubric scores and unknown results. GitHub/Vercel and signed-in browser checks follow deployment.

## Data and forms repair

Review detail pages lead with actual record cards and a decision form per card. #149 renders the eleven-process inventory plus existing live database/source-health evidence. #123 renders the quality/coverage rubric; #135 the retained dated remaining-source proposals; #145 four saved source texts and AI-labelled candidate manifests. #34/#126/#128/#136 query explicit bounded projections of published venues/news/Originals/current activities. #130 reuses the public deals selector. Current browsing datasets are not frozen #122 samples or verified pilot-only cohorts; saved proposals are not current source checks. Rejected Originals drafts and provider result/cost comparisons are explicitly identified as missing evidence.

Forms always render for allowed operators. A top-of-page setup panel distinguishes a missing GitHub token, missing reviewer allowlist, a nonmatching reviewer identity, and unavailable task/history. Saving stays disabled when any prerequisite fails. No permission fallback is introduced. Each record save re-fetches its page and verifies the displayed SHA-256 snapshot before appending a decision with the full server-verified row, dataset scope and evidence. It records decisions, not live publication or database edits. GitHub failure does not hide independently available review data.

Validation: 27 targeted tests, including missing configuration, protected data reads, incomplete/paged datasets, saved source content, changed record rejection and snapshot audit comments. TypeScript checked with the existing local dependency set. Browser and deployment evidence is recorded in the PR.

The homepage Operations login button sends users through existing Supabase login to `/ops`. The protected `/ops/reviews` inventory links nine owner-review tasks to live acceptance criteria, GitHub discussion and related evidence. Each card and detail page links back to operations.

## Deployment configuration

Existing `DADSPACE_OPERATOR_USER_IDS` / `DADSPACE_OPERATOR_EMAILS` authorize read access. Saving additionally requires `DADSPACE_REVIEWER_USER_IDS` or `DADSPACE_REVIEWER_EMAILS` (exact verified Supabase identities) and server-only `DADSPACE_REVIEW_GITHUB_TOKEN`, a fine-grained GitHub credential restricted to this repository with Issues read/write. Never use a NEXT_PUBLIC variable for this token. Configure via the hosting provider's secret settings; do not commit it.

Decisions are append-only GitHub issue comments, including verified reviewer UUID, scope, evidence and observed issue version. Approval does not close the issue, apply source/data changes, activate providers or release anything. GitHub comments are public and the form says so. History displays GitHub authors without asserting all marker-matching comments are trusted owner decisions.

The server rechecks operator/reviewer identity on every write, accepts only the nine known tasks and three decision values, bounds input lengths and rejects changed/closed issues. Next server actions supply same-origin POST protection. Writes use the fixed repository endpoint only. A failed or timed-out save may have reached GitHub: inspect history before retrying. Concurrent reviews append independent records rather than overwriting each other; the preflight version check is not an atomic GitHub compare-and-swap. Conflicting simultaneous decisions need explicit follow-up.

## Review inventory — 15 October 2026

Human gates: #123 thresholds; #34 venue sample; #126 news; #128 Originals; #130 deals; #135 historical proposals; #136 activity quality. #145 provider rollout and #149 operations coverage include owner acceptance but still need engineering evidence. These are not all immediately approval-ready. Samples/prerequisites and current task criteria remain authoritative. Deferred community, external access, scheduled observation and general implementation backlog are not represented as ready human reviews.

## Release checks

Verify signed-out redirects and denied accounts; an operator without reviewer configuration must remain read-only. Verify an explicitly configured reviewer can save and read back a scoped decision; changed evidence rejects the form. Verify keyboard/mobile forms, pending/error/success states and homepage login return. Exercise writes on a designated test task/environment, not by posting dummy approval to a live acceptance task.
