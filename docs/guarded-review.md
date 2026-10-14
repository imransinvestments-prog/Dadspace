# Guarded operations review

Routes: `/ops/review` → `/ops/decision`. Related #33, #40, #70.

Existing exact operator UUID/confirmed-email access is unchanged. All operators
can inspect current evidence, possible canonical candidates and signed previews.
Applying requires **separate** server-only `DADSPACE_REVIEWER_USER_IDS`, exact
verified Auth UUIDs; empty means no reviewers. Operator access is also required.
Never infer this permission from email fragments, profile metadata or client input.
The selected owner's reviewer role is disabled until explicit approval.

Each preview binds the verified actor, exact action/record/target/reason, current
database fingerprint, unique request and 15-minute expiry. HMAC uses the existing
server service key with a distinct purpose prefix; no key is sent to the client.
Next server actions enforce same-origin requests and recheck identity/role on every
apply. Changed form fields cannot alter the signed intent. Separate evidence and
apply confirmations are required. No GET request performs a decision.

Service-only SECURITY INVOKER functions provide approval/hiding, duplicate merge,
unresolved listing link and rollback. RLS and explicit revokes prevent ordinary
anon/authenticated access to both RPCs and private audit records. The audit stores
actor, time, reason and bounded before/after state; client previews show only selected
names/postcodes/current visibility/counts. Raw record hashes, notes and payloads
do not render. Reasons are private operator evidence, HTML-escaped.

Transactions serialize review changes against imports with three-second lock waits,
stale fingerprints, a unique request key and a 200-relationship merge bound. Identity
collisions fail atomically; no automatic event deletion/deduplication. Merge keeps
the source venue hidden with `merged_into`, moves event/activity links and provenance,
and preserves dates/recurrence/classification. Future inserts follow the canonical
chain; reviewed venue fields and listing matches resist subsequent upsert overwrites.
Missing evidence cannot approve a venue. Public target visibility is required, but
reviewers must independently verify branch identity; name/postcode equality is not proof.

Rollback previews compare the full affected snapshot. Subsequent import/source or
decision changes block rollback rather than overwrite newer evidence. Restores only
review fields and original relationships, retains original audit and adds a reversal
audit record. Generic rollback does not delete venues/listings/provenance. Removing
the reviewer allowlist immediately disables new applies. Reverting application code
leaves the private audit/canonical protection in place; do not drop it while merged
records exist. Never roll back schema by discarding decision history.

Isolated PostgreSQL regressions and production transaction/ROLLBACK verification
cover stale previews, one-time application, approve/hide, reviewed-field protection,
listing evidence preservation, merge/provenance, repeat imports and guarded rollback.
Production verification leaves zero test records and zero decisions. Security checks
confirm the API is invoker-only and anon/authenticated have no execute grants. The
audit's RLS-with-no-policy INFO notice is intentional: only the existing service role
reads/writes it. No policy grants ordinary users access.

The official CLI generated the migration name in Linux because the local Windows
CLI requires an unwritable home config directory. Repository migration timestamp
is aligned to the managed Supabase migration history, `20261014203725`, after apply.
No home-directory permission expansion was requested.

Separate maintenance/run controls, source activation, editorial corrections, field
editing/photo rights and wider pilot/seven-day acceptance remain their own gates.
This increment grants no such powers. See the process inventory in `/ops` and tickets.

References: https://nextjs.org/docs/app/guides/data-security,
https://supabase.com/docs/guides/database/functions
