-- Speed up council discovery (owner, 24 Oct 2026): besides the twice-daily workers run, dispatch
-- a council-only batch (venue-reference.yml, 10 councils) every 15 minutes, about 40 councils an
-- hour instead of 20 a day. Needs 20261022130000_scheduled_dispatch_timer.sql.
--
-- The timer stops dispatching by itself once every GB council in the latest geography release
-- has an ok or no_boundary run within the refresh window (venue_council_discovery.py:
-- REFRESH_DAYS 180, Northern Ireland excluded). Retries of failed councils and missing boundaries
-- are left to the twice-daily run. To stop it early:
--   select cron.unschedule('dadspace-council-discovery-timer');
create or replace function public.dadspace_council_discovery_pending()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.geography_areas a
    where a.kind = 'council' and a.code not like 'N%'
      and a.release_id = (select id from public.geography_releases order by imported_at desc limit 1)
      and not exists (
        select 1 from public.venue_council_discovery_runs r
        where r.council_code = a.code and r.status in ('ok', 'no_boundary')
          and r.ran_at > now() - interval '180 days'))
$$;
revoke all on function public.dadspace_council_discovery_pending() from public, anon, authenticated, service_role;

-- Every quarter hour is a London slot, so all 24 hours are allowed.
select cron.schedule('dadspace-council-discovery-timer', '*/15 * * * *',
  $$select public.dadspace_dispatch_slot('venue-reference.yml', array(select generate_series(0, 23)),
      '{"dry_run": "false", "council_discovery_only": "true"}')
    where public.dadspace_council_discovery_pending()$$);
