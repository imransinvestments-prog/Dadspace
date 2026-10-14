-- Service-only, SECURITY INVOKER transaction API. Application re-verifies reviewers.
alter table public.venues add column if not exists merged_into uuid references public.venues(id);
alter table public.venues add column if not exists ops_reviewed_at timestamptz;
alter table public.collected_events add column if not exists venue_reviewed_at timestamptz;

create table public.operations_review_audit (
 id uuid primary key default gen_random_uuid(), request_id uuid not null unique,
 actor_id uuid not null, action text not null check(action in ('approve','hide','merge','link','rollback')),
 record_id uuid not null, target_id uuid, reason text not null check(length(btrim(reason)) between 10 and 1000),
 created_at timestamptz not null default now(), before_state jsonb not null, after_state jsonb not null,
 reverted_by uuid references public.operations_review_audit(id)
);
alter table public.operations_review_audit enable row level security;
revoke all on public.operations_review_audit from public, anon, authenticated;
grant select, insert, update on public.operations_review_audit to service_role;
create index operations_review_audit_record_created on public.operations_review_audit(record_id,created_at desc);

create function public.dadspace_review_snapshot(p_action text,p_record uuid,p_target uuid)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare vids uuid[]; bulk boolean:=p_action='merge'; lid uuid; result jsonb;
begin
 if p_action='link' then vids:=array[p_target]; lid:=p_record;
 else vids:=array[p_record,p_target]; end if;
 if bulk and ((select count(*) from public.collected_events where venue_id=any(vids))>200
   or (select count(*) from public.venue_sources where venue_id=any(vids))>200) then
  raise exception 'Review exceeds 200 relationships; engineering review required';
 end if;
 select jsonb_build_object(
 'venues',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'name',v.venue_name,'address',v.address,'postcode',v.postcode,
  'public_visible',v.public_visible,'discovery_status',v.discovery_status,'review_reason',v.review_reason,
  'merged_into',v.merged_into,'ops_reviewed_at',v.ops_reviewed_at,'version',md5(to_jsonb(v)::text)) order by v.id)
  from public.venues v where v.id=any(vids)),'[]'::jsonb),
 'listings',coalesce((select jsonb_agg(jsonb_build_object('id',e.id,'venue_id',e.venue_id,'venue_reviewed_at',e.venue_reviewed_at,
  'version',md5(to_jsonb(e)::text)) order by e.id) from public.collected_events e where (bulk and e.venue_id=any(vids)) or e.id=lid),'[]'::jsonb),
 'provenance',coalesce((select jsonb_agg(jsonb_build_object('id',s.id,'venue_id',s.venue_id,'version',md5(to_jsonb(s)::text)) order by s.id)
  from public.venue_sources s where bulk and s.venue_id=any(vids)),'[]'::jsonb)) into result;
 return result;
end $$;

create function public.dadspace_review_plan(p_action text,p_record uuid,p_target uuid default null)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare state jsonb; v public.venues%rowtype; t public.venues%rowtype; e public.collected_events%rowtype;
 a public.operations_review_audit%rowtype;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 if p_action='rollback' then
  select * into a from public.operations_review_audit where id=p_record;
  if not found or a.action='rollback' or a.reverted_by is not null then raise exception 'Rollback unavailable'; end if;
  state:=public.dadspace_review_snapshot(a.action,a.record_id,a.target_id);
  if state is distinct from a.after_state then raise exception 'Records changed after decision; rollback blocked'; end if;
  return jsonb_build_object('fingerprint',md5(state::text),'action',p_action,'record',p_record,'target',null,
    'summary','Restore the previous reviewed fields and relationships; retain the original audit record.',
    'venues',state->'venues','listings',jsonb_array_length(state->'listings'),'provenance',jsonb_array_length(state->'provenance'));
 end if;
 if p_action is null or p_action not in ('approve','hide','merge','link') then raise exception 'Invalid review action'; end if;
 if p_record is null then raise exception 'Record required'; end if;
 if p_action='link' then
  select * into e from public.collected_events where id=p_record and withdrawn_at is null;
  if not found or e.venue_id is not null then raise exception 'Listing is no longer unresolved'; end if;
 else
  select * into v from public.venues where id=p_record;
  if not found or v.merged_into is not null then raise exception 'Venue unavailable or already merged'; end if;
 end if;
 if p_action in ('merge','link') then
  select * into t from public.venues where id=p_target and public_visible and merged_into is null;
  if not found or p_target=p_record then raise exception 'Choose a distinct public canonical venue'; end if;
 elsif p_target is not null then raise exception 'Unexpected target'; end if;
 if p_action='approve' and (nullif(btrim(v.venue_name),'') is null
   or (nullif(btrim(v.postcode),'') is null and nullif(btrim(v.address),'') is null)
   or coalesce(v.source_url,'') !~ '^https?://') then raise exception 'Name, location and source evidence required'; end if;
 state:=public.dadspace_review_snapshot(p_action,p_record,p_target);
 return jsonb_build_object('fingerprint',md5(state::text),'action',p_action,'record',p_record,'target',p_target,
  'summary',case p_action when 'approve' then 'Publish this venue as verified. Listing classification and publication stay unchanged.'
    when 'hide' then 'Hide this venue from public discovery. Retain venue, listings and provenance.'
    when 'merge' then 'Hide the duplicate, retain its identity, and move listing/provenance relationships to the canonical venue.'
    else 'Link the unresolved listing to the chosen public venue. Preserve dates, schedule, classification and source evidence.' end,
  'venues',state->'venues','listings',jsonb_array_length(state->'listings'),'provenance',jsonb_array_length(state->'provenance'));
end $$;

create function public.dadspace_review_apply(p_actor uuid,p_request uuid,p_action text,p_record uuid,p_target uuid,p_expected text,p_reason text)
returns uuid language plpgsql security invoker set search_path=pg_catalog,public set lock_timeout='3s' set statement_timeout='10s' as $$
declare plan jsonb; before_data jsonb; after_data jsonb; aid uuid:=gen_random_uuid(); existing public.operations_review_audit%rowtype;
 original public.operations_review_audit%rowtype; row_data jsonb;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 if p_actor is null or p_request is null or length(btrim(coalesce(p_reason,''))) not between 10 and 1000 then raise exception 'Actor, request and review reason required'; end if;
 -- Short, bounded review transactions serialize against imports. Readers remain free.
 lock table public.venues,public.collected_events,public.venue_sources,public.operations_review_audit in share row exclusive mode;
 select * into existing from public.operations_review_audit where request_id=p_request;
 if found then
  if existing.actor_id=p_actor and existing.action=p_action and existing.record_id=p_record
    and existing.target_id is not distinct from p_target and existing.reason=p_reason then return existing.id; end if;
  raise exception 'Request identity already used';
 end if;
 plan:=public.dadspace_review_plan(p_action,p_record,p_target);
 if plan->>'fingerprint' is distinct from p_expected then raise exception 'Preview is stale; review again'; end if;
 perform set_config('dadspace.review_write','on',true);
 if p_action='rollback' then
  select * into original from public.operations_review_audit where id=p_record for update;
  before_data:=original.after_state;
  for row_data in select value from jsonb_array_elements(original.before_state->'venues') loop
   update public.venues set public_visible=(row_data->>'public_visible')::boolean,
    discovery_status=row_data->>'discovery_status',review_reason=row_data->>'review_reason',
    merged_into=(row_data->>'merged_into')::uuid,ops_reviewed_at=(row_data->>'ops_reviewed_at')::timestamptz
    where id=(row_data->>'id')::uuid;
  end loop;
  for row_data in select value from jsonb_array_elements(original.before_state->'listings') loop
   update public.collected_events set venue_id=(row_data->>'venue_id')::uuid,
    venue_reviewed_at=(row_data->>'venue_reviewed_at')::timestamptz where id=(row_data->>'id')::uuid;
  end loop;
  for row_data in select value from jsonb_array_elements(original.before_state->'provenance') loop
   update public.venue_sources set venue_id=(row_data->>'venue_id')::uuid where id=(row_data->>'id')::uuid;
  end loop;
  after_data:=public.dadspace_review_snapshot(original.action,original.record_id,original.target_id);
 else
  before_data:=public.dadspace_review_snapshot(p_action,p_record,p_target);
  if p_action in ('approve','hide') then
   update public.venues set public_visible=p_action='approve',discovery_status=case when p_action='approve' then 'verified' else 'rejected' end,
    review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
  elsif p_action='merge' then
   update public.venues set public_visible=false,discovery_status='merged',merged_into=p_target,review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
   update public.collected_events set venue_id=p_target,venue_reviewed_at=now() where venue_id=p_record;
   update public.venue_sources set venue_id=p_target where venue_id=p_record;
  else
   update public.collected_events set venue_id=p_target,venue_reviewed_at=now() where id=p_record;
  end if;
  after_data:=public.dadspace_review_snapshot(p_action,p_record,p_target);
 end if;
 insert into public.operations_review_audit(id,request_id,actor_id,action,record_id,target_id,reason,before_state,after_state)
 values(aid,p_request,p_actor,p_action,p_record,p_target,p_reason,before_data,after_data);
 if p_action='rollback' then update public.operations_review_audit set reverted_by=aid where id=p_record; end if;
 perform set_config('dadspace.review_write','off',true);
 return aid;
end $$;

-- Preserve explicit decisions through subsequent collector/reference upserts.
create function public.dadspace_preserve_venue_review() returns trigger language plpgsql security invoker set search_path=pg_catalog,public as $$
begin
 if old.ops_reviewed_at is not null and coalesce(current_setting('dadspace.review_write',true),'off')<>'on' then
  new.public_visible:=old.public_visible; new.discovery_status:=old.discovery_status;
  new.review_reason:=old.review_reason; new.merged_into:=old.merged_into; new.ops_reviewed_at:=old.ops_reviewed_at;
  new.venue_name:=old.venue_name; new.address:=old.address; new.postcode:=old.postcode;
  new.latitude:=old.latitude; new.longitude:=old.longitude; new.website:=old.website;
 end if;
 return new;
end $$;
create trigger venues_preserve_operations_review before update on public.venues for each row execute function public.dadspace_preserve_venue_review();

create function public.dadspace_preserve_venue_relationship() returns trigger language plpgsql security invoker set search_path=pg_catalog,public as $$
declare canonical uuid; steps int:=0;
begin
 if tg_table_name='collected_events' and tg_op='UPDATE' then
  if old.venue_reviewed_at is not null and coalesce(current_setting('dadspace.review_write',true),'off')<>'on' then
   new.venue_id:=old.venue_id; new.venue_reviewed_at:=old.venue_reviewed_at;
  end if;
 end if;
 loop
  select merged_into into canonical from public.venues where id=new.venue_id;
  exit when canonical is null;
  steps:=steps+1; if steps>20 then raise exception 'Canonical venue chain invalid'; end if;
  new.venue_id:=canonical;
 end loop;
 return new;
end $$;
-- Run before identity/dedupe computation, including repeat imports after a merge.
create trigger aa_operations_venue_relationship before insert or update on public.collected_events for each row execute function public.dadspace_preserve_venue_relationship();
create trigger aa_operations_venue_provenance before insert or update on public.venue_sources for each row execute function public.dadspace_preserve_venue_relationship();

revoke execute on function public.dadspace_review_snapshot(text,uuid,uuid),public.dadspace_review_plan(text,uuid,uuid),
 public.dadspace_review_apply(uuid,uuid,text,uuid,uuid,text,text),public.dadspace_preserve_venue_review(),public.dadspace_preserve_venue_relationship() from public,anon,authenticated;
grant execute on function public.dadspace_review_snapshot(text,uuid,uuid),public.dadspace_review_plan(text,uuid,uuid),
 public.dadspace_review_apply(uuid,uuid,text,uuid,uuid,text,text),public.dadspace_preserve_venue_review(),public.dadspace_preserve_venue_relationship() to service_role;
