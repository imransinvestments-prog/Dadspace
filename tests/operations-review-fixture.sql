create role anon;
create role authenticated;
create role service_role bypassrls;
create table public.venues(id uuid primary key default gen_random_uuid(),venue_name text,address text,postcode text,
 source_url text unique,public_visible boolean not null default false,discovery_status text,review_reason text,
 latitude double precision,longitude double precision,website text);
create table public.collected_events(id uuid primary key default gen_random_uuid(),title text,venue_id uuid references public.venues(id),
 withdrawn_at timestamptz,start_date date,end_date date,schedule_text text,listing_type text,recurrence text);
create table public.venue_sources(id uuid primary key default gen_random_uuid(),venue_id uuid references public.venues(id),
 source_name text,source_record_id text,unique(source_name,source_record_id));
grant all on public.venues,public.collected_events,public.venue_sources to service_role;
