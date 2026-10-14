# Operations dashboard: first increment

Related: #70, #32, #33, #40. Route: `/ops`.

Read-only, dynamically rendered and noindex. Server-side `auth.getUser()` verifies
the session on every request before loading evidence. Signed-out visitors go to
the existing login flow with a safe `/ops` return path. Signed-in nonoperators
receive a 404. Proxy protection is convenience, not the authorization boundary.

## Setup

Use the existing Supabase public URL/key and cookie-based sign-in. Configure
server-only `DADSPACE_OPERATOR_USER_IDS` with comma-separated, explicitly approved
Supabase Auth user UUIDs. An empty/invalid list denies everyone. Do not use names,
email substring matching or user-editable `user_metadata`. This first increment
grants read-only visibility; it conveys no reviewer/maintenance mutation powers.
Role provisioning and owner usability acceptance remain rollout dependencies.

Alternatively set server-only `DADSPACE_OPERATOR_EMAILS` to approved exact email
addresses. Only an email returned by the verified Auth server user with
`email_confirmed_at` qualifies; unconfirmed/anonymous users are rejected.
The owner selected `imransinvestments@gmail.com` in chat on 14 October. This email
has no account in the current Auth lookup; a confirmed sign-in is still required.
Do not create passwords or send invitations automatically. This route can be
configured before the owner completes the existing sign-up/confirmation flow.

No service-role key, GitHub token, new package, schema or database mutation is
required. Read-only GitHub metadata is available from this public repository.

## Evidence contract

- Last three scheduled main worker runs, individual job outcomes and last success
  observed in that window. Manual runs cannot satisfy scheduled freshness.
- Latest scheduled Originals publication job; a successful duplicate skip is not
  proof that a new post was generated. Verify published content separately.
- Latest main shadow comparison; it neither publishes nor changes production models.
- Next expected start at 07:17/19:17 Europe/London, including BST/GMT. Runner delay
  is explicit. A 16-hour gap flags a possibly missed run (12-hour cadence + 4-hour
  grace), not source-level freshness.
- Fixed repository endpoints, ten-second timeouts, redirects rejected, bounded
  requests (at most seven), shared public-metadata cache refreshing after ten
  minutes. Authentication/identities and private records are never cached.
- HTTP errors/rate limits produce unknown/unavailable states, never empty supply
  or success. Failed job retrieval does not discard other feed evidence. More
  than 100 jobs is incomplete and shown unknown instead of silently truncated.

Source-level verification, accepted/rejected counts, pilot quality, backlog totals,
pricing/usage, deployments, secrets readiness and seven-day acceptance are not yet
connected. UI says so. No production listings, logs, payloads or secrets are read.

## Process coverage and next increments

The dashboard's process inventory maps collection/recovery, source review, venue
validation, enrichment/photos, activities/events, news, Originals, deals, AI usage,
release/backup and community/moderation to owner, cadence, evidence, permission and
explicit next action. Ticket links provide recovery context; they do not complete
the maintenance-action acceptance criteria of #70.

Next: agree owner navigation/process coverage; connect verified source/run summaries
and review queues; add previewed/audited maintenance actions with distinct server
permissions, concurrency protection and rollback. Venue merges must preserve
canonical relationships. Keep regular activities distinct from infrequent events.

## Validation and rollout

`node --test tests/operations.test.cjs`, TypeScript and production build run in
the dedicated workflow. Tests cover fail-closed access, server-side session errors,
metadata privilege attempts, failed/unknown/empty job evidence, independent feed
status, manual-run exclusion, stale runs and DST/year boundaries.

Owner account provisioning, authenticated populated desktop/mobile browser review,
keyboard usability and deployment verification are still required. This document
does not claim them. Removing the route/allowlist disables this read-only feature;
no data/schema rollback is needed. No #70 closure or broader release implied.

Auth reference: https://supabase.com/docs/reference/javascript/auth-getuser
