-- Exact reviewed correction rollback; aborts if any target row has since changed.
-- Owner rollback approval required. Default is inspection/rollback, not commit.
begin;
set local lock_timeout='5s';
create temporary table places_undo on commit drop as
select s.id as audit_id,s.venue_id,s.source_payload from public.venue_sources s
where s.source_name in ('Dadspace reviewed geography','Dadspace reviewed classification')
and s.source_payload->>'ticket' in ('100','162');
do $$ begin
 perform 1 from public.venues v join places_undo u on u.venue_id=v.id order by v.id for update of v;
 if not exists(select 1 from places_undo) or exists(select 1 from places_undo u left join public.venues v on v.id=u.venue_id
    where v.id is null or md5(to_jsonb(v)::text)<>u.source_payload->>'after_fingerprint') then
   raise exception 'Rollback target missing or changed: inspect before recovery';
 end if;
end $$;
select set_config('dadspace.review_write','on',true);
update public.venues v set country=u.source_payload->'before_row'->>'country',
category=u.source_payload->'before_row'->>'category',
public_visible=(u.source_payload->'before_row'->>'public_visible')::boolean,
review_reason=u.source_payload->'before_row'->>'review_reason',
ops_reviewed_at=(u.source_payload->'before_row'->>'ops_reviewed_at')::timestamptz
from places_undo u where v.id=u.venue_id;
-- Retain the audit before-image. Mark acceptance false so the protection releases country.
update public.venue_sources s set source_payload=s.source_payload || jsonb_build_object('accepted',false,'rolled_back_at',now()),updated_at=now()
from places_undo u where s.id=u.audit_id;
rollback;
