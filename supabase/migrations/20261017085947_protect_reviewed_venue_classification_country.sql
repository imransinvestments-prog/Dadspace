-- Field-specific protection supplements the existing operations review trigger.
-- No data is corrected or made public by this migration.
create or replace function public.dadspace_preserve_reviewed_geography()
returns trigger language plpgsql
set search_path = pg_catalog, public
as $$
begin
  if coalesce(current_setting('dadspace.review_write', true), 'off') <> 'on' then
    if old.ops_reviewed_at is not null then
      new.category := old.category;
    end if;
    if exists (
      select 1 from public.venue_sources s where s.venue_id = old.id
      and s.source_name = 'Dadspace reviewed geography'
      and s.source_payload->>'country' = old.country
      and s.source_payload->>'accepted' = 'true'
    ) then
      new.country := old.country;
    end if;
  end if;
  return new;
end;
$$;
revoke all on function public.dadspace_preserve_reviewed_geography() from public, anon, authenticated;
create trigger venues_preserve_reviewed_geography
before update on public.venues
for each row execute function public.dadspace_preserve_reviewed_geography();
