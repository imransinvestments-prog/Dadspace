-- Stable event identity enforcement for Dadspace.
-- Keeps current collectors compatible: they can continue upserting on dedupe_key,
-- while the trigger reuses an existing row's dedupe_key whenever the same stable
-- identity is seen again.

create or replace function public.dadspace_norm_text(value text)
returns text
language sql
immutable
set search_path = public, pg_temp
as $$
  select trim(regexp_replace(regexp_replace(lower(coalesce(value,'')), '&', ' and ', 'g'), '[^a-z0-9]+', ' ', 'g'));
$$;

create or replace function public.dadspace_canonical_url(value text)
returns text
language sql
immutable
set search_path = public, pg_temp
as $$
  select case
    when nullif(trim(coalesce(value,'')), '') is null then null
    else lower(regexp_replace(regexp_replace(trim(value), '#.*$', ''), '/$', ''))
  end;
$$;

create or replace function public.dadspace_event_identity(
  p_listing_type text,
  p_title text,
  p_start_date date,
  p_event_url text,
  p_venue_id uuid,
  p_postcode text,
  p_venue_name text,
  p_location text
)
returns text
language plpgsql
immutable
set search_path = public, pg_temp
as $$
declare
  v_type text := lower(coalesce(p_listing_type, 'event'));
  v_url text := public.dadspace_canonical_url(p_event_url);
  v_venue text;
  v_raw text;
begin
  if p_venue_id is not null then
    v_venue := 'venue_id:' || p_venue_id::text;
  elsif nullif(regexp_replace(upper(coalesce(p_postcode,'')), '\s+', '', 'g'), '') is not null then
    v_venue := 'postcode:' || regexp_replace(upper(coalesce(p_postcode,'')), '\s+', '', 'g')
      || '|venue:' || public.dadspace_norm_text(coalesce(p_venue_name, p_location));
  else
    v_venue := 'venue:' || public.dadspace_norm_text(coalesce(p_venue_name, p_location));
  end if;

  if v_type = 'activity' then
    -- Different recurring classes at the same venue must remain distinct.
    v_raw := 'activity|title:' || public.dadspace_norm_text(p_title) || '|' || v_venue;
  elsif v_url is not null then
    -- For dated events, stable URL + occurrence date + venue survives LLM title drift.
    v_raw := 'event|url:' || v_url || '|date:' || coalesce(p_start_date::text,'') || '|' || v_venue;
  else
    v_raw := 'event|title:' || public.dadspace_norm_text(p_title)
      || '|date:' || coalesce(p_start_date::text,'') || '|' || v_venue;
  end if;

  return md5(v_raw);
end;
$$;

create or replace function public.dadspace_set_event_identity()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
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

  -- Existing collectors currently conflict on dedupe_key. Reuse the canonical
  -- row's dedupe_key so an LLM wording change updates that row instead of adding
  -- a second copy of the same real-world event.
  select c.dedupe_key into v_existing_dedupe
  from public.collected_events c
  where c.identity_key = new.identity_key
    and (tg_op = 'INSERT' or c.id <> new.id)
  limit 1;

  if v_existing_dedupe is not null then
    new.dedupe_key := v_existing_dedupe;
  end if;

  return new;
end;
$$;

drop trigger if exists collected_events_set_identity on public.collected_events;
create trigger collected_events_set_identity
before insert or update of title, start_date, event_url, venue_id, postcode, venue_name, location, listing_type,
                         description, end_date, time_text, cost_text, age_range, recurrence, schedule_text, category, venue_address
on public.collected_events
for each row execute function public.dadspace_set_event_identity();
