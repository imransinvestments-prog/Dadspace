-- Sprint 6 additive schema and service-only transaction API. Rehearse before release.
-- This script does not change publication or source activation for any existing row.
begin;
create temporary table sprint6_feed_before on commit drop as
 select md5(coalesce(jsonb_agg(id order by id)::text,'[]')) as fingerprint from public.feed_items;
alter table public.news_items add column if not exists ops_hidden boolean not null default false;
alter table public.original_posts add column if not exists ops_hidden boolean not null default false;

create table public.original_content_attempts (
 id uuid primary key, run_id text, cadence text not null check(cadence in ('daily','weekly')),
 slot_date date not null, dry_run boolean not null, created_at timestamptz not null default now(),
 stage text not null check(stage in ('draft','validation_rejected','editor_rejected','approved','published','duplicate','failed','dry_run')),
 attempt integer not null check(attempt between 0 and 2),
 draft jsonb, detail text not null check(length(detail)<=1500),
 model_calls integer, input_tokens integer, output_tokens integer,
 check(draft is null or (jsonb_typeof(draft)='object' and octet_length(draft::text)<=60000))
);
alter table public.original_content_attempts enable row level security;
revoke all on public.original_content_attempts from public,anon,authenticated;
grant select,insert on public.original_content_attempts to service_role;
create index original_attempts_slot on public.original_content_attempts(slot_date desc,created_at desc);

create table public.operations_maintenance_audit (
 id uuid primary key, actor_id uuid not null, action text not null, family text not null,
 record_id text not null, reason text not null check(length(btrim(reason)) between 10 and 1000),
 created_at timestamptz not null default now(), before_state jsonb not null, after_state jsonb not null,
 status text not null check(status in ('applied','claimed','submitted','uncertain','reconciled')),
 run_id bigint, reverted_by uuid references public.operations_maintenance_audit(id)
);
alter table public.operations_maintenance_audit enable row level security;
revoke all on public.operations_maintenance_audit from public,anon,authenticated;
grant select,insert,update on public.operations_maintenance_audit to service_role;
create index maintenance_recent on public.operations_maintenance_audit(created_at desc);

create function public.dadspace_maintenance_snapshot(p_family text,p_record text)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare result jsonb;
begin
 if current_user not in ('postgres','service_role') then raise exception 'Maintenance denied'; end if;
 if p_family='news' then select to_jsonb(n) into result from public.news_items n where id::text=p_record;
 elsif p_family='originals' then select to_jsonb(n) into result from public.original_posts n where slug=p_record;
 elsif p_family='news-source' then select to_jsonb(n) into result from public.news_sources n where id::text=p_record;
 elsif p_family='deals-source' then select to_jsonb(n) into result from public.deal_sources n where id::text=p_record;
 elsif p_family='discovery-source' then select to_jsonb(n) into result from public.sources n where id::text=p_record;
 else raise exception 'Invalid maintenance family'; end if;
 if result is null then raise exception 'Record unavailable'; end if;
 return result;
end $$;

create function public.dadspace_maintenance_plan(p_action text,p_family text,p_record text)
returns jsonb language plpgsql security invoker set search_path=pg_catalog,public as $$
declare state jsonb; a public.operations_maintenance_audit%rowtype;
begin
 if current_user not in ('postgres','service_role') then raise exception 'Maintenance denied'; end if;
 if p_action='restore' then
  select * into a from public.operations_maintenance_audit where id::text=p_record and status='applied' and reverted_by is null and action in ('hide','pause','activate');
  if not found then raise exception 'Restore unavailable'; end if;
  if p_family is distinct from a.family then raise exception 'Wrong family'; end if;
  state:=public.dadspace_maintenance_snapshot(a.family,a.record_id);
  if state is distinct from a.after_state then raise exception 'Newer evidence blocks restore'; end if;
 elsif p_action in ('hide','pause','activate') then
  state:=public.dadspace_maintenance_snapshot(p_family,p_record);
  if p_action='hide' and (p_family not in ('news','originals') or (state->>'ops_hidden')::boolean) then raise exception 'Article already hidden or wrong family'; end if;
  if p_action in ('pause','activate') and (p_family not in ('news-source','deals-source','discovery-source') or (state->>'active')::boolean=(p_action='activate')) then raise exception 'Source already in requested state or wrong family'; end if;
 else raise exception 'Invalid maintenance action'; end if;
 return jsonb_build_object('fingerprint',md5(state::text),'title',coalesce(state->>'title',state->>'name'),'hidden',state->'ops_hidden','active',state->'active');
end $$;

create function public.dadspace_maintenance_apply(p_actor uuid,p_request uuid,p_action text,p_family text,p_record text,p_expected text,p_reason text)
returns uuid language plpgsql security invoker set search_path=pg_catalog,public set lock_timeout='3s' set statement_timeout='10s' as $$
declare before_data jsonb; after_data jsonb; plan jsonb; old public.operations_maintenance_audit%rowtype;
 target text:=p_record; family text:=p_family; desired boolean;
begin
 if current_user not in ('postgres','service_role') then raise exception 'Maintenance denied'; end if;
 if p_actor is null or p_request is null or length(btrim(coalesce(p_reason,''))) not between 10 and 1000 then raise exception 'Actor/request/reason required'; end if;
 -- This serializes maintenance against imports without cancelling a collector.
 lock table public.news_items,public.original_posts,public.news_sources,public.deal_sources,public.sources,public.operations_maintenance_audit in share row exclusive mode;
 select * into old from public.operations_maintenance_audit where id=p_request;
 if found then
  if old.actor_id=p_actor and old.action=p_action and old.family=p_family and old.record_id=p_record and old.reason=p_reason then return old.id; end if;
  raise exception 'Request reused with different intent';
 end if;
 plan:=public.dadspace_maintenance_plan(p_action,p_family,p_record);
 if plan->>'fingerprint' is distinct from p_expected then raise exception 'Preview stale'; end if;
 if p_action='restore' then
  select * into old from public.operations_maintenance_audit where id::text=p_record;
  target:=old.record_id;
  desired:=case when family in ('news','originals') then (old.before_state->>'ops_hidden')::boolean else (old.before_state->>'active')::boolean end;
 else desired:=p_action in ('hide','activate'); end if;
 before_data:=public.dadspace_maintenance_snapshot(family,target);
 if family='news' then update public.news_items set ops_hidden=desired where id::text=target;
 elsif family='originals' then update public.original_posts set ops_hidden=desired where slug=target;
 elsif family='news-source' then update public.news_sources set active=desired where id::text=target;
 elsif family='deals-source' then update public.deal_sources set active=desired where id::text=target;
 elsif family='discovery-source' then update public.sources set active=desired where id::text=target;
 end if;
 after_data:=public.dadspace_maintenance_snapshot(family,target);
 insert into public.operations_maintenance_audit(id,actor_id,action,family,record_id,reason,before_state,after_state,status)
 values(p_request,p_actor,p_action,p_family,p_record,p_reason,before_data,after_data,'applied');
 if p_action='restore' then update public.operations_maintenance_audit set reverted_by=p_request where id=old.id; end if;
 return p_request;
end $$;

-- Remote dispatch is an outbox claim, not a transaction pretending to span GitHub.
create function public.dadspace_maintenance_claim(p_actor uuid,p_request uuid,p_family text,p_record text,p_reason text,p_scope jsonb)
returns boolean language plpgsql security invoker set search_path=pg_catalog,public set lock_timeout='3s' as $$
begin
 if current_user not in ('postgres','service_role') or p_actor is null or p_request is null or p_family not in ('news','originals')
  or length(btrim(coalesce(p_reason,''))) not between 10 and 1000 or p_scope is null then raise exception 'Invalid dispatch'; end if;
 lock table public.operations_maintenance_audit in share row exclusive mode;
 if exists(select 1 from public.operations_maintenance_audit where id=p_request) then return false; end if;
 -- One outstanding dispatch per family, and a minimum ten-minute cooldown.
 if exists(select 1 from public.operations_maintenance_audit where action='retry' and family=p_family and
  (status in ('claimed','submitted','uncertain') or created_at>now()-interval '10 minutes')) then raise exception 'Dispatch pending or cooling down'; end if;
 insert into public.operations_maintenance_audit(id,actor_id,action,family,record_id,reason,before_state,after_state,status)
 values(p_request,p_actor,'retry',p_family,p_record,p_reason,p_scope,p_scope,'claimed');
 return true;
end $$;

revoke all on function public.dadspace_maintenance_snapshot(text,text),public.dadspace_maintenance_plan(text,text,text),public.dadspace_maintenance_apply(uuid,uuid,text,text,text,text,text),public.dadspace_maintenance_claim(uuid,uuid,text,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.dadspace_maintenance_snapshot(text,text),public.dadspace_maintenance_plan(text,text,text),public.dadspace_maintenance_apply(uuid,uuid,text,text,text,text,text),public.dadspace_maintenance_claim(uuid,uuid,text,text,text,jsonb) to service_role;

-- Preserve the existing public feed contract; hide is enforced in the database.
-- No row is hidden by installation: both new columns default to false.
create or replace view public.feed_items as
 select id,title,url,source_name,published_at,summary,why_it_matters,category,relevance,region,geo_scope,geo_region,admin_area,locality
 from public.news_items
 where not ops_hidden and relevance>=3 and coalesce(is_primary,true)
 and coalesce(published_at,created_at)>now()-interval '14 days'
 order by coalesce(published_at,created_at) desc;
alter policy original_posts_public_read on public.original_posts using (published_at<=now() and not ops_hidden);
do $$ begin
 if (select fingerprint from sprint6_feed_before) is distinct from
  (select md5(coalesce(jsonb_agg(id order by id)::text,'[]')) from public.feed_items) then
  raise exception 'Installation changed public News membership; entire setup aborted';
 end if;
 if exists(select 1 from public.news_items where ops_hidden) or exists(select 1 from public.original_posts where ops_hidden) then
  raise exception 'Installation must not hide existing content';
 end if;
end $$;
commit;
