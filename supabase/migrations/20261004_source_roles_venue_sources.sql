-- Source roles + canonical venue provenance for Dadspace.
-- Category remains compatible with the existing event workers, while
-- source_role describes business responsibility independently of fetch method.

alter table public.sources
  add column if not exists source_role text,
  add column if not exists source_adapter text;

update public.sources
set source_role = case
  when category = 'activities' then 'activity_listing'
  when category in ('councils','heritage_parks','niche_venues') then 'event_listing'
  else coalesce(source_role, 'event_listing')
end
where source_role is null;

alter table public.sources
  alter column source_role set default 'event_listing';

alter table public.sources drop constraint if exists sources_category_check;
alter table public.sources
  add constraint sources_category_check
  check (category = any (array[
    'activities'::text,
    'councils'::text,
    'heritage_parks'::text,
    'niche_venues'::text,
    'venue_reference'::text
  ]));

create index if not exists idx_sources_role_active
  on public.sources (source_role, active);

create table if not exists public.venue_sources (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues(id) on delete cascade,
  source_name text not null,
  source_record_id text,
  source_url text,
  source_role text not null default 'venue_reference',
  match_method text,
  match_confidence numeric(5,4),
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  source_payload jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_name, source_record_id)
);

create index if not exists idx_venue_sources_venue_id
  on public.venue_sources(venue_id);
create index if not exists idx_venue_sources_source_name
  on public.venue_sources(source_name);

alter table public.venue_sources enable row level security;

-- Internal worker table: intentionally no anon/authenticated policies.
-- Service-role collectors can write it; public clients cannot query it directly.

insert into public.sources
  (name, url, category, kind, org_type, focus, nation, region, fetch_method,
   active, notes, source_role, source_adapter)
values
  ('Sport England Active Places',
   'https://apiportal.activeplacespower.com/',
   'venue_reference', 'event_listing', 'sport_england',
   'sports facilities and venue verification', 'England', null, 'unknown',
   false,
   'Authoritative venue-reference source. Activate only after ACTIVE_PLACES_DATA_URL/API credentials are configured; not an activity listing feed.',
   'venue_reference', 'active_places'),
  ('Public Library Open Data',
   'https://schema.librarydata.uk/libraries',
   'venue_reference', 'event_listing', 'public_libraries',
   'library venue verification and enrichment', 'United Kingdom', null, 'unknown',
   false,
   'Schema/standard rather than one current national feed. Use for reconciliation/enrichment when a conforming dataset URL is configured; never bulk-insert without matching existing venues first.',
   'venue_reference', 'library_open_data'),
  ('NCT Local Activities & Meet-ups',
   'https://www.nct.org.uk/local-activities-meet-ups',
   'activities', 'event_listing', 'charity',
   'parent, baby and family groups/events', 'United Kingdom', null, 'js_render',
   false,
   'Strong Dadspace activity fit. Kept inactive until approved data-access/republishing route is confirmed; adapter should use NCT branch/group discovery rather than treating the postcode landing page as a single generic page.',
   'activity_listing', 'nct_group_finder')
on conflict (url) do update set
  category = excluded.category,
  source_role = excluded.source_role,
  source_adapter = excluded.source_adapter,
  notes = excluded.notes;
