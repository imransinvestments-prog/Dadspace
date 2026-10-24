import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'

// The real migration, minus the Supabase extensions PGlite cannot load; small
// stand-ins record what pg_net, Vault and pg_cron would have been asked to do.
const migration = fs.readFileSync('supabase/migrations/20261022130000_scheduled_dispatch_timer.sql', 'utf8')
  .replace(/^create extension[^\n]*\n/gm, '')
const stubs = `
  create role anon; create role authenticated; create role service_role;
  create schema vault; create schema net; create schema cron;
  create table vault.decrypted_secrets(name text, decrypted_secret text);
  create table net.calls(id bigint generated always as identity primary key, url text, body jsonb, headers jsonb);
  create table net._http_response(id bigint, status_code integer, content text, error_msg text);
  create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds integer default 5000)
    returns bigint language sql as $$ insert into net.calls(url, body, headers) values (url, body, headers) returning id $$;
  create table cron.jobs(name text primary key, schedule text, command text);
  create function cron.schedule(job_name text, schedule text, command text) returns bigint language sql as
    $$ insert into cron.jobs values (job_name, schedule, command) on conflict (name) do update set schedule = excluded.schedule, command = excluded.command returning 1::bigint $$;`

async function database(token = 'github_pat_test') {
  const db = new PGlite()
  await db.exec(stubs)
  if (token) await db.query("insert into vault.decrypted_secrets values ('dadspace_github_dispatch', $1)", [token])
  await db.exec(migration)
  return db
}
const dispatch = async (db, at, workflow = 'daily-workers.yml', hours = [7, 19], inputs = {}) =>
  (await db.query('select public.dadspace_dispatch_slot($1, $2, $3, $4) as r', [workflow, hours, inputs, at])).rows[0].r

test('dispatches each London slot once, through both sides of the 25 October clock change', async () => {
  const db = await database()
  try {
    // BST: 07:17 London is 06:17 UTC; the 07:17 UTC call is 08:17 London and does nothing.
    assert.equal(await dispatch(db, '2026-10-22T06:17:00Z'), 'dispatched: 2026-10-22T07:17')
    assert.equal(await dispatch(db, '2026-10-22T07:17:00Z'), 'not a London slot: 2026-10-22T08:17')
    assert.equal(await dispatch(db, '2026-10-22T18:17:00Z'), 'dispatched: 2026-10-22T19:17')
    // GMT after 25 Oct: the UTC hour and the London hour agree again.
    assert.equal(await dispatch(db, '2026-10-26T06:17:00Z'), 'not a London slot: 2026-10-26T06:17')
    assert.equal(await dispatch(db, '2026-10-26T07:17:00Z'), 'dispatched: 2026-10-26T07:17')
    // A repeated cron call for the same slot never sends a second request.
    assert.equal(await dispatch(db, '2026-10-26T07:17:00Z'), 'already dispatched: 2026-10-26T07:17')
    const calls = (await db.query('select url, body, headers from net.calls order by id')).rows
    assert.equal(calls.length, 3)
    assert.equal(calls[0].url, 'https://api.github.com/repos/imransinvestments-prog/Dadspace/actions/workflows/daily-workers.yml/dispatches')
    assert.deepEqual(calls[0].body, { ref: 'main', inputs: { timer_slot: '2026-10-22T07:17' } })
    assert.equal(calls[0].headers.Authorization, 'Bearer github_pat_test')
    assert.equal(calls[0].headers['X-GitHub-Api-Version'], '2022-11-28')
    const rows = (await db.query('select slot, request_id from public.scheduled_dispatches order by id')).rows
    assert.deepEqual(rows.map(r => [r.slot, Number(r.request_id)]), [['2026-10-22T07:17', 1], ['2026-10-22T19:17', 2], ['2026-10-26T07:17', 3]])
  } finally { await db.close() }
})

test('Originals publishes explicitly at 07:17 and 09:17, and GitHub\'s answer is kept after pg_net forgets it', async () => {
  const db = await database()
  try {
    const originals = (at) => dispatch(db, at, 'original-content.yml', [7, 9], { dry_run: 'false', cadence: 'all' })
    assert.equal(await originals('2026-10-22T06:17:00Z'), 'dispatched: 2026-10-22T07:17')
    assert.equal(await originals('2026-10-22T07:17:00Z'), 'not a London slot: 2026-10-22T08:17')
    assert.equal(await originals('2026-10-22T08:17:00Z'), 'dispatched: 2026-10-22T09:17')
    assert.deepEqual((await db.query('select body from net.calls where id = 1')).rows[0].body,
      { ref: 'main', inputs: { dry_run: 'false', cadence: 'all', timer_slot: '2026-10-22T07:17' } })
    await db.exec("insert into net._http_response values (1, 204, '', null), (2, 422, '{\"message\":\"Unexpected inputs provided\"}', null)")
    assert.equal((await db.query('select public.dadspace_record_dispatch_status() as n')).rows[0].n, 2)
    const rows = (await db.query('select slot, status_code, error from public.scheduled_dispatches order by id')).rows
    assert.deepEqual(rows.map(r => [r.slot, r.status_code, r.error]),
      [['2026-10-22T07:17', 204, null], ['2026-10-22T09:17', 422, '{"message":"Unexpected inputs provided"}']])
    assert.equal((await db.query('select public.dadspace_record_dispatch_status() as n')).rows[0].n, 0, 'recorded once')
  } finally { await db.close() }
})

test('without the Vault token nothing is sent and the slot records why', async () => {
  const db = await database(null)
  try {
    assert.equal(await dispatch(db, '2026-10-22T06:17:00Z'), 'missing token: 2026-10-22T07:17')
    assert.equal((await db.query('select count(*)::int n from net.calls')).rows[0].n, 0)
    assert.equal((await db.query('select error from public.scheduled_dispatches')).rows[0].error, 'Vault secret dadspace_github_dispatch is missing')
  } finally { await db.close() }
})

test('the schedules are registered and only the owner can run the token-reading functions', async () => {
  const db = await database()
  try {
    const jobs = (await db.query('select name, schedule from cron.jobs order by name')).rows
    assert.deepEqual(jobs.map(j => [j.name, j.schedule]), [
      ['dadspace-dispatch-status', '*/10 * * * *'], ['dadspace-originals-timer', '17 6,7,8,9 * * *'], ['dadspace-workers-timer', '17 6,7,18,19 * * *']])
    for (const role of ['anon', 'authenticated', 'service_role']) {
      const r = (await db.query("select has_function_privilege($1, 'public.dadspace_dispatch_slot(text, integer[], jsonb, timestamptz)', 'execute') as ok", [role])).rows[0]
      assert.equal(r.ok, false, role)
    }
    // Re-running the migration replaces the schedules rather than adding duplicates.
    await db.exec(migration)
    assert.equal((await db.query('select count(*)::int n from cron.jobs')).rows[0].n, 3)
  } finally { await db.close() }
})

test('the council discovery timer dispatches a council-only batch every 15 minutes until no council is due', async () => {
  const db = await database()
  try {
    await db.exec(`
      create table public.geography_releases(id text primary key, imported_at timestamptz);
      create table public.geography_areas(code text, name text, kind text, release_id text);
      create table public.venue_council_discovery_runs(council_code text, status text, ran_at timestamptz default now());
      insert into public.geography_releases values ('old', '2026-01-01'), ('new', '2026-10-18');
      insert into public.geography_areas values ('E06000001', 'Hartlepool', 'council', 'new'),
        ('N09000003', 'Belfast', 'council', 'new'), ('E99999999', 'Old area', 'council', 'old');`)
    await db.exec(fs.readFileSync('supabase/migrations/20261024120000_council_discovery_timer.sql', 'utf8'))
    const job = (await db.query("select schedule, command from cron.jobs where name = 'dadspace-council-discovery-timer'")).rows[0]
    assert.equal(job.schedule, '*/15 * * * *')
    // pg_cron runs the command at now(); any quarter hour is a slot.
    await db.exec(job.command)
    const call = (await db.query('select url, body from net.calls')).rows[0]
    assert.match(call.url, /workflows\/venue-reference\.yml\/dispatches$/)
    assert.equal(call.body.inputs.dry_run, 'false')
    assert.equal(call.body.inputs.council_discovery_only, 'true')
    // Northern Ireland and older releases never keep it running; a failed run does not count as done.
    await db.exec("insert into public.venue_council_discovery_runs (council_code, status) values ('E06000001', 'failed')")
    assert.equal((await db.query('select public.dadspace_council_discovery_pending() as p')).rows[0].p, true)
    await db.exec("insert into public.venue_council_discovery_runs (council_code, status) values ('E06000001', 'ok')")
    assert.equal((await db.query('select public.dadspace_council_discovery_pending() as p')).rows[0].p, false)
    await db.exec('delete from public.scheduled_dispatches')
    await db.exec(job.command)
    assert.equal((await db.query('select count(*)::int n from net.calls')).rows[0].n, 1)
  } finally { await db.close() }
})
