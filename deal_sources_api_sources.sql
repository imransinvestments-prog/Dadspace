-- Dadspace deal source adapters: Awin, FMTC and Pepper/HotUKDeals API.
-- Safe to run more than once in the Supabase SQL editor.
--
-- New API sources are deliberately INACTIVE. Turn each on only when its
-- credentials/endpoint are ready. Existing RSS sources are not changed.

-- If deal_sources currently restricts source_type to RSS, replace that check
-- with the set supported by the deals worker. The DO block only removes CHECK
-- constraints on this table that explicitly reference source_type.
do $$
declare
  c record;
begin
  for c in
    select conname
    from pg_constraint
    where conrelid = 'public.deal_sources'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%source_type%'
  loop
    execute format('alter table public.deal_sources drop constraint %I', c.conname);
  end loop;
end $$;

alter table public.deal_sources
  drop constraint if exists deal_sources_source_type_check;

alter table public.deal_sources
  add constraint deal_sources_source_type_check
  check (source_type in ('rss', 'awin', 'fmtc', 'pepper'));

-- The url column is UNIQUE in Dadspace. Awin and FMTC use unique config://
-- sentinel URLs here; the Python adapters recognise these and substitute the
-- provider's real API endpoint at runtime.
insert into public.deal_sources (name, url, source_type, active)
select 'Awin Offers API', 'config://awin', 'awin', false
where not exists (
  select 1 from public.deal_sources where source_type = 'awin'
);

insert into public.deal_sources (name, url, source_type, active)
select 'FMTC Deal Feed', 'config://fmtc', 'fmtc', false
where not exists (
  select 1 from public.deal_sources where source_type = 'fmtc'
);

-- Pepper / HotUKDeals REST API. Replace this base URL with the exact
-- thread-list/deal-list endpoint from the Pepper API documentation before
-- activating the row.
insert into public.deal_sources (name, url, source_type, active)
select 'HotUKDeals - Pepper API', 'https://www.hotukdeals.com/rest_api/v2', 'pepper', false
where not exists (
  select 1 from public.deal_sources where source_type = 'pepper'
);

-- Check the result. Toggle active=true only when that source is ready.
select id, name, source_type, active, url
from public.deal_sources
order by id;
