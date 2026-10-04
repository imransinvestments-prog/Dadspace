-- Dadspace news locality metadata.
-- Additive/backwards-compatible: existing rows remain NULL and continue to use
-- the current nation-level behaviour until they age out of the 14-day feed.

alter table public.news_items
  add column if not exists geo_scope text,
  add column if not exists geo_region text,
  add column if not exists admin_area text,
  add column if not exists locality text;

comment on column public.news_items.geo_scope is
  'Geographic breadth: nationwide, regional, or local. NULL means legacy/unclassified.';
comment on column public.news_items.geo_region is
  'Normalised broad region within a UK nation, e.g. east_of_england.';
comment on column public.news_items.admin_area is
  'Normalised council/county/admin area for local news matching.';
comment on column public.news_items.locality is
  'Normalised town/city/locality for local news matching.';

create or replace view public.feed_items as
select
  id,
  title,
  url,
  source_name,
  published_at,
  summary,
  why_it_matters,
  category,
  relevance,
  region,
  geo_scope,
  geo_region,
  admin_area,
  locality
from public.news_items
where relevance >= 3
  and coalesce(published_at, created_at) > now() - interval '14 days'
order by coalesce(published_at, created_at) desc;
