-- Council discovery run log (venue_council_discovery.py). Each run takes the next councils from
-- geography_areas that have no recent successful row here, so all councils are covered over time
-- without re-querying OpenStreetMap for every council on every run. Service role only.
create table if not exists public.venue_council_discovery_runs (
  id bigint generated always as identity primary key,
  council_code text not null,
  release_id text references public.geography_releases(id),
  ran_at timestamptz not null default now(),
  status text not null check (status in ('ok', 'no_boundary', 'failed')),
  candidates integer not null default 0 check (candidates >= 0),
  new_count integer not null default 0 check (new_count >= 0),
  artifact_path text
);

create index if not exists venue_council_discovery_runs_council_idx
  on public.venue_council_discovery_runs (council_code, ran_at desc);

alter table public.venue_council_discovery_runs enable row level security;
revoke all on public.venue_council_discovery_runs from public, anon, authenticated, service_role;
grant select, insert on public.venue_council_discovery_runs to service_role;
create policy venue_council_discovery_runs_service_read on public.venue_council_discovery_runs
  for select to service_role using (true);
create policy venue_council_discovery_runs_service_insert on public.venue_council_discovery_runs
  for insert to service_role with check (true);
