# Historical listing cleanup applied — 12 October 2026

Owner explicitly authorised reviewing/applying date backfills, correcting classifications/duplicates and withdrawing stale listings in chat. This is a live database reconciliation, independent of the still-draft worker PR. No source registry activation or application deployment occurred.

## Applied and verified

Reviewed all 679 stored records structurally and fetched 177 relevant primary detail URLs (168 readable, nine unresolved), followed by 13 checks of expired dated activity details. A readable page alone is not qualified/current supply.

The guarded batch changed 147 distinct records:
- 111 published date/schedule backfills from matched primary HAY, Hoop, council/library details.
- 16 confirmed sales/special-photo-occasion classifications corrected from Activity to Event. Regular NCT groups remain Activities; dates alone did not determine type.
- 14 expired dated occurrences withdrawn, including one discovered during fresh backfill. This does not declare the continuing programme closed.
- Eight duplicate rows withdrawn with `superseded_by` links to their retained programme record. Shared generic provider URLs for different venues were not merged.

Counts overlap where an expired occasion also needed date/classification correction. All 679 rows remain stored; 532 rows are untouched. No deletions, source-registry changes, venue changes or collection/verification timestamp renewals. Feed counts move from 453 current Activities / 148 upcoming Events to 416 / 163. All 22 withdrawn rows are absent from both feed views. Existing expired Events were already outside upcoming discovery and remain archived.

[Applied plan](../data/ds10-historical-cleanup-plan-2026-10-12.json), [source checks](../data/ds10-historical-source-checks-2026-10-12.json), [verification](../data/ds10-historical-cleanup-verification-2026-10-12.json). The plan retains 191 distinct records requiring schedule, classification, identity or missing-detail review. These were not guessed or bulk deleted; they depend on remaining source repair/owner review. This does not certify all historic data or close #39.

## Safe execution and undo

Full 679-record pre-change snapshots are retained locally under `event-backup/historical-2026-10-12-before`, plus post-schema/final snapshots. Before committing, the exact 147-record update ran and rolled back with row-fingerprint, identity, protected-provenance and feed-visibility checks. SQL uses a bounded write lock, timeout, field whitelist and rejects concurrent changes. Actual changed IDs match the plan; protected timestamps/venue/source IDs are unchanged.

The final `event-backup/historical-rollback-plan-v2.json` restores original fields and clears review/withdrawal metadata. It was executed in a transaction and rolled back successfully; live corrections remain applied. Generate with `historical_cleanup.build_sql(plan, commit=False)` for a rollback-only check; `commit=True` is the explicit write path. Fresh row checks are mandatory if data has changed since the final snapshot. Earlier backup/undo versions are historical, not the current restore plan.

## Durable withdrawal and reviewed dates

Live migrations `20261012121658_ds10_reversible_listing_withdrawal` and `20261012123414_ds10_protect_reviewed_date_backfills` are exported directly from recorded Supabase migration history. The CLI could not initialise its settings folder despite granted permission; the official migration API applied the schema atomically. Exact migration SQL is committed for review.

Withdrawal metadata preserves evidence and excludes rows from current/upcoming feed views. Identity reuse ignores withdrawn aliases, preventing retired duplicates from hijacking retained rows. Views retain `security_invoker=true`; existing RLS and grants are unchanged.

109 records with explicit date backfills are guarded against the older deployed cleaner dropping dates. An incoming null-date write retains reviewed dates/schedule/time and does not advance verification timestamps. Source-level unchanged refresh also cannot verify those individual dated sessions. Explicit dated collector updates remain permitted. If a programme legitimately becomes undated, clear its review flag only after direct source review. The two undated HAY schedule backfills are not represented as exact-date guard coverage.

Real database probes verified legacy null-date protection, explicit-date updates and nested source-level refresh, all rolled back. Source/collection timestamps are unchanged after the probes. Worker/source qualification and normal repeat ingestion remain separate acceptance work.

125 local Python tests pass. Security advisor findings are unchanged from the pre-change baseline; no new RLS/grant/view findings were introduced. App caches can take up to their configured revalidation interval to show corrected schedules. #39 remains open for unresolved source records, pilot breadth, scored owner quality review and scheduled seven-day evidence.
