# Sprint 6 — implementation and decisions

Tracker [#185](https://github.com/imransinvestments-prog/Dadspace/issues/185). **22 committed / 0 accepted / 22 remaining**. This is a preview increment, not sprint closure.

## Entry point and owner workload

Open `/ops/editorial` on the PR preview and sign in with the existing owner account. Review the Originals, News, source and draft/history tabs; prepare a preview from a record. Preview deployments cannot execute live actions, even if production flags are accidentally copied. Existing content approvals remain settled: **zero repeat News/Originals content judgments requested**. The owner usability pass covers the new workspace and preview explanations, not a fresh article sample.

## Decisions prepared for the owner

1. **Publish schedule:** replace the existing 19:17 Originals run with the specified 09:17 London retry, retaining the 07:17 daily/Friday run. Retry skips any existing slot, including an operator-hidden slot. Pushing code will run checks but no longer generate a paid article automatically.
2. **Maintenance access:** retain owner-only Operations access and add a separate exact-user-ID maintainer setting. Recommendation: only the same confirmed owner account. Review permission never confers maintenance permission. Keep live maintenance disabled until approved configuration and release readback.
3. **Bounded retries:** recommend opt-in News retry for one currently active source, at most ten candidates and a five-minute collection budget (in-flight requests may finish later), with no global retention cleanup or automatic source pause; Originals retry for today's due slot only, at most two drafts/two independent editorial review requests. Dry runs may still cost money. Billed cost is unknown; no paid diagnostic or maintenance run has been performed. A separate approved retry-policy flag and Actions token are needed before this is usable in production.
4. **Publication/source actions:** one-record hide, source pause/activation and restore have exact previews and audit history. Actual source activation still needs its specific policy decision; no activation or unpublish is proposed in this pack. Restore refuses newer evidence and never deletes an identity/history.

These are implementation recommendations awaiting the consolidated review; no new maintenance role, token, live retry policy or publication decision has been enabled.

## Delivered increment

- Server-verified owner gate on all editorial reads; separate maintenance identity on each write.
- Actor/action/record/reason/mode/fingerprint-bound ten-minute signed previews. Generic errors expose no raw database payloads or secret values.
- Service-only, RLS-protected future draft/rejection/validation/publication evidence and maintenance audit. Historical drafts remain unknown. Model request counts are recorded cumulatively; unavailable token usage and billed costs remain unknown.
- Atomic hide/pause/activate/restore, stale checks, duplicate request guards and full private before/after snapshots. Public News view and Originals RLS/readers enforce hiding without destroying slot identities.
- Remote dispatch claimed before submission. Ambiguous responses stay unresolved and block another request. The normal runner consumes the exact claim once, rechecks the scope and reports its result. Manual reconciliation requires a completed matching main-branch workflow whose displayed request UUID matches; it never runs a worker itself.
- A News-only source selector and shared non-cancelling News concurrency group. Other healthy feed collectors stay independent.
- A targeted News retry is capped inside a single feed, skips feed-wide deletion and automatic source pause, and reports source/batch/fatal failures in both live and dry runs. Remote authentication/billing/rate-limit denials are not retried.

Local validation: 168 Node tests (including PostgreSQL rehearsal), 12 Originals tests, four runner-claim tests and five bounded-News tests; 11 Python locality tests, TypeScript and webpack production build. Initial hosted checks and Vercel passed; subsequent changes must pass again before release. A broad Python discovery job initially lacked News-only dependencies: News-specific regressions now run alongside locality checks in the dedicated News workflow. No live collection or paid test was started.

## Database setup evidence

The additive `sprint6_news_maintenance_evidence` migration was applied after PostgreSQL rehearsals. It changes no existing activation/publication state. The transaction aborts if public News membership changes during installation. Readback:

| Check | Before and after |
| --- | --- |
| Public News ID digest | `37efdf0915c7366cd92512f7a0b7c853` |
| Originals identity digest | `77c3bd14500d708c5423dec522017edf` |
| News source activation digest | `635988a7f199ad5dc89c73381fa608f5` |

Zero hidden News rows, zero hidden Originals, zero maintenance actions and zero retained attempts immediately after installation. Both new private tables have RLS and deny anon/authenticated SELECT. No historical draft is backfilled.

The Supabase advisor reports intentional service-only tables without public RLS policies. It also reports the existing owner-executed `feed_items` public projection and unrelated pre-existing Auth/function notices; this is not a clean whole-project security audit. Switching that view to invoker without redesigning underlying News access would break the public contract. No new SECURITY DEFINER function was added. See [view security guidance](https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view).

## Remaining acceptance

- Finish hosted deployment/browser checks and normal-runner evidence; verify owner keyboard/mobile usability and any approved configuration/live actions before accepting #146/#147.
- #146's wider source recommendations, schedule management and non-News bounded collection coverage must be reconciled against its complete criteria; News/Originals retry support alone does not close that shared ticket.
- #129 requires actual scheduled daily/Friday publication plus duplicate-safe 09:17 evidence after release. No observed week or future Friday is invented. #125 remains open for all cross-feed criteria.
- No points are accepted merely because code, tests or a preview exists. End with a sprint review before the Deals commitment.

## Recovery

Disable `DADSPACE_MAINTENANCE_ENABLED` to stop UI writes. Preview and ordinary owner reads remain available. Do not blindly retry an uncertain dispatch: inspect the request UUID in Actions and reconcile its completed run. If no matching completed run can be proven, retain the block and investigate rather than clearing it by elapsed time.

Restore an applied hide/source decision through its audit UUID only while its after-state still matches. For deployment rollback, retain the additive tables/columns and audit evidence; old code ignores them. Inspect hidden rows before reverting code that lacks explicit Originals service-reader filtering. Never drop evidence tables or unhide content automatically as a rollback shortcut.
