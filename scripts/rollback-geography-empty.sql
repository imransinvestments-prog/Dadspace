-- Development-only empty installation inverse. Imported releases/history refuse deletion.
begin;
lock table public.geography_releases,public.geography_areas,public.geography_relationships,public.geography_postcodes in access exclusive mode;
do $$ begin
  if exists(select 1 from geography_releases) or exists(select 1 from geography_areas) or
     exists(select 1 from geography_relationships) or exists(select 1 from geography_postcodes)
  then raise exception 'Cannot discard imported geography history; retain releases and roll back application separately'; end if;
end $$;
drop table public.geography_postcodes,public.geography_relationships,public.geography_areas,public.geography_releases;
drop function public.geography_validate_reference();
commit;
