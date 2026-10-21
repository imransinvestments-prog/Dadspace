import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'

test('real source freshness trigger does not renew unseen rows on revalidated or failed snapshots',async()=>{
  const db=new PGlite()
  try {
    await db.exec(`create role anon;create role authenticated;
      create table sources(id text primary key,last_checked_at timestamptz,last_hash text,
        last_success_at timestamptz,last_error text,fail_count int);
      create table collected_events(id text primary key,source_id text,listing_type text,last_seen_at timestamptz);
      insert into sources values('source','2026-10-10','same','2026-10-10',null,0);
      insert into collected_events values('covered','source','activity','2026-10-10'),('unseen','source','activity','2026-10-10');`)
    await db.exec(fs.readFileSync('supabase/migrations/20261001221249_activity_last_seen_refresh.sql','utf8'))
    await db.exec(fs.readFileSync('supabase/migrations/20261008202338_activity_freshness_only_after_unchanged_success.sql','utf8'))
    // The MyLibrary adapter emits ok and new last_success, even for equal hashes.
    await db.exec(`update collected_events set last_seen_at='2026-10-11' where id='covered';
      update sources set last_checked_at='2026-10-11',last_success_at='2026-10-11' where id='source';`)
    let rows=(await db.query('select id,last_seen_at::text seen from collected_events order by id')).rows
    assert.match(rows[0].seen,/2026-10-11/)
    assert.match(rows[1].seen,/2026-10-10/)
    await db.exec(`update sources set last_checked_at='2026-10-12',last_error='incomplete snapshot',fail_count=1 where id='source';`)
    rows=(await db.query('select id,last_seen_at::text seen from collected_events order by id')).rows
    assert.match(rows[0].seen,/2026-10-11/)
    assert.match(rows[1].seen,/2026-10-10/)
    assert.equal((await db.query('select count(*)::int n from collected_events')).rows[0].n,2)
  } finally {await db.close()}
})
