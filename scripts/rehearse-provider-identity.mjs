// Isolated proposal for #198. No Supabase client, credentials or production DDL.
import fs from 'node:fs'
import { pathToFileURL } from 'node:url'
import { PGlite } from '@electric-sql/pglite'

const basePath = 'supabase/migrations/20261002_stable_event_identity_trigger.sql'
const withdrawalPath = 'supabase/migrations/20261012121658_ds10_reversible_listing_withdrawal.sql'
const provider = 'ealing.events.mylibrary.digital'
const source = '10000000-0000-0000-0000-000000000001'

export async function rehearseProviderIdentity() {
  const db = new PGlite()
  try {
    await db.exec(`create table collected_events(
      id uuid primary key default gen_random_uuid(), source_id uuid,
      dedupe_key text unique, identity_key text unique, content_hash text,
      title text, description text, start_date date, end_date date, time_text text,
      location text, event_url text, cost_text text, age_range text, recurrence text,
      listing_type text, schedule_text text, category text, venue_name text,
      venue_address text, postcode text, venue_id uuid, withdrawn_at timestamptz);
      create table retained_review_history(listing_id uuid, decision text);
      create table qualified_identity_sources(source_id uuid primary key, namespace text not null);
      create table identity_adoption_snapshot(id uuid primary key, before_row jsonb, after_row jsonb);`)
    await db.exec(fs.readFileSync(basePath, 'utf8'))
    const raw = fs.readFileSync(withdrawalPath, 'utf8').replaceAll('\r\n','\n')
    const legacy = raw.slice(raw.indexOf('CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()'))
    await db.exec(legacy)
    const fixtures = JSON.parse(fs.readFileSync('tests/fixtures/library-portal-records.json', 'utf8'))
    const first = fixtures.find(r => r.series_id === 319285)
    const write = async (r, key, sid = null, realm = null, sidSource = source) => db.query(`
      insert into collected_events(source_id,dedupe_key,title,listing_type,venue_name,
        location,event_url,schedule_text,provider_namespace,provider_session_id)
      values($1,$2,$3,'activity',$4,$4,$5,$6,$7,$8)
      on conflict(dedupe_key) do update set title=excluded.title,
        schedule_text=excluded.schedule_text,event_url=excluded.event_url
      returning id,identity_key,content_hash`,
      [sidSource,key,r.name,r.location_name,r.url,r.recurring_dates_tagline || null,realm,sid])

    // Additive proposal only; use real migration tooling after review, never deploy this script.
    await db.exec(`alter table collected_events add provider_namespace text;
      alter table collected_events add provider_session_id text;`)
    const original = (await write(first,'legacy-key')).rows[0]
    await db.query('insert into retained_review_history values($1,$2)', [original.id,'Reviewed facts retained'])
    const before = (await db.query('select to_jsonb(c) row from collected_events c')).rows[0].row
    const assignment = `new.identity_key := public.dadspace_event_identity(
    new.listing_type, new.title, new.start_date, new.event_url,
    new.venue_id, new.postcode, new.venue_name, new.location
  );`
    if (!legacy.includes(assignment)) throw Error('Legacy trigger changed; inspect before adapting prototype')
    const proposed = legacy.replace(assignment, () => `
  if exists(select 1 from qualified_identity_sources q where q.source_id=new.source_id) then
    if new.listing_type <> 'activity' or new.listing_type is null
       or new.provider_namespace is null or new.provider_session_id is null
       or new.provider_session_id !~ '^[1-9][0-9]*$'
       or not exists(select 1 from qualified_identity_sources q
         where q.source_id=new.source_id and q.namespace=new.provider_namespace) then
      raise exception 'Qualified source requires explicit validated session identity';
    end if;
    if tg_op='UPDATE' and (old.source_id is distinct from new.source_id
      or (old.provider_session_id is not null and
        (old.provider_session_id is distinct from new.provider_session_id
         or old.provider_namespace is distinct from new.provider_namespace))
      or old.venue_id is distinct from new.venue_id
      or old.venue_name is distinct from new.venue_name
      or old.location is distinct from new.location
      or old.withdrawn_at is distinct from new.withdrawn_at) then
      raise exception 'Identity, place or retirement change requires a separate reviewed operation';
    end if;
    new.identity_key := md5('activity-session-v1|' || new.provider_namespace || '|' || new.provider_session_id);
    if exists(select 1 from collected_events c where c.dedupe_key=new.dedupe_key
      and c.identity_key is distinct from new.identity_key
      and (tg_op='INSERT' or c.id<>new.id)) then
      raise exception 'Dedupe key belongs to a different identity';
    end if;
  elsif new.provider_namespace is not null or new.provider_session_id is not null then
    raise exception 'Source is not qualified for provider identity';
  else
    ${assignment}
  end if;`)
    await db.exec(proposed)
    // Source gate must remain empty in production until a frozen mapping is approved.
    await db.query('insert into qualified_identity_sources values($1,$2)',[source,provider])
    // The prototype needs metadata/source changes to invoke the guard too.
    await db.exec(`drop trigger collected_events_set_identity on collected_events;
      create trigger collected_events_set_identity before insert or update on collected_events
      for each row execute function dadspace_set_event_identity();`)
    await db.query('insert into identity_adoption_snapshot(id,before_row) values($1,$2)',[original.id,before])
    const adopted = (await db.query(`update collected_events set provider_namespace=$1,
      provider_session_id='319285' where id=$2 returning id,identity_key`,[provider,original.id])).rows[0]
    await db.exec('update identity_adoption_snapshot s set after_row=to_jsonb(c) from collected_events c where c.id=s.id')
    const rollback = async () => {
      // Forward adoption may be inverted only before any retained row changes/additions.
      await db.exec(`do $$ begin
        if exists(select 1 from identity_adoption_snapshot s join collected_events c on c.id=s.id
                  where to_jsonb(c) is distinct from s.after_row)
          or exists(select 1 from identity_adoption_snapshot s left join collected_events c on c.id=s.id where c.id is null)
          or exists(select 1 from collected_events c where c.provider_namespace is not null
                    and not exists(select 1 from identity_adoption_snapshot s where s.id=c.id)) then
          raise exception 'Stale rollback: retain current rows and prepare a new reviewed inverse';
        end if;
      end $$;`)
      await db.exec('delete from qualified_identity_sources')
      await db.exec(legacy)
      await db.exec(`update collected_events c set provider_namespace=null,provider_session_id=null,
        identity_key=s.before_row->>'identity_key' from identity_adoption_snapshot s where s.id=c.id`)
    }
    await rollback()
    const restored = (await db.query('select to_jsonb(c) row from collected_events c')).rows[0].row
    const cases = [{case:'forward_inverse_exact_row',pass:JSON.stringify(before)===JSON.stringify(restored)},
      {case:'adoption_retains_listing_id',pass:adopted.id===original.id}]
    // Repeat adoption and exercise the actual ON CONFLICT(dedupe_key) collector contract.
    await db.exec(proposed)
    await db.query('insert into qualified_identity_sources values($1,$2)',[source,provider])
    await db.query(`update collected_events set provider_namespace=$1,provider_session_id='319285' where id=$2`,[provider,original.id])
    await db.exec('update identity_adoption_snapshot s set after_row=to_jsonb(c) from collected_events c where c.id=s.id')
    const renamed = (await write({...first,name:'Reviewed renamed programme'},'new-wording','319285',provider)).rows[0]
    cases.push({case:'rename_preserves_id_and_legacy_dedupe',pass:renamed.id===original.id &&
      (await db.query('select dedupe_key from collected_events where id=$1',[original.id])).rows[0].dedupe_key==='legacy-key'})
    cases.push({case:'content_changes_without_identity_change',pass:renamed.identity_key===adopted.identity_key && renamed.content_hash!==original.content_hash})
    const nextOccurrence = fixtures.find(r=>r.series_id===319285 && r.event_id!==first.event_id)
    const repeated = (await write(nextOccurrence,'next-occurrence','319285',provider)).rows[0]
    cases.push({case:'real_distinct_occurrences_one_session',pass:repeated.id===original.id})
    const other = (await write(first,'separate-session','264038',provider)).rows[0]
    cases.push({case:'synthetic_same_title_same_venue_distinct_sessions',pass:other.id!==original.id})
    const rejects = async (name, action) => {
      let rejected=false
      try { await action() } catch { rejected=true }
      cases.push({case:name,pass:rejected})
    }
    await rejects('qualified_source_missing_ids_rejected',()=>write(first,'unqualified'))
    await rejects('conflicting_dedupe_cannot_merge_sessions',()=>write(first,'legacy-key','999',provider))
    await rejects('unqualified_source_cannot_claim_namespace',()=>write(first,'wrong-source','319285',provider,'20000000-0000-0000-0000-000000000002'))
    await rejects('session_reassignment_rejected',()=>db.query("update collected_events set provider_session_id='123' where id=$1",[original.id]))
    await rejects('place_change_requires_review',()=>db.query("update collected_events set venue_name='Moved' where id=$1",[original.id]))
    await rejects('retirement_requires_review',()=>db.query('update collected_events set withdrawn_at=now() where id=$1',[original.id]))
    await rejects('changed_or_added_rows_block_inverse',rollback)
    cases.push({case:'retained_review_history',pass:(await db.query('select * from retained_review_history')).rows[0].listing_id===original.id})
    const legacySource='30000000-0000-0000-0000-000000000003'
    const old = (await write({...first,name:'Unaffected legacy'},'legacy-other',null,null,legacySource)).rows[0]
    const again = (await write({...first,name:'Unaffected legacy'},'legacy-other',null,null,legacySource)).rows[0]
    cases.push({case:'non_enrolled_collectors_unchanged',pass:old.id===again.id})
    return {production_writes:0,production_schema_changes:0,
      scope:'Local PGlite prototype; legacy repository trigger plus explicit opt-in guard. Not a deployable migration or concurrent-writer certification.',
      fixture:'tests/fixtures/library-portal-records.json',cases}
  } finally { await db.close() }
}

if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const report=await rehearseProviderIdentity()
  if(process.argv[2]) fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n')
  console.log(JSON.stringify(report,null,2))
  if(report.cases.some(c=>!c.pass)) process.exitCode=1
}
