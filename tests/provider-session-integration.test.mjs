import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'
import { migration,setup,source,legacySource,workerRows,enrolSQL,writeSQL } from '../scripts/provider-session-test-support.mjs'

test('actual worker payloads preserve session IDs, provenance and real review/rollback guards',async()=>{
 const db=new PGlite()
 try {
  await setup(db)
  const venue='30000000-0000-0000-0000-000000000003', legacy='40000000-0000-0000-0000-000000000004'
  await db.exec(`insert into venues(id,venue_name,postcode,source_url,public_visible) values('${venue}','Reviewed test library','W4 2AB','https://example.test/library',true);
   insert into collected_events(id,source_id,title,listing_type,venue_name,dedupe_key) values('${legacy}','${legacySource}','Existing reviewed programme','activity','Reviewed test library','legacy-key');`)
  const actor='50000000-0000-0000-0000-000000000005'
  const plan=(await db.query(`select dadspace_review_plan('link','${legacy}','${venue}') p`)).rows[0].p
  const audit=(await db.query(`select dadspace_review_apply('${actor}',gen_random_uuid(),'link','${legacy}','${venue}',$1,'Fixture source and place verified') id`,[plan.fingerprint])).rows[0].id
  const before=(await db.query(`select dadspace_review_snapshot('link','${legacy}','${venue}') s`)).rows[0].s
  await db.exec(fs.readFileSync(migration,'utf8'))
  assert.deepEqual((await db.query(`select dadspace_review_snapshot('link','${legacy}','${venue}') s`)).rows[0].s,before,'nullable additions preserve prior accepted fingerprints')
  const rollback=(await db.query(`select dadspace_review_plan('rollback','${audit}',null) p`)).rows[0].p
  await db.query(`select dadspace_review_apply('${actor}',gen_random_uuid(),'rollback','${audit}',null,$1,'Restore fixture original relationship')`,[rollback.fingerprint])
  assert.equal((await db.query(`select venue_id from collected_events where id='${legacy}'`)).rows[0].venue_id,null)
  assert.equal((await db.query(`select count(*)::int n from operations_review_audit`)).rows[0].n,2)
  await db.exec(enrolSQL)
  const rows=workerRows()
  await db.exec('set role service_role')
  const a=(await db.query(writeSQL(rows[0]))).rows[0]
  const b=(await db.query(writeSQL(rows[1]))).rows[0]
  assert.notEqual(a.id,b.id,'same title and venue, distinct series survive actual worker and database')
  const renamed=(await db.query(writeSQL({...rows[0],title:'Renamed regular family programme'}))).rows[0]
  assert.equal(renamed.id,a.id);assert.equal(renamed.identity_key,a.identity_key)
  assert.notEqual(renamed.content_hash,a.content_hash)
  const rewritten=(await db.query(writeSQL({...rows[0],dedupe_key:'different-explicit-session-key'}))).rows[0]
  assert.equal(rewritten.id,a.id);assert.equal(rewritten.dedupe_key,a.dedupe_key)
  const revised=structuredClone(rows[0])
  revised.provider_occurrences[1].id+=123450
  revised.provider_occurrences[1].url='https://ealing.events.mylibrary.digital/event?id='+revised.provider_occurrences[1].id
  const provenanceChange=(await db.query(writeSQL(revised))).rows[0]
  assert.equal(provenanceChange.id,a.id)
  assert.notEqual(provenanceChange.content_hash,rewritten.content_hash,'occurrence provenance changes are content changes')
  await assert.rejects(()=>db.query(writeSQL({...rows[1],dedupe_key:rows[0].dedupe_key})),/another identity/)
  const missing={...rows[0],dedupe_key:'missing-session'}
  delete missing.provider_namespace;delete missing.provider_session_id;delete missing.provider_occurrences
  await assert.rejects(()=>db.query(writeSQL(missing)),/explicit session/)
  await assert.rejects(()=>db.query(writeSQL({...rows[0],source_id:legacySource})),/Unqualified/)
  await assert.rejects(()=>db.query(`update collected_events set provider_session_id='319285' where id=$1`,[a.id]),/reassignment/)
  await assert.rejects(()=>db.query(`update collected_events set venue_name='Invented move' where id=$1`,[a.id]),/reviewed operation/)
  await assert.rejects(()=>db.query(`update collected_events set withdrawn_at=now() where id=$1`,[a.id]),/reviewed operation/)
  const link=(await db.query(`select dadspace_review_plan('link',$1,$2) p`,[a.id,venue])).rows[0].p
  const providerReview=(await db.query(`select dadspace_review_apply('${actor}',gen_random_uuid(),'link',$1,$2,$3,'Verified provider session and canonical venue') id`,[a.id,venue,link.fingerprint])).rows[0].id
  // The actual reviewed relationship guard protects the next import's null venue_id.
  await db.query(writeSQL({...rows[0],title:'Newer accepted source title'}))
  assert.equal((await db.query('select venue_id from collected_events where id=$1',[a.id])).rows[0].venue_id,venue)
  await assert.rejects(()=>db.query(`select dadspace_review_plan('rollback',$1,null)`,[providerReview]),/changed after decision/)
  const history=await db.query('select before_row,after_row from activity_identity_audit where listing_id=$1 order by created_at,id',[a.id])
  assert.ok(history.rows.length>=4)
  assert.ok(history.rows.every(r=>r.after_row.id===a.id && r.after_row.provider_occurrences.length===2))
  assert.equal((await db.query("select has_table_privilege('anon','activity_identity_audit','SELECT') allowed")).rows[0].allowed,false)
  assert.equal((await db.query("select has_table_privilege('service_role','activity_identity_audit','DELETE') allowed")).rows[0].allowed,false)
  await db.exec('reset role')
  await assert.rejects(()=>db.exec(fs.readFileSync('scripts/rollback-provider-session-identity.sql','utf8')),/Stale or nonempty/)
  await db.exec('rollback')
  assert.equal((await db.query('select count(*)::int n from collected_events where provider_session_id is not null')).rows[0].n,2)
 } finally {await db.close()}
})

test('empty-enrolment migration inverse restores original trigger and accepted review history',async()=>{
 const db=new PGlite()
 try {
  await setup(db)
  const before=(await db.query("select pg_get_functiondef('dadspace_set_event_identity()'::regprocedure) f")).rows[0].f
  await db.exec(fs.readFileSync(migration,'utf8'))
  await db.exec(fs.readFileSync('tests/operations-review-transactions.sql','utf8'))
  await db.exec(fs.readFileSync('tests/operations-review-edit-transactions.sql','utf8'))
  await db.exec(fs.readFileSync('scripts/rollback-provider-session-identity.sql','utf8'))
  assert.equal((await db.query("select pg_get_functiondef('dadspace_set_event_identity()'::regprocedure) f")).rows[0].f,before)
  assert.equal((await db.query("select to_regclass('activity_identity_sources') t")).rows[0].t,null)
  // Installer can be applied again after the verified empty inverse.
  await db.exec(fs.readFileSync(migration,'utf8'))
  assert.equal((await db.query('select count(*)::int n from activity_identity_sources')).rows[0].n,0)
 } finally {await db.close()}
})
