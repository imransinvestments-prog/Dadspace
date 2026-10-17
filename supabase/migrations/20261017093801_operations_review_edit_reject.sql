create or replace function public.dadspace_review_snapshot(p_action text,p_record uuid,p_target uuid)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare vids uuid[]; bulk boolean:=p_action='merge'; lid uuid; result jsonb;
begin
 if p_action='link' then vids:=array[p_target]; lid:=p_record;
 else vids:=array[p_record,p_target]; end if;
 if (bulk and (select count(*) from public.collected_events where venue_id=any(vids))>200)
   or (select count(*) from public.venue_sources where venue_id=any(vids))>200 then
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
  from public.venue_sources s where s.venue_id=any(vids)),'[]'::jsonb)) into result;
 return result;
end $$;


-- Incremental v2 extension. The original review API/history stays available.
alter table public.operations_review_audit drop constraint operations_review_audit_action_check;
alter table public.operations_review_audit add constraint operations_review_audit_action_check check(action in ('approve','hide','reject','edit','merge','link','rollback'));
alter table public.operations_review_audit add column requested_patch jsonb not null default '{}'::jsonb;
alter table public.operations_review_audit add column before_fields jsonb not null default '{}'::jsonb;
alter table public.operations_review_audit add column after_fields jsonb not null default '{}'::jsonb;

create function public.dadspace_review_patch(p_patch jsonb) returns jsonb
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
  if k not in ('venue_name','category','address','postcode','latitude','longitude','website','access') then raise exception 'Unapproved edit field'; end if;
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
   limit_size:=case k when 'venue_name' then 200 when 'category' then 100 when 'address' then 500 when 'postcode' then 20 when 'website' then 2048 else 100 end;
   if length(str)>limit_size or (k in ('venue_name','category') and str is null) then raise exception 'Invalid reviewed fact'; end if;
   if k='website' and str is not null and str !~ '^https://[^/@[:space:]\\\\]+([/?#][^[:space:]\\\\]*)?$' then raise exception 'HTTPS website required'; end if;
  end if;
 end loop;
 if (changes ? 'latitude')<>(changes ? 'longitude')
  or ((changes ? 'latitude') and ((changes->'latitude'='null'::jsonb)<>(changes->'longitude'='null'::jsonb)))
  or ((changes ? 'address' or changes ? 'postcode') and not(changes ? 'latitude')) then raise exception 'Location corrections require an explicit coordinate pair or clearing both'; end if;
 return p_patch;
end $$;

create function public.dadspace_review_plan_v2(p_action text,p_record uuid,p_target uuid default null,p_patch jsonb default '{}'::jsonb)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare state jsonb; v public.venues%rowtype; t public.venues%rowtype; e public.collected_events%rowtype; prospective public.venues%rowtype;
 a public.operations_review_audit%rowtype;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 if p_action<>'edit' and (p_patch is null or p_patch<>'{}'::jsonb) then raise exception 'Unexpected edit payload'; end if;
 if p_action='rollback' then
  select * into a from public.operations_review_audit where id=p_record;
  if not found or a.action='rollback' or a.reverted_by is not null then raise exception 'Rollback unavailable'; end if;
  state:=public.dadspace_review_snapshot(a.action,a.record_id,a.target_id);
  if state is distinct from a.after_state then raise exception 'Records changed after decision; rollback blocked'; end if;
  return jsonb_build_object('fingerprint',md5(state::text),'action',p_action,'record',p_record,'target',null,
    'summary','Restore the previous reviewed fields and relationships; retain the original audit record.',
    'venues',state->'venues','listings',jsonb_array_length(state->'listings'),'provenance',jsonb_array_length(state->'provenance'));
 end if;
 if p_action is null or p_action not in ('approve','hide','reject','edit','merge','link') then raise exception 'Invalid review action'; end if;
 if p_action='edit' then perform public.dadspace_review_patch(p_patch); elsif p_patch is null or p_patch<>'{}'::jsonb then raise exception 'Unexpected edit payload'; end if;
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
 if p_action in ('approve','edit') then
  prospective:=v;
  if p_action='edit' then select * into prospective from jsonb_populate_record(v,p_patch->'changes'); end if;
  if p_action='approve' or prospective.public_visible then
   if (coalesce(prospective.category,'') ~* 'playground' and lower(btrim(coalesce(prospective.access,''))) in ('customers','private','no'))
     or (coalesce(prospective.category,'') ~* 'park' and lower(btrim(coalesce(prospective.access,''))) in ('private','no')) then
    raise exception 'Restricted playground or park cannot be public; hide before correcting restrictive facts';
   end if;
   if exists(select 1 from public.venue_sources s where s.venue_id=p_record and s.source_name='Dadspace reviewed classification' and s.source_payload->>'accepted'='true' and s.source_payload->>'public_visible'='false') then
    raise exception 'Existing classification hold requires separate visitor-suitability evidence review';
   end if;
  end if;
 end if;
 state:=public.dadspace_review_snapshot(p_action,p_record,p_target);
 return jsonb_build_object('fingerprint',md5(state::text),'action',p_action,'record',p_record,'target',p_target,
  'summary',case p_action when 'approve' then 'Publish this venue as verified. Listing classification and publication stay unchanged.'
    when 'hide' then 'Temporarily hide this venue. Retain its identity, listings and provenance.'
    when 'reject' then 'Reject this venue from public discovery. Retain its identity, listings and provenance.'
    when 'edit' then 'Correct only the selected evidenced facts. Publication, country and relationships stay unchanged.'
    when 'merge' then 'Hide the duplicate, retain its identity, and move listing/provenance relationships to the canonical venue.'
    else 'Link the unresolved listing to the chosen public venue. Preserve dates, schedule, classification and source evidence.' end,
  'venues',state->'venues','listings',jsonb_array_length(state->'listings'),'provenance',jsonb_array_length(state->'provenance'));
end $$;

create function public.dadspace_review_apply_v2(p_actor uuid,p_request uuid,p_action text,p_record uuid,p_target uuid,p_expected text,p_reason text,p_patch jsonb default '{}'::jsonb)
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
   update public.venues set venue_name=original.before_fields->>'venue_name',category=original.before_fields->>'category',address=original.before_fields->>'address',postcode=original.before_fields->>'postcode',latitude=(original.before_fields->>'latitude')::double precision,longitude=(original.before_fields->>'longitude')::double precision,website=original.before_fields->>'website',access=original.before_fields->>'access' where id=original.record_id;
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
   select jsonb_build_object('venue_name',venue_name,'category',category,'address',address,'postcode',postcode,'latitude',latitude,'longitude',longitude,'website',website,'access',access) into old_fields from public.venues where id=p_record;
   update public.venues v set
    venue_name=case when changes ? 'venue_name' then changes->>'venue_name' else v.venue_name end,
    category=case when changes ? 'category' then changes->>'category' else v.category end,
    address=case when changes ? 'address' then changes->>'address' else v.address end,
    postcode=case when changes ? 'postcode' then changes->>'postcode' else v.postcode end,
    latitude=case when changes ? 'latitude' then (changes->>'latitude')::double precision else v.latitude end,
    longitude=case when changes ? 'longitude' then (changes->>'longitude')::double precision else v.longitude end,
    website=case when changes ? 'website' then changes->>'website' else v.website end,
    access=case when changes ? 'access' then changes->>'access' else v.access end,
    review_reason=p_reason,ops_reviewed_at=now() where id=p_record;
   select jsonb_build_object('venue_name',venue_name,'category',category,'address',address,'postcode',postcode,'latitude',latitude,'longitude',longitude,'website',website,'access',access) into new_fields from public.venues where id=p_record;
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

create or replace function public.dadspace_review_plan(p_action text,p_record uuid,p_target uuid default null)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare state jsonb; v public.venues%rowtype; t public.venues%rowtype; e public.collected_events%rowtype;
 a public.operations_review_audit%rowtype;
begin
 if current_user not in ('service_role','postgres') then raise exception 'Review access denied'; end if;
 if p_action='rollback' then
  select * into a from public.operations_review_audit where id=p_record;
  if not found or a.action in ('rollback','edit','reject') or a.reverted_by is not null then raise exception 'Rollback unavailable'; end if;
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


-- Keep newer reviewed facts protected from every importer, without replacing the geography trigger.
create or replace function public.dadspace_preserve_venue_review() returns trigger language plpgsql security invoker set search_path=pg_catalog,public as $$
begin
 if old.ops_reviewed_at is not null and coalesce(current_setting('dadspace.review_write',true),'off')<>'on' then
  new.public_visible:=old.public_visible; new.discovery_status:=old.discovery_status;
  new.review_reason:=old.review_reason; new.merged_into:=old.merged_into; new.ops_reviewed_at:=old.ops_reviewed_at;
  new.venue_name:=old.venue_name; new.address:=old.address; new.postcode:=old.postcode;
  new.latitude:=old.latitude; new.longitude:=old.longitude; new.website:=old.website;
  new.category:=old.category; new.access:=old.access;
 end if;
 return new;
end $$;
revoke execute on function public.dadspace_review_patch(jsonb),public.dadspace_review_plan_v2(text,uuid,uuid,jsonb),public.dadspace_review_apply_v2(uuid,uuid,text,uuid,uuid,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.dadspace_review_patch(jsonb),public.dadspace_review_plan_v2(text,uuid,uuid,jsonb),public.dadspace_review_apply_v2(uuid,uuid,text,uuid,uuid,text,text,jsonb) to service_role;

