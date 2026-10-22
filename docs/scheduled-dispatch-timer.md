# Scheduled dispatch timer (#124)

GitHub's `schedule` trigger has started runs 2.5–7 hours late since 15 October 2026 and drops the Originals 07:17 slot. A `pg_cron` timer in Supabase now calls GitHub's workflow-dispatch API at the London slot times:

| Workflow | London slots | Inputs sent |
|---|---|---|
| `daily-workers.yml` | 07:17, 19:17 | `timer_slot` |
| `original-content.yml` | 07:17, 09:17 | `dry_run=false`, `cadence=all`, `timer_slot` |

The migration is `supabase/migrations/20261022130000_scheduled_dispatch_timer.sql`.

**How it works:**
- `pg_cron` runs in UTC, so each slot is scheduled at both its GMT and BST UTC hour; only the call whose London hour is a real slot dispatches.
- A unique `(workflow, slot)` row means a slot is dispatched at most once.
- Timer runs are named "… timer slot YYYY-MM-DDTHH:MM", which is how the slot ledger and Operations recognise them.
- GitHub's own schedule stays as a backup. The workers gate skips a late scheduled run if a timer run happened in the previous 10 hours. Originals already skips a slot that is published.

## Setup (owner, once)
1. **Token.** GitHub → Settings → Developer settings → Fine-grained personal access tokens → Generate:
   - repository access: only `imransinvestments-prog/Dadspace`
   - permission: **Actions: Read and write**
   - expiry: 90 days (set a reminder to rotate it).
2. **Store the token in Vault.** In the Supabase SQL editor, replacing the placeholder:
   ```sql
   select vault.create_secret('PASTE_TOKEN_HERE', 'dadspace_github_dispatch', 'GitHub workflow dispatch for #124');
   ```
3. **Create the timer:** paste the whole migration file into the SQL editor and run it.
4. **Check it is scheduled:**
   ```sql
   select jobname, schedule, active from cron.job where jobname like 'dadspace-%' order by jobname;
   ```
   You should see three active jobs.

## Checking it worked (after the next slot)
```sql
select workflow, slot, status_code, error, created_at from public.scheduled_dispatches order by id desc limit 10;
```
`status_code = 204` means GitHub accepted the run (filled in within 10 minutes). Any other code, or an `error`, says what went wrong. Then confirm on GitHub (Actions → the workflow → a run named "… timer slot …") or run `python scripts/schedule-ledger.py --days 2`, which should show `OK … via timer`.

## Rotate the token
```sql
select vault.update_secret((select id from vault.secrets where name = 'dadspace_github_dispatch'), 'NEW_TOKEN');
```

## Pause or remove
```sql
select cron.unschedule('dadspace-workers-timer');
select cron.unschedule('dadspace-originals-timer');
select cron.unschedule('dadspace-dispatch-status');
```
GitHub's schedule keeps running as before. To remove the token: `delete from vault.secrets where name = 'dadspace_github_dispatch';`

Once the timer has run reliably for a week, the GitHub `schedule:` triggers can be removed (a separate, owner-approved change).
