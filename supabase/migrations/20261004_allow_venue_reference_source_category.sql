-- Production received this constraint update as a follow-up migration during release.
-- Keep it explicit in repository history so database state and migrations stay aligned.
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

update public.sources
set category = 'venue_reference'
where source_role = 'venue_reference';
