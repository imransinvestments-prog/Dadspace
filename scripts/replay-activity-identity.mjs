import fs from 'node:fs'
import { pathToFileURL } from 'node:url'
import { PGlite } from '@electric-sql/pglite'

export async function replayIdentity() {
  const db = new PGlite()
  try {
    await db.exec(`create table collected_events(
      id uuid primary key default gen_random_uuid(), dedupe_key text unique,
      identity_key text unique, content_hash text, title text, description text,
      start_date date, end_date date, time_text text, location text, event_url text,
      cost_text text, age_range text, recurrence text, listing_type text,
      schedule_text text, category text, venue_name text, venue_address text,
      postcode text, venue_id uuid, withdrawn_at timestamptz);`)
    await db.exec(fs.readFileSync('supabase/migrations/20261002_stable_event_identity_trigger.sql', 'utf8'))
    const withdrawal = fs.readFileSync('supabase/migrations/20261012121658_ds10_reversible_listing_withdrawal.sql','utf8')
    await db.exec(withdrawal.slice(withdrawal.indexOf('CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()')))
    const recorded = JSON.parse(fs.readFileSync('tests/fixtures/activity-repeat-cardiff.json','utf8'))
    const baseline = recorded[1].find(row => row.listing_type === 'activity')
    const write = async (row, key) => db.query(`insert into collected_events
      (dedupe_key,title,listing_type,venue_name,location,event_url,start_date,schedule_text)
      values($1,$2,$3,$4,$5,$6,$7,$8) on conflict(dedupe_key) do update set
      title=excluded.title,venue_name=excluded.venue_name,location=excluded.location,
      event_url=excluded.event_url,schedule_text=excluded.schedule_text
      returning id,identity_key,content_hash`, [key,row.title,row.listing_type,row.venue_name,
        row.location,row.event_url,row.start_date,row.schedule_text ?? null])
    const reset = () => db.exec('truncate collected_events')
    const count = async () => (await db.query('select count(*)::int n from collected_events')).rows[0].n
    const cases = []
    await reset()
    const first = (await write(baseline,'original')).rows[0]
    const repeated = (await write(baseline,'original')).rows[0]
    cases.push({case:'repeat_import',rows:await count(),same_id:first.id===repeated.id,
      same_identity:first.identity_key===repeated.identity_key,same_content:first.content_hash===repeated.content_hash})
    const revised = (await write({...baseline,schedule_text:'Every Monday at 10am'},'original')).rows[0]
    cases.push({case:'changed_schedule',rows:await count(),same_id:first.id===revised.id,
      same_identity:first.identity_key===revised.identity_key,content_changed:first.content_hash!==revised.content_hash})
    await write({...baseline,title:baseline.title+' for families'},'renamed')
    cases.push({case:'renamed_programme_same_url',rows:await count(),finding:'title-based identity creates a second row; requires reviewed continuity evidence'})
    await reset()
    await write(baseline,'original')
    await write({...baseline,venue_name:'Different Library',location:'Different Library'},'moved')
    cases.push({case:'moved_programme',rows:await count(),finding:'distinct venue preserved; old row is not retired automatically'})
    await reset()
    await write({...baseline,schedule_text:'Every Monday at 10am'},'session-a')
    await write({...baseline,event_url:baseline.event_url+'?session=b',schedule_text:'Every Tuesday at 2pm'},'session-b')
    cases.push({case:'distinct_same_title_same_venue_sessions',rows:await count(),
      finding:'current identity merges distinct session candidates; no production repair performed'})
    await reset()
    await write(baseline,'original')
    await write({...baseline,title:'A different programme'},'different')
    cases.push({case:'distinct_named_programmes_same_venue',rows:await count()})
    return {fixture:'tests/fixtures/activity-repeat-cardiff.json',source_url:baseline.source_url,
      baseline,method:'Real repository SQL functions and trigger in isolated PostgreSQL-compatible PGlite; mutations are synthetic scenarios, not claims about source changes',cases}
  } finally { await db.close() }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const result = await replayIdentity()
  const output = process.argv[2]
  if(output) fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n')
  console.log(JSON.stringify(result,null,2))
}
