"""Build a guarded, reversible SQL batch from an evidence-reviewed cleanup plan."""
import json
import re
import uuid
from urllib.parse import urlsplit

ALLOWED={'start_date','end_date','schedule_text','time_text','listing_type','recurrence','withdrawn_at','withdrawal_reason','superseded_by','date_backfill_reviewed_at','date_backfill_review_note','event_url','location','postcode','venue_name','age_range'}

def validate_plan(plan):
    seen=set()
    for item in plan['changes']:
        uuid.UUID(item['id'])
        if item['id'] in seen:raise ValueError('Duplicate plan ID')
        seen.add(item['id'])
        if not re.fullmatch('[0-9a-f]{32}',item['expected_fingerprint']):raise ValueError('Missing row fingerprint')
        patch=item['patch']
        if not patch or set(patch)-ALLOWED:raise ValueError('Unsupported cleanup field')
        if patch.get('event_url'):
            url=urlsplit(patch['event_url'])
            if url.scheme!='https' or not url.hostname or url.username or url.password or url.port not in (None,443):
                raise ValueError('Invalid reviewed public URL')
        if patch.get('superseded_by'):
            uuid.UUID(patch['superseded_by'])
            if patch['superseded_by']==item['id']:raise ValueError('Cannot supersede itself')
        if patch.get('withdrawn_at') and not patch.get('withdrawal_reason'):raise ValueError('Withdrawal needs reason')
        if patch.get('listing_type') and patch['listing_type'] not in ('event','activity'):raise ValueError('Invalid classification')

def build_sql(plan,commit=False):
    validate_plan(plan)
    payload=json.dumps(plan['changes'],ensure_ascii=False)
    marker='$ds10_cleanup_plan$'
    if marker in payload:raise ValueError('Unsafe SQL delimiter in data')
    assignments=',\n'.join(f'{column}=CASE WHEN v_patch ? \'{column}\' THEN (jsonb_populate_record(c,v_patch)).{column} ELSE c.{column} END' for column in sorted(ALLOWED))
    action='commit' if commit else 'rollback'
    return f'''begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
lock table public.collected_events in share row exclusive mode;
do $ds10_cleanup$
declare
 v_item jsonb; v_patch jsonb; v_before jsonb; v_after jsonb; v_expected jsonb; v_key text;
begin
 for v_item in select value from jsonb_array_elements({marker}{payload}{marker}::jsonb) order by case when value->'patch' ? 'withdrawn_at' then 0 else 1 end loop
  select to_jsonb(c) into v_before from public.collected_events c where id=(v_item->>'id')::uuid for update;
  if v_before is null or md5(v_before::text)<>v_item->>'expected_fingerprint' then
   raise exception 'Concurrent change/missing row: %',v_item->>'id';
  end if;
  v_patch=v_item->'patch';
  update public.collected_events c set {assignments} where c.id=(v_item->>'id')::uuid;
  select to_jsonb(c) into v_after from public.collected_events c where id=(v_item->>'id')::uuid;
  v_expected=to_jsonb(jsonb_populate_record(null::public.collected_events,v_patch));
  for v_key in select jsonb_object_keys(v_patch) loop
   if v_after->v_key is distinct from v_expected->v_key then raise exception 'Patch verification failed: %, %',v_item->>'id',v_key;end if;
  end loop;
  foreach v_key in array array['last_seen_at','last_verified_at','first_seen_at','source_id','venue_id'] loop
   if v_after->v_key is distinct from v_before->v_key then raise exception 'Protected provenance changed';end if;
  end loop;
  if v_after->>'withdrawn_at' is not null and (exists(select 1 from public.current_activities where id=(v_item->>'id')::uuid) or exists(select 1 from public.upcoming_events where id=(v_item->>'id')::uuid)) then
   raise exception 'Withdrawn record remains in public feed';
  end if;
 end loop;
end;
$ds10_cleanup$;
{action};
select '{action}' as batch_result, {len(plan['changes'])} as reviewed_records;
'''
