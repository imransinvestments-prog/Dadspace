# Sprint 6 — News and Originals reliability

Approved 17 October 2026. Tracker: [#185](https://github.com/imransinvestments-prog/Dadspace/issues/185).

Goal: reliable publication, usable editorial upkeep and bounded recovery. Commitment is **22 points**: #146 (11), #147 (8), #129 (3). Acceptance, not code completion, burns points. No end date or ideal burndown has been invented.

## Sequence and ownership

1. Inventory released worker/queue/auth/audit behaviour. Preserve accepted News and Originals reviews and geographic corrections.
2. #146/S1: actor-bound previews with separate maintenance permission; explicit dry/live scope, cost unknowns, missing configuration and source-policy gates.
3. #146/S2/S3: bounded, idempotent execution and audit/recovery; treat uncertain remote submission as unknown, never blindly retry it. Do not cancel independent healthy collectors.
4. #147/S1: protected published/draft/rejection/failure queues, provenance and honest usage. No invented historical drafts.
5. #147/S2: editorial retry/unpublish through the shared controls, preserving independent review and slot identity. Verify failures and owner usability.
6. #129: offline rejection/revision/idempotency checks plus actual daily/Friday and 09:17 retry evidence. One revision, at most two drafts; auth/billing denials stop immediately.
7. One consolidated owner preview/decision pack, approved release, production readback and sprint review.

## Findings at commencement

- `original-content.yml` currently schedules 07:17 and 19:17 London; #129 requires a 09:17 retry. Correct this deliberately and do not claim the old schedule met acceptance.
- `original_content_worker.py` retains only published rows; no draft/maintenance table exists in the inspected public schema. Capture future evidence; historical absence is unknown.
- Published rows include daily 17 October and weekly 16 October, but timestamps alone do not prove the originating scheduled run or timeliness.
- Existing owner-only Operations and separately configured reviewer access must not confer maintenance power.

## Boundaries and decisions

Maintenance starts disabled. Prepare exact role/configuration, retry/spend and publication effects for the owner in one pack. No paid test calls, activation, provider change or live editorial action is implied by assignment. Preview deployments must never dispatch to production.

#125 remains open: its complete seven-day, cross-feed acceptance includes Activities. Capture reusable News observations independently. Deals is next; Activities implementation, #149 wider handover, #101 and Morning Brief remain outside this sprint.

Existing 50 News reviews, 19 corrections and six Originals approvals remain settled. Request only genuinely new editorial judgments, with an exact manifest and count at preview.
