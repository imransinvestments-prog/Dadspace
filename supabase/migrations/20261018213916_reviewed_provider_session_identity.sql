-- Additive capability only. The approved existing-row adoption cohort is empty.
-- No source is enrolled or activated by this migration.
set lock_timeout='3s';
create table public.activity_identity_installation (
 singleton boolean primary key default true check(singleton),
 original_identity text not null, original_review text not null,
 original_trigger text not null, installed_fingerprint text
);
alter table public.activity_identity_installation enable row level security;
revoke all on public.activity_identity_installation from public,anon,authenticated,service_role;
insert into public.activity_identity_installation(original_identity,original_review,original_trigger)
 select pg_get_functiondef('public.dadspace_set_event_identity()'::regprocedure),
        pg_get_functiondef('public.dadspace_review_snapshot(text,uuid,uuid)'::regprocedure),
        pg_get_triggerdef(oid) from pg_trigger
 where tgrelid='public.collected_events'::regclass and tgname='collected_events_set_identity';
alter table public.collected_events
 add column provider_namespace text,
 add column provider_session_id text,
 add column provider_occurrences jsonb;

create table public.activity_identity_sources (
 source_id uuid primary key references public.sources(id),
 namespace text not null unique check(namespace='ealing.events.mylibrary.digital'),
 session_ids text[] not null check(cardinality(session_ids) between 1 and 20
   and session_ids <@ array['264038','319285']::text[]),
 approved_reason text not null check(length(btrim(approved_reason)) between 10 and 1000),
 created_at timestamptz not null default now()
);
create table public.activity_identity_audit (
 id uuid primary key default gen_random_uuid(), listing_id uuid not null,
 database_actor text not null default current_user,
 created_at timestamptz not null default now(),
 before_row jsonb, after_row jsonb not null
);
alter table public.activity_identity_sources enable row level security;
alter table public.activity_identity_audit enable row level security;
revoke all on public.activity_identity_sources,public.activity_identity_audit from public,anon,authenticated,service_role;
grant select on public.activity_identity_sources to service_role;
grant select,insert on public.activity_identity_audit to service_role;
create index activity_identity_audit_listing on public.activity_identity_audit(listing_id,created_at);

create function public.dadspace_guard_provider_session() returns trigger
language plpgsql security invoker set search_path=pg_catalog,public as $$
declare rule public.activity_identity_sources%rowtype; occurrence jsonb; ids text[]:='{}';
begin
 select * into rule from public.activity_identity_sources where source_id=new.source_id;
 if new.provider_namespace is null and new.provider_session_id is null and new.provider_occurrences is null then
  if rule.source_id is not null and new.listing_type='activity' then
   raise exception 'Enrolled source requires explicit session identity';
  end if;
  if tg_op='UPDATE' and old.provider_session_id is not null then
   raise exception 'Provider identity cannot be removed by an importer';
  end if;
  return new;
 end if;
 if rule.source_id is null or new.listing_type is distinct from 'activity'
    or new.provider_namespace is distinct from rule.namespace
    or new.provider_session_id is null or not(new.provider_session_id=any(rule.session_ids))
    or new.provider_occurrences is null or jsonb_typeof(new.provider_occurrences)<>'array' then
  raise exception 'Unqualified provider session identity';
 end if;
 if jsonb_array_length(new.provider_occurrences) not between 1 and 200 then
  raise exception 'Bounded occurrence provenance required';
 end if;
 for occurrence in select value from jsonb_array_elements(new.provider_occurrences) loop
  if coalesce(occurrence->>'id','') !~ '^[1-9][0-9]*$'
    or occurrence->>'url' is distinct from ('https://' || rule.namespace || '/event?id=' || (occurrence->>'id'))
    or (occurrence->>'id')=any(ids) then
   raise exception 'Contradictory occurrence provenance';
  end if;
  ids:=array_append(ids,occurrence->>'id');
 end loop;
 if tg_op='UPDATE' then
  if old.provider_session_id is null then
   -- No importer can silently adopt an existing legacy row on a dedupe conflict.
   -- Any future adoption must be a separately reviewed, fingerprinted operation.
   raise exception 'Existing legacy row requires reviewed identity adoption';
  end if;
  if old.source_id is distinct from new.source_id
    or old.provider_namespace is distinct from new.provider_namespace
    or old.provider_session_id is distinct from new.provider_session_id then
   raise exception 'Provider identity reassignment requires a new reviewed mapping';
  end if;
  if coalesce(current_setting('dadspace.review_write',true),'off')<>'on' and
    (old.venue_id is distinct from new.venue_id or old.venue_name is distinct from new.venue_name
     or old.location is distinct from new.location or old.postcode is distinct from new.postcode
     or old.withdrawn_at is distinct from new.withdrawn_at) then
   raise exception 'Provider place or retirement change requires a reviewed operation';
  end if;
 end if;
 -- Serialise the same session across independent connections. Unique indexes
 -- remain authoritative; any conflict still fails the save and freshness path.
 perform pg_advisory_xact_lock(hashtextextended(rule.namespace || '|' || new.provider_session_id,0));
 return new;
end $$;

create trigger ab_provider_session_guard before insert or update on public.collected_events
 for each row execute function public.dadspace_guard_provider_session();

create function public.dadspace_audit_provider_session() returns trigger
language plpgsql security invoker set search_path=pg_catalog,public as $$
begin
 if new.provider_session_id is not null then
  insert into public.activity_identity_audit(listing_id,before_row,after_row)
   values(new.id,case when tg_op='UPDATE' then to_jsonb(old) else null end,to_jsonb(new));
 end if;
 return null;
end $$;
create trigger provider_session_audit after insert or update on public.collected_events
 for each row execute function public.dadspace_audit_provider_session();

revoke execute on function public.dadspace_guard_provider_session(),public.dadspace_audit_provider_session() from public,anon,authenticated;
grant execute on function public.dadspace_guard_provider_session(),public.dadspace_audit_provider_session() to service_role;

-- Existing reviewed venue/provenance guards run before this identity trigger.
-- Nullable additions must not invalidate existing reviewed row fingerprints.
create function public.dadspace_listing_review_version(p_row public.collected_events)
returns text language sql stable security invoker set search_path=pg_catalog,public as $$
 select case when p_row.provider_namespace is null and p_row.provider_session_id is null
                  and p_row.provider_occurrences is null
 then md5((to_jsonb(p_row)-'provider_namespace'-'provider_session_id'-'provider_occurrences')::text)
 else md5(to_jsonb(p_row)::text) end
$$;
revoke execute on function public.dadspace_listing_review_version(public.collected_events) from public,anon,authenticated;
grant execute on function public.dadspace_listing_review_version(public.collected_events) to service_role;
do $$ declare definition text; begin
 select original_review into definition from public.activity_identity_installation;
 if position('md5(to_jsonb(e)::text)' in definition)=0 then
  raise exception 'Review snapshot changed; inspect compatibility before installation';
 end if;
 execute replace(definition,'md5(to_jsonb(e)::text)','public.dadspace_listing_review_version(e)');
end $$;

CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_existing_dedupe text;
begin
  if new.provider_session_id is not null then
    new.identity_key := md5('activity-session-v1|' || new.provider_namespace || '|' || new.provider_session_id);
  else
    new.identity_key := public.dadspace_event_identity(
    new.listing_type, new.title, new.start_date, new.event_url,
    new.venue_id, new.postcode, new.venue_name, new.location
  );
  end if;

  new.content_hash := md5(concat_ws('|',
    coalesce(new.title,''), coalesce(new.description,''), coalesce(new.start_date::text,''),
    coalesce(new.end_date::text,''), coalesce(new.time_text,''), coalesce(new.location,''),
    coalesce(new.event_url,''), coalesce(new.cost_text,''), coalesce(new.age_range,''),
    coalesce(new.recurrence,''), coalesce(new.listing_type,''), coalesce(new.schedule_text,''),
    coalesce(new.category,''), coalesce(new.venue_name,''), coalesce(new.venue_address,''),
    coalesce(new.postcode,''), coalesce(new.venue_id::text,'')));

  if new.provider_session_id is not null and exists(
    select 1 from public.collected_events c where c.dedupe_key=new.dedupe_key
    and c.identity_key is distinct from new.identity_key
    and (tg_op='INSERT' or c.id<>new.id)) then
    raise exception 'Dedupe key belongs to another identity';
  end if;

  if new.provider_session_id is not null then
    new.content_hash:=md5(new.content_hash || '|' || new.provider_occurrences::text);
  end if;

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


drop trigger collected_events_set_identity on public.collected_events;
create trigger collected_events_set_identity before insert or update on public.collected_events
 for each row execute function public.dadspace_set_event_identity();
reset lock_timeout;

create function public.dadspace_provider_install_fingerprint() returns text
language sql stable security invoker set search_path=pg_catalog,public as $$
 select md5(concat_ws('|',
   pg_get_functiondef('public.dadspace_set_event_identity()'::regprocedure),
   pg_get_functiondef('public.dadspace_review_snapshot(text,uuid,uuid)'::regprocedure),
   pg_get_functiondef('public.dadspace_guard_provider_session()'::regprocedure),
   pg_get_functiondef('public.dadspace_audit_provider_session()'::regprocedure),
   pg_get_functiondef('public.dadspace_listing_review_version(public.collected_events)'::regprocedure),
   (select string_agg(pg_get_triggerdef(oid),'|' order by tgname) from pg_trigger
    where tgrelid='public.collected_events'::regclass and tgname in
      ('collected_events_set_identity','ab_provider_session_guard','provider_session_audit'))))
$$;
revoke execute on function public.dadspace_provider_install_fingerprint() from public,anon,authenticated,service_role;
update public.activity_identity_installation set installed_fingerprint=public.dadspace_provider_install_fingerprint();
