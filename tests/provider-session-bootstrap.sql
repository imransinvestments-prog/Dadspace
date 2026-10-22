create table public.sources(id uuid primary key,source_adapter text);
alter table public.collected_events
 add column source_id uuid references public.sources(id),
 add column identity_key text unique,add column content_hash text,
 add column description text,add column time_text text,add column location text,
 add column event_url text,add column cost_text text,add column age_range text,
 add column category text,add column venue_name text,add column venue_address text,
 add column postcode text,add column is_holiday_camp boolean,
 add column family_relevance int,add column confidence double precision,
 add column source_url text,add column extraction_method text,
 add column last_seen_at timestamptz,add column last_verified_at timestamptz;
