alter table public.collected_events add column if not exists date_backfill_reviewed_at timestamptz, add column if not exists date_backfill_review_note text;
create or replace function public.dadspace_guard_reviewed_activity_dates()
returns trigger language plpgsql set search_path=public,pg_temp as $guard$
begin
 if old.date_backfill_reviewed_at is not null
    and new.date_backfill_reviewed_at is not distinct from old.date_backfill_reviewed_at then
  if old.start_date is not null and new.start_date is null and new.end_date is null then
   new.start_date=old.start_date; new.end_date=old.end_date;
   new.schedule_text=old.schedule_text; new.time_text=old.time_text;
   new.last_seen_at=old.last_seen_at; new.last_verified_at=old.last_verified_at;
   new.date_backfill_review_note='Incoming collector omitted reviewed dates; evidence retained without verification refresh.';
  elsif pg_trigger_depth()>1 then
   new.last_seen_at=old.last_seen_at; new.last_verified_at=old.last_verified_at;
   new.date_backfill_review_note='Source-level refresh cannot verify individually reviewed dated sessions.';
  end if;
 end if;
 return new;
end;
$guard$;
create trigger collected_events_guard_reviewed_dates
before update of start_date,end_date,schedule_text,time_text,last_seen_at,last_verified_at,date_backfill_reviewed_at
on public.collected_events for each row execute function public.dadspace_guard_reviewed_activity_dates();
