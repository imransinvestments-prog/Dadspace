-- Exact-time dispatch for scheduled GitHub workflows (#124).
-- Since 15 Oct 2026 GitHub's own `schedule` trigger has started these workflows
-- 2.5-7 hours late and dropped the Originals 07:17 slot. This timer calls the
-- workflow_dispatch API at the Europe/London slot time instead; the GitHub
-- schedule stays as a backup and the workers gate skips its late duplicate.
--
-- Before scheduling: the owner stores a fine-grained token (this repository only,
-- Actions: read and write) in Vault under the name dadspace_github_dispatch:
--   select vault.create_secret('<token>', 'dadspace_github_dispatch', 'GitHub workflow dispatch for #124');
-- The token never appears in this file, the repository or a log.

create extension if not exists pg_cron;
create extension if not exists pg_net with schema extensions;

-- One row per workflow slot: the unique key is what stops a slot being dispatched twice.
create table if not exists public.scheduled_dispatches (
  id bigint generated always as identity primary key,
  workflow text not null,
  slot text not null, -- Europe/London wall-clock time, e.g. 2026-10-23T07:17
  request_id bigint,
  status_code integer, -- GitHub answers 204 when the run is accepted
  error text,
  created_at timestamptz not null default now(),
  unique (workflow, slot)
);
alter table public.scheduled_dispatches enable row level security;
revoke all on public.scheduled_dispatches from public, anon, authenticated;
grant select on public.scheduled_dispatches to service_role;

-- pg_cron runs in UTC, so each slot is scheduled at both its GMT and BST hour and
-- only the call whose London hour is a real slot dispatches. p_at exists for tests.
create or replace function public.dadspace_dispatch_slot(p_workflow text, p_london_hours integer[], p_inputs jsonb default '{}', p_at timestamptz default now())
returns text language plpgsql security definer set search_path = '' as $$
declare
  v_london timestamp := p_at at time zone 'Europe/London';
  v_slot text := to_char(p_at at time zone 'Europe/London', 'YYYY-MM-DD"T"HH24:MI');
  v_token text;
  v_request bigint;
begin
  if not (extract(hour from v_london)::integer = any(p_london_hours)) then
    return 'not a London slot: ' || v_slot;
  end if;
  insert into public.scheduled_dispatches (workflow, slot) values (p_workflow, v_slot)
    on conflict (workflow, slot) do nothing;
  if not found then
    return 'already dispatched: ' || v_slot;
  end if;
  select decrypted_secret into v_token from vault.decrypted_secrets where name = 'dadspace_github_dispatch' limit 1;
  if v_token is null then
    update public.scheduled_dispatches set error = 'Vault secret dadspace_github_dispatch is missing'
      where workflow = p_workflow and slot = v_slot;
    return 'missing token: ' || v_slot;
  end if;
  select net.http_post(
    url := 'https://api.github.com/repos/imransinvestments-prog/Dadspace/actions/workflows/' || p_workflow || '/dispatches',
    body := jsonb_build_object('ref', 'main', 'inputs', p_inputs || jsonb_build_object('timer_slot', v_slot)),
    headers := jsonb_build_object('Authorization', 'Bearer ' || v_token, 'Accept', 'application/vnd.github+json',
      'X-GitHub-Api-Version', '2022-11-28', 'User-Agent', 'dadspace-supabase-timer', 'Content-Type', 'application/json'),
    timeout_milliseconds := 10000) into v_request;
  update public.scheduled_dispatches set request_id = v_request where workflow = p_workflow and slot = v_slot;
  return 'dispatched: ' || v_slot;
end $$;

-- pg_net keeps responses for about six hours; copy GitHub's answer onto the slot row so
-- the evidence lasts. Anything other than 204 is kept as the error.
create or replace function public.dadspace_record_dispatch_status()
returns integer language plpgsql security definer set search_path = '' as $$
declare v_updated integer;
begin
  update public.scheduled_dispatches d
    set status_code = r.status_code,
        error = coalesce(d.error, case when r.status_code is distinct from 204 then left(coalesce(r.error_msg, r.content::text, 'no response'), 300) end)
    from net._http_response r
    where r.id = d.request_id and d.status_code is null and (r.status_code is not null or r.error_msg is not null);
  get diagnostics v_updated = row_count;
  return v_updated;
end $$;

-- Only pg_cron (running as the owner) may call these: they read the Vault token.
revoke all on function public.dadspace_dispatch_slot(text, integer[], jsonb, timestamptz) from public, anon, authenticated, service_role;
revoke all on function public.dadspace_record_dispatch_status() from public, anon, authenticated, service_role;

-- Workers: 07:17 and 19:17 London. Originals: 07:17 and 09:17 London; a manual run
-- defaults to a dry run, so the timer must publish explicitly.
select cron.schedule('dadspace-workers-timer', '17 6,7,18,19 * * *',
  $$select public.dadspace_dispatch_slot('daily-workers.yml', array[7, 19])$$);
select cron.schedule('dadspace-originals-timer', '17 6,7,8,9 * * *',
  $$select public.dadspace_dispatch_slot('original-content.yml', array[7, 9], '{"dry_run": "false", "cadence": "all"}')$$);
select cron.schedule('dadspace-dispatch-status', '*/10 * * * *',
  $$select public.dadspace_record_dispatch_status()$$);
