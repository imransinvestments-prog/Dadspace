-- Public directory pages read visible venues ordered by name and paged by offset.
-- Without a matching index every page sequentially scans and sorts the whole
-- table, which reached the 8s statement timeout under load. These partial
-- indexes serve the two read shapes in lib/venue-discovery.ts (national browse,
-- and area + category pages) and let the visible-venue count use an index-only
-- scan. Additive only; no venue rows are changed.
--
-- Not CONCURRENTLY: migrations run inside a transaction, so each build blocks
-- writes to public.venues until it finishes (expected to be brief at ~60k rows).
create index if not exists venues_public_name_idx
  on public.venues (venue_name, id)
  where public_visible;

create index if not exists venues_public_town_category_name_idx
  on public.venues (town_city, category, venue_name, id)
  where public_visible;
