import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'
// Reuse the real shared transaction definitions without creating another API.
const schema = fs.readFileSync('scripts/news-maintenance.sql','utf8')
const functions = schema.slice(schema.indexOf('create function public.dadspace_maintenance_snapshot'),schema.indexOf('create function public.dadspace_maintenance_claim'))
test('Deals pause is audited/idempotent, stale previews fail and restore preserves newer collector facts', async () => {
  const db = new PGlite()
  try {
    await db.exec(`create table news_items(id bigint, ops_hidden boolean);create table original_posts(slug text, ops_hidden boolean);
      create table news_sources(id bigint,active boolean);create table sources(id uuid,active boolean);
      create table deal_sources(id bigint primary key,name text,active boolean,last_checked_at text);
      create table operations_maintenance_audit(id uuid primary key, actor_id uuid, action text,family text,record_id text,reason text,before_state jsonb,after_state jsonb,status text,reverted_by uuid);
      insert into deal_sources values(34,'Halfords',true,'original check');`)
    await db.exec(functions)
    const actor='11111111-1111-4111-8111-111111111111', request='22222222-2222-4222-8222-222222222222', restore='33333333-3333-4333-8333-333333333333'
    const plan=async(action,record)=>(await db.query('select dadspace_maintenance_plan($1,$2,$3) p',[action,'deals-source',record])).rows[0].p
    const apply=(action,record,fingerprint,id)=>db.query('select dadspace_maintenance_apply($1,$2,$3,$4,$5,$6,$7)',[actor,id,action,'deals-source',record,fingerprint,'Owner reviewed exact source decision'])
    const stale=await plan('pause','34')
    await db.exec("update deal_sources set last_checked_at='new collector check'")
    await assert.rejects(apply('pause','34',stale.fingerprint,request),/stale/i)
    assert.equal((await db.query('select active from deal_sources')).rows[0].active,true)
    const fresh=await plan('pause','34')
    await apply('pause','34',fresh.fingerprint,request)
    await apply('pause','34',fresh.fingerprint,request)
    assert.equal((await db.query('select count(*)::int n from operations_maintenance_audit')).rows[0].n,1)
    assert.equal((await db.query('select active from deal_sources')).rows[0].active,false)
    const undo=await plan('restore',request)
    await apply('restore',request,undo.fingerprint,restore)
    assert.equal((await db.query('select active from deal_sources')).rows[0].active,true)
    const again=await plan('pause','34'), next='44444444-4444-4444-8444-444444444444'
    await apply('pause','34',again.fingerprint,next)
    await db.exec("update deal_sources set last_checked_at='later collector check'")
    await assert.rejects(plan('restore',next),/newer evidence/i)
  } finally {await db.close()}
})
