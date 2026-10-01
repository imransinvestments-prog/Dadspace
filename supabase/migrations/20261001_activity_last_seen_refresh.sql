create or replace function public.refresh_activity_last_seen_from_source_check()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.last_checked_at is distinct from old.last_checked_at and new.last_checked_at is not null then
    update public.collected_events
       set last_seen_at = new.last_checked_at
     where source_id = new.id
       and listing_type = 'activity';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_refresh_activity_last_seen on public.sources;
create trigger trg_refresh_activity_last_seen
after update of last_checked_at on public.sources
for each row
execute function public.refresh_activity_last_seen_from_source_check();
