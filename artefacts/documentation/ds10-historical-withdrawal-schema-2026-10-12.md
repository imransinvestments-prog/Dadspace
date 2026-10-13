# Historical withdrawal schema

Reversible withdrawal metadata; existing feed columns and RLS remain unchanged. Withdrawn rows are excluded from both public feed views and collector identity reuse. No data updates or deletions in this migration.

```sql
alter table public.collected_events add column if not exists withdrawn_at timestamptz, add column if not exists withdrawal_reason text, add column if not exists superseded_by uuid references public.collected_events(id) on delete set null;
alter table public.collected_events add constraint collected_events_withdrawal_reason_check check ((withdrawn_at is null and withdrawal_reason is null and superseded_by is null) or (withdrawn_at is not null and nullif(btrim(withdrawal_reason),'') is not null));
create or replace view public.current_activities with (security_invoker=true) as  SELECT id,
    source_id,
    title,
    description,
    start_date,
    end_date,
    time_text,
    location,
    event_url,
    cost_text,
    age_range,
    recurrence,
    family_relevance,
    confidence,
    source_url,
    extraction_method,
    dedupe_key,
    first_seen_at,
    last_verified_at,
    listing_type,
    is_holiday_camp,
    schedule_text,
    category,
    venue_name,
    venue_address,
    postcode,
    venue_id,
    last_seen_at
   FROM collected_events
  WHERE (withdrawn_at is null) AND ((listing_type = 'activity'::text) AND (last_seen_at >= (now() - '60 days'::interval)));
create or replace view public.upcoming_events with (security_invoker=true) as  SELECT id,
    source_id,
    title,
    description,
    start_date,
    end_date,
    time_text,
    location,
    event_url,
    cost_text,
    age_range,
    recurrence,
    family_relevance,
    confidence,
    source_url,
    extraction_method,
    dedupe_key,
    first_seen_at,
    last_verified_at,
    listing_type,
    is_holiday_camp,
    schedule_text,
    category,
    venue_name,
    venue_address,
    postcode,
    venue_id,
    last_seen_at
   FROM collected_events
  WHERE (withdrawn_at is null) AND ((listing_type = 'event'::text) AND (start_date IS NOT NULL) AND (COALESCE(end_date, start_date) >= ((now() AT TIME ZONE 'Europe/London'::text))::date));
CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_existing_dedupe text;
begin
  new.identity_key := public.dadspace_event_identity(
    new.listing_type, new.title, new.start_date, new.event_url,
    new.venue_id, new.postcode, new.venue_name, new.location
  );

  new.content_hash := md5(concat_ws('|',
    coalesce(new.title,''), coalesce(new.description,''), coalesce(new.start_date::text,''),
    coalesce(new.end_date::text,''), coalesce(new.time_text,''), coalesce(new.location,''),
    coalesce(new.event_url,''), coalesce(new.cost_text,''), coalesce(new.age_range,''),
    coalesce(new.recurrence,''), coalesce(new.listing_type,''), coalesce(new.schedule_text,''),
    coalesce(new.category,''), coalesce(new.venue_name,''), coalesce(new.venue_address,''),
    coalesce(new.postcode,''), coalesce(new.venue_id::text,'')));

  -- Current collectors still upsert on dedupe_key. If this stable identity already
  -- exists, reuse its dedupe_key so their ON CONFLICT(dedupe_key) updates that row
  -- instead of inserting a second real-world event.
  select c.dedupe_key into v_existing_dedupe
  from public.collected_events c
  where c.identity_key = new.identity_key
    and c.withdrawn_at is null
    and (tg_op = 'INSERT' or c.id <> new.id)
  limit 1;

  if v_existing_dedupe is not null then
    new.dedupe_key := v_existing_dedupe;
  end if;

  return new;
end;
$function$
;

```
