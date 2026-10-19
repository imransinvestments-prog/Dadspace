-- Development only. Extend the existing actor-bound, previewed and audited review API.
-- No production migration or venue correction has been applied.

-- Return only the evidence URL/date for the latest still-current visitor-fact audit.
-- Internal reasons, actor IDs, patches and private audit snapshots never leave this function.
create function public.dadspace_public_venue_visitor_info(p_id uuid) returns jsonb
language plpgsql stable security invoker set search_path=pg_catalog,public as $$
declare result jsonb;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 select jsonb_build_object('source_url',a.requested_patch->>'source_url','checked_at',a.created_at,'reviewed_fields',(select jsonb_agg(k order by k) from jsonb_object_keys(a.requested_patch->'changes') k where k in ('opening_hours','fee','access','website')))
 into result from public.venues v join public.operations_review_audit a on a.record_id=v.id
 where v.id=p_id and v.public_visible and v.merged_into is null and a.action='edit' and a.reverted_by is null
 and (a.requested_patch->'changes') ?| array['opening_hours','fee','access','website']
 and exists(select 1 from jsonb_array_elements(a.after_state->'venues') s where s->>'id'=v.id::text and s->>'version'=md5(to_jsonb(v)::text))
 order by a.created_at desc,a.id desc limit 1;
 return result;
end $$;
revoke execute on function public.dadspace_public_venue_visitor_info(uuid) from public,anon,authenticated;
grant execute on function public.dadspace_public_venue_visitor_info(uuid) to service_role;

create or replace function public.dadspace_review_patch(p_patch jsonb) returns jsonb
language plpgsql immutable security invoker set search_path=pg_catalog,public as $$
declare k text; value jsonb; changes jsonb; str text; n numeric; limit_size int;
begin
 if p_patch is null or jsonb_typeof(p_patch)<>'object' or not(p_patch ? 'changes') or not(p_patch ? 'source_url')
  or exists(select 1 from jsonb_object_keys(p_patch) t(key) where key not in ('changes','source_url')) then raise exception 'Invalid edit payload'; end if;
 str:=p_patch->>'source_url';
 if jsonb_typeof(p_patch->'source_url')<>'string' or length(str)>2048 or str !~ '^https://[^/@[:space:]\\\\]+([/?#][^[:space:]\\\\]*)?$' then raise exception 'HTTPS source evidence required'; end if;
 changes:=p_patch->'changes';
 if jsonb_typeof(changes)<>'object' or changes='{}'::jsonb then raise exception 'Select fields to correct'; end if;
 for k,value in select * from jsonb_each(changes) loop
  if k not in ('venue_name','category','address','postcode','latitude','longitude','website','access','opening_hours','fee') then raise exception 'Unapproved edit field'; end if;
  if k in ('latitude','longitude') then
   if value<>'null'::jsonb then
    if jsonb_typeof(value)<>'number' then raise exception 'Invalid coordinates'; end if;
    n:=value::text::numeric;
    if abs(n)>(case when k='latitude' then 90 else 180 end) then raise exception 'Invalid coordinates'; end if;
   end if;
  else
   if jsonb_typeof(value) not in ('string','null') then raise exception 'Invalid text field'; end if;
   str:=changes->>k;
   if str is not null and (str<>btrim(str) or str='' or str ~ '[[:cntrl:]]') then raise exception 'Text must be trimmed or null'; end if;
   limit_size:=case k when 'venue_name' then 200 when 'category' then 100 when 'address' then 500 when 'postcode' then 20 when 'website' then 2048 when 'opening_hours' then 1000 when 'fee' then 500 else 100 end;
   if length(str)>limit_size or (k in ('venue_name','category') and str is null) then raise exception 'Invalid reviewed fact'; end if;
   if k='website' and str is not null and str !~ '^https://[^/@[:space:]\\\\]+([/?#][^[:space:]\\\\]*)?$' then raise exception 'HTTPS website required'; end if;
  end if;
 end loop;
 if (changes ? 'latitude')<>(changes ? 'longitude')
  or ((changes ? 'latitude') and ((changes->'latitude'='null'::jsonb)<>(changes->'longitude'='null'::jsonb)))
  or ((changes ? 'address' or changes ? 'postcode') and not(changes ? 'latitude')) then raise exception 'Location corrections require an explicit coordinate pair or clearing both'; end if;
 return p_patch;
end $$;

create or replace function public.dadspace_review_apply_v2(p_actor uuid,p_request uuid,p_action text,p_record uuid,p_target uuid,p_expected text,p_reason text,p_patch jsonb default '{}'::jsonb)
returns uuid language plpgsql security invoker set search_path=pg_catalog,public set lock_timeout='3s' set statement_timeout='10s' as $$
declare plan jsonb; before_data jsonb; after_data jsonb; aid uuid:=gen_random_uuid(); existing public.operations_review_audit%rowtype;
 original public.operations_review_audit%rowtype; row_data jsonb; old_fields jsonb:='{}'::jsonb; new_fields jsonb:='{}'::jsonb; changes jsonb;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 if p_actor is null or p_request is null or length(btrim(coalesce(p_reason,''))) not between 10 and 1000 then raise exception 'Actor, request and review reason required'; end if;
 -- Short, bounded review transactions serialize against imports. Readers remain free.
 lock table public.venues,public.collected_events,public.venue_sources,public.operations_review_audit in share row exclusive mode;
 select * into existing from public.operations_review_audit where request_id=p_request;
 if found then
  if existing.actor_id=p_actor and existing.action=p_action and existing.record_id=p_record
    and existing.target_id is not distinct from p_target and existing.reason=p_reason and existing.requested_patch=p_patch then return existing.id; end if;
  raise exception 'Request identity already used';
 end if;
 plan:=public.dadspace_review_plan_v2(p_action,p_record,p_target,p_patch);
 if plan->>'fingerprint' is distinct from p_expected then raise exception 'Preview is stale; review again'; end if;
 perform set_config('dadspace.review_write','on',true);
 if p_action='rollback' then
  select * into original from public.operations_review_audit where id=p_record for update;
  before_data:=original.after_state;
  old_fields:=original.after_fields;
  if original.action='edit' then
   update public.venues set venue_name=original.before_fields->>'venue_name',category=original.before_fields->>'category',address=original.before_fields->>'address',postcode=original.before_fields->>'postcode',latitude=(original.before_fields->>'latitude')::double precision,longitude=(original.before_fields->>'longitude')::double precision,website=original.before_fields->>'website',access=original.before_fields->>'access',opening_hours=case when original.before_fields ? 'opening_hours' then original.before_fields->>'opening_hours' else opening_hours end,fee=case when original.before_fields ? 'fee' then original.before_fields->>'fee' else fee end where id=original.record_id;
   new_fields:=original.before_fields;
  end if;
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
  if p_action in ('approve','hide','reject') then
   update public.venues set public_visible=p_action='approve',discovery_status=case p_action when 'approve' then 'verified' when 'reject' then 'rejected' else 'hidden' end,
    review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
  elsif p_action='edit' then
   changes:=p_patch->'changes';
   select jsonb_build_object('venue_name',venue_name,'category',category,'address',address,'postcode',postcode,'latitude',latitude,'longitude',longitude,'website',website,'access',access,'opening_hours',opening_hours,'fee',fee) into old_fields from public.venues where id=p_record;
   update public.venues v set
    venue_name=case when changes ? 'venue_name' then changes->>'venue_name' else v.venue_name end,
    category=case when changes ? 'category' then changes->>'category' else v.category end,
    address=case when changes ? 'address' then changes->>'address' else v.address end,
    postcode=case when changes ? 'postcode' then changes->>'postcode' else v.postcode end,
    latitude=case when changes ? 'latitude' then (changes->>'latitude')::double precision else v.latitude end,
    longitude=case when changes ? 'longitude' then (changes->>'longitude')::double precision else v.longitude end,
    website=case when changes ? 'website' then changes->>'website' else v.website end,
    access=case when changes ? 'access' then changes->>'access' else v.access end,
    opening_hours=case when changes ? 'opening_hours' then changes->>'opening_hours' else v.opening_hours end,
    fee=case when changes ? 'fee' then changes->>'fee' else v.fee end,
    review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
   select jsonb_build_object('venue_name',venue_name,'category',category,'address',address,'postcode',postcode,'latitude',latitude,'longitude',longitude,'website',website,'access',access,'opening_hours',opening_hours,'fee',fee) into new_fields from public.venues where id=p_record;
  elsif p_action='merge' then
   update public.venues set public_visible=false,discovery_status='merged',merged_into=p_target,review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
   update public.collected_events set venue_id=p_target,venue_reviewed_at=now() where venue_id=p_record;
   update public.venue_sources set venue_id=p_target where venue_id=p_record;
  else
   update public.collected_events set venue_id=p_target,venue_reviewed_at=now() where id=p_record;
  end if;
  after_data:=public.dadspace_review_snapshot(p_action,p_record,p_target);
 end if;
 insert into public.operations_review_audit(id,request_id,actor_id,action,record_id,target_id,reason,before_state,after_state,requested_patch,before_fields,after_fields)
 values(aid,p_request,p_actor,p_action,p_record,p_target,p_reason,before_data,after_data,p_patch,old_fields,new_fields);
 if p_action='rollback' then update public.operations_review_audit set reverted_by=aid where id=p_record; end if;
 perform set_config('dadspace.review_write','off',true);
 return aid;
end $$;

create or replace function public.dadspace_preserve_venue_review() returns trigger language plpgsql security invoker set search_path=pg_catalog,public as $$
begin
 if old.ops_reviewed_at is not null and coalesce(current_setting('dadspace.review_write',true),'off')<>'on' then
  new.public_visible:=old.public_visible; new.discovery_status:=old.discovery_status;
  new.review_reason:=old.review_reason; new.merged_into:=old.merged_into; new.ops_reviewed_at:=old.ops_reviewed_at;
  new.venue_name:=old.venue_name; new.address:=old.address; new.postcode:=old.postcode;
  new.latitude:=old.latitude; new.longitude:=old.longitude; new.website:=old.website;
  new.category:=old.category; new.access:=old.access;
  new.opening_hours:=old.opening_hours; new.fee:=old.fee;
 end if;
 return new;
end $$;
