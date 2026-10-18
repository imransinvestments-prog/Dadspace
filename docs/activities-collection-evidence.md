# Activities collection evidence — #180

The normal Activities workflow writes `collection-evidence.jsonl` and uploads it
as `activities-evidence-{run_id}-{run_attempt}` even when collection fails.
Each invocation creates a new file exclusively; a reused file is rejected before
source processing. Artifact upload treats missing evidence as an error.

The start record freezes selected source IDs and GitHub run/attempt/SHA/event.
Source records append immediately after processing and health-write handling.
The finish record explicitly enumerates all selected but unprocessed sources.
A killed job may have no finish record: retain its start and source records;
missing finish is incomplete execution evidence, never successful acceptance.
No run history is stored in a new database table. Normal artifact retention
applies; preserve the relevant artifacts in the acceptance pack before expiry.

## Outcome contract

- `extracted`: available extraction count; unknown stays null.
- `validated`: locally qualified rows, including a source whose save failed.
- `rejected`: extracted minus validated and merged duplicates, when known.
- `saved_count`: submitted candidate count only after the existing save protocol
  returns success. This is not the number of new rows, distinct database identities
  or publicly visible Activities. Failed sequential retries may have partially
  committed; their count stays null and write state is `unknown_partial`.
- `health_state`: separately confirmed source status write, failed, unconfirmed,
  not attempted or dry run. An empty database response is not confirmed success.
- `unchanged`: root/cache outcome, not proof all programme details were checked.
- `deferred`: source not completed because of budget or an unprocessed tail.
- `suspicious_zero`: a successful extraction with no kept output, requiring review.
- `coverage`: unknown unless source evidence establishes more; a green source or
  root hash cannot establish complete programme coverage. Deferred sources are
  explicitly not checked. No new renewal/withdrawal policy is introduced here.

The public-view readback uses at most 20 distinct candidate keys per successful
live Activities source and reads `current_activities`. It records sample size,
whether all candidate keys fit, matched row IDs/last-seen/links and unmatched keys.
It uses the collector's existing database client, so it proves view membership,
not anonymous access or a browser journey. Trigger-rewritten keys can be unmatched;
absence is not proof of expiry, cancellation or failed persistence. Query failure
is unavailable with null rows, distinct from a successful empty result. Dry runs
do not perform this readback. No extra model calls or database writes are added.

## Verification and remaining acceptance

Eight focused evidence/run-loop checks cover partial save, budget stop, deferred
tail, unchanged, zero yield, status-write uncertainty, append preservation,
bounded public-view readback and unavailable versus genuine empty results.
The real run-loop fixture confirms failed saves do not advance source hash or
last-success and that budget-deferred sources receive no status write.

Local full Python discovery: 253 tests run, 13 skipped, exit 0 (240 passed).
Existing Activities ingestion: 15 passed; Gemini controls: 11 passed. The full
suite includes unrelated local workspace changes, so this does not certify a
clean release branch. No paid/provider calls or live content mutations were run.

Remaining: clean branch/hosted checks, concrete release review, representative
production artifact/source/public readback and acceptance of coverage semantics.
MyLibrary now supplies bounded item coverage including fetched/included/withheld
links and completion/failure state; other adapters retain unknown coverage.
Ticket #180 remains open with zero accepted points. Sustained scheduled evidence
belongs to #125 in planned Sprint 9 #197; it is not manufactured by local fixtures.
