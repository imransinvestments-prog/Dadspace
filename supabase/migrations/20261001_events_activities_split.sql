-- Events / Activities split for Dadspace
-- Additive/backwards-compatible migration. Existing rows remain visible as events until preview cleanup is approved.

alter table public.collected_events
  add column if not exists listing_type text,
  add column if not exists is_holiday_camp boolean not null default false,
  add column if not exists schedule_text text,
  add column if not exists category text,
  add column if not exists venue_name text,
  add column if not exists venue_address text,
  add column if not exists postcode text,
  add column if not exists venue_id uuid,
  add column if not exists last_seen_at timestamptz;

update public.collected_events
set listing_type = 'event'
where listing_type is null;

update public.collected_events
set last_seen_at = coalesce(last_verified_at, first_seen_at, now())
where last_seen_at is null;

alter table public.collected_events
  alter column listing_type set default 'event',
  alter column listing_type set not null,
  alter column start_date drop not null,
  alter column end_date drop not null;

alter table public.collected_events
  drop constraint if exists collected_events_listing_type_check;
alter table public.collected_events
  add constraint collected_events_listing_type_check
  check (listing_type in ('event','activity'));

alter table public.collected_events
  drop constraint if exists collected_events_venue_id_fkey;
alter table public.collected_events
  add constraint collected_events_venue_id_fkey
  foreign key (venue_id) references public.venues(id) on delete set null;

create index if not exists idx_collected_events_listing_type on public.collected_events(listing_type);
create index if not exists idx_collected_events_last_seen_at on public.collected_events(last_seen_at);
create index if not exists idx_collected_events_postcode on public.collected_events(postcode);
create index if not exists idx_collected_events_venue_id on public.collected_events(venue_id);

alter table public.venues
  add column if not exists public_visible boolean not null default true,
  add column if not exists discovery_status text,
  add column if not exists discovered_at timestamptz,
  add column if not exists discovered_source_url text,
  add column if not exists review_reason text;

update public.venues
set discovery_status = 'existing'
where discovery_status is null;

create index if not exists idx_venues_public_visible on public.venues(public_visible);
create index if not exists idx_venues_discovery_status on public.venues(discovery_status);
create index if not exists idx_venues_name_postcode on public.venues(lower(venue_name), upper(postcode));

create or replace view public.upcoming_events
with (security_invoker = true)
as
select
  id, source_id, title, description, start_date, end_date, time_text, location,
  event_url, cost_text, age_range, recurrence, family_relevance, confidence,
  source_url, extraction_method, dedupe_key, first_seen_at, last_verified_at,
  listing_type, is_holiday_camp, schedule_text, category,
  venue_name, venue_address, postcode, venue_id, last_seen_at
from public.collected_events
where listing_type = 'event'
  and start_date is not null
  and coalesce(end_date, start_date) >= (now() at time zone 'Europe/London')::date;

create or replace view public.current_activities
with (security_invoker = true)
as
select
  id, source_id, title, description, start_date, end_date, time_text, location,
  event_url, cost_text, age_range, recurrence, family_relevance, confidence,
  source_url, extraction_method, dedupe_key, first_seen_at, last_verified_at,
  listing_type, is_holiday_camp, schedule_text, category,
  venue_name, venue_address, postcode, venue_id, last_seen_at
from public.collected_events
where listing_type = 'activity'
  and last_seen_at >= now() - interval '60 days';

create or replace view public.venues_to_review
with (security_invoker = true)
as
select *
from public.venues
where discovery_status = 'discovered'
   or review_reason is not null
order by discovered_at desc nulls last, venue_name;

-- Placeholder forum: secure it now. No public policies are added, so it remains inaccessible via anon/authenticated API.
alter table public.forum_threads enable row level security;

-- Public venue browsing must exclude hidden/discovered rows until reviewed.
drop policy if exists "Public venues are readable" on public.venues;
create policy "Public venues are readable"
on public.venues
for select
to anon, authenticated
using (public_visible = true);

grant select on public.venues to anon, authenticated;
grant select on public.upcoming_events to anon, authenticated;
grant select on public.current_activities to anon, authenticated;
revoke all on public.venues_to_review from anon, authenticated;
