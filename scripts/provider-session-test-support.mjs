import fs from 'node:fs'
export const migration='supabase/migrations/20261018213916_reviewed_provider_session_identity.sql'
export const setupFiles=['tests/operations-review-fixture.sql','tests/provider-session-bootstrap.sql',
  'supabase/migrations/20261002_stable_event_identity_trigger.sql','scripts/operations-review.sql',
  'supabase/migrations/20261017102447_operations_review_edit_reject.sql']
export const source='10000000-0000-0000-0000-000000000001'
export const legacySource='20000000-0000-0000-0000-000000000002'
export const workerRows=()=>JSON.parse(fs.readFileSync('tests/fixtures/provider-session-worker-rows.json','utf8'))
export const enrolSQL=`insert into activity_identity_sources(source_id,namespace,session_ids,approved_reason)
 values('${source}','ealing.events.mylibrary.digital',array['264038','319285'],'Isolated fixture of the approved session policy');`
export function writeSQL(row) {
  const keys=Object.keys(row)
  if(keys.some(k=>!/^[a-z_]+$/.test(k))) throw Error('Invalid fixture column')
  const json=JSON.stringify(row).replaceAll("'","''")
  return `insert into collected_events(${keys.join(',')})
    select ${keys.join(',')} from jsonb_populate_record(null::collected_events,'${json}'::jsonb)
    on conflict(dedupe_key) do update set ${keys.map(k=>`${k}=excluded.${k}`).join(',')}
    returning id,identity_key,dedupe_key,content_hash,provider_session_id;`
}

export async function setup(db) {
  for(const path of setupFiles) await db.exec(fs.readFileSync(path,'utf8'))
  const raw=fs.readFileSync('supabase/migrations/20261012121658_ds10_reversible_listing_withdrawal.sql','utf8')
  await db.exec(raw.slice(raw.indexOf('CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()')))
  await db.exec(`insert into sources values('${source}','library_portal_sessions_v1'),('${legacySource}','library_portal');`)
}
