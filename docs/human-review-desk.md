# Human review desk

The homepage Operations login button sends users through existing Supabase login to `/ops`. The protected `/ops/reviews` inventory links nine owner-review tasks to live acceptance criteria, GitHub discussion and related evidence. Each card and detail page links back to operations.

## Deployment configuration

Existing `DADSPACE_OPERATOR_USER_IDS` / `DADSPACE_OPERATOR_EMAILS` authorize read access. Saving additionally requires `DADSPACE_REVIEWER_USER_IDS` or `DADSPACE_REVIEWER_EMAILS` (exact verified Supabase identities) and server-only `DADSPACE_REVIEW_GITHUB_TOKEN`, a fine-grained GitHub credential restricted to this repository with Issues read/write. Never use a NEXT_PUBLIC variable for this token. Configure via the hosting provider's secret settings; do not commit it.

Decisions are append-only GitHub issue comments, including verified reviewer UUID, scope, evidence and observed issue version. Approval does not close the issue, apply source/data changes, activate providers or release anything. GitHub comments are public and the form says so. History displays GitHub authors without asserting all marker-matching comments are trusted owner decisions.

The server rechecks operator/reviewer identity on every write, accepts only the nine known tasks and three decision values, bounds input lengths and rejects changed/closed issues. Next server actions supply same-origin POST protection. Writes use the fixed repository endpoint only. A failed or timed-out save may have reached GitHub: inspect history before retrying. Concurrent reviews append independent records rather than overwriting each other; the preflight version check is not an atomic GitHub compare-and-swap. Conflicting simultaneous decisions need explicit follow-up.

## Review inventory — 15 October 2026

Human gates: #123 thresholds; #34 venue sample; #126 news; #128 Originals; #130 deals; #135 historical proposals; #136 activity quality. #145 provider rollout and #149 operations coverage include owner acceptance but still need engineering evidence. These are not all immediately approval-ready. Samples/prerequisites and current task criteria remain authoritative. Deferred community, external access, scheduled observation and general implementation backlog are not represented as ready human reviews.

## Release checks

Verify signed-out redirects and denied accounts; an operator without reviewer configuration must remain read-only. Verify an explicitly configured reviewer can save and read back a scoped decision; changed evidence rejects the form. Verify keyboard/mobile forms, pending/error/success states and homepage login return. Exercise writes on a designated test task/environment, not by posting dummy approval to a live acceptance task.
