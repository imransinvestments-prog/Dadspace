-- Source failures and changed pages must not refresh every old activity.
-- Changed-page ingestion refreshes only the rows actually accepted by the worker.
-- Exact unchanged successful checks may renew the stored activity evidence.
create or replace function public.refresh_activity_last_seen_from_source_check()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  if new.last_checked_at is distinct from old.last_checked_at
     and new.last_checked_at is not null
     and new.last_error is null
     and coalesce(new.fail_count, 0) = 0
     and new.last_hash is not null
     and new.last_hash = old.last_hash
     and new.last_success_at is not null
     and new.last_success_at is not distinct from old.last_success_at then
    update public.collected_events
       set last_seen_at = new.last_checked_at
     where source_id = new.id and listing_type = 'activity';
  end if;
  return new;
end;
$$;
revoke execute on function public.refresh_activity_last_seen_from_source_check() from public, anon, authenticated;
