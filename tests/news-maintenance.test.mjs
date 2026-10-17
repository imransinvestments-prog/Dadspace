import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'
const schema=fs.readFileSync('scripts/news-maintenance.sql','utf8')
const actor='11111111-1111-4111-8111-111111111111'
const request='22222222-2222-4222-8222-222222222222'
const restore='33333333-3333-4333-8333-333333333333'
async function setup(){
  const db=new PGlite()
  await db.exec(`create role anon;create role authenticated;create role service_role bypassrls;
    create table news_items(id bigint primary key,title text,url text,source_name text,published_at timestamptz default now(),summary text,why_it_matters text,category text,relevance int default 5,region text,geo_scope text,geo_region text,admin_area text,locality text,is_primary boolean,created_at timestamptz default now());insert into news_items(id,title,url) values(1,'Accepted story','https://example.com/news');
    create table original_posts(slug text primary key,title text,published_at timestamptz default now());insert into original_posts(slug,title) values('daily-2026-10-17','Accepted original');
    alter table original_posts enable row level security;grant select on original_posts to anon,authenticated;
    create policy original_posts_public_read on original_posts for select to anon,authenticated using (published_at<=now());
    create table news_sources(id bigint primary key,name text,active boolean);insert into news_sources values(1,'Approved feed',true);
    create table deal_sources(id bigint primary key,name text,active boolean);
    create table sources(id bigint primary key,name text,active boolean);
    create view feed_items as select id,title,url,source_name,published_at,summary,why_it_matters,category,relevance,region,geo_scope,geo_region,admin_area,locality from news_items where relevance>=3 and coalesce(is_primary,true) and coalesce(published_at,created_at)>now()-interval '14 days';
    grant select,update on news_items,original_posts,news_sources,deal_sources,sources to service_role;`)
  await db.exec(schema)
  return db
}
const plan=(db,action='hide',family='news',id='1')=>db.query('select dadspace_maintenance_plan($1,$2,$3) as plan',[action,family,id]).then(r=>r.rows[0].plan)
const apply=(db,fingerprint,id=request,action='hide',record='1')=>db.query('select dadspace_maintenance_apply($1,$2,$3,$4,$5,$6,$7) as id',[actor,id,action,'news',record,fingerprint,'Owner reviewed exact action'])
test('additive schema preserves publication; hide/duplicate/restore are atomic and audited',async()=>{
  const db=await setup();try{
    assert.equal((await db.query('select ops_hidden from news_items')).rows[0].ops_hidden,false)
    const p=await plan(db);await apply(db,p.fingerprint)
    assert.equal((await db.query('select ops_hidden from news_items')).rows[0].ops_hidden,true)
    await apply(db,p.fingerprint)
    assert.equal((await db.query('select count(*)::int as n from operations_maintenance_audit')).rows[0].n,1)
    const undo=await plan(db,'restore','news',request);await apply(db,undo.fingerprint,restore,'restore',request)
    assert.equal((await db.query('select ops_hidden from news_items')).rows[0].ops_hidden,false)
    assert.equal((await db.query('select reverted_by from operations_maintenance_audit where id=$1',[request])).rows[0].reverted_by,restore)
    await assert.rejects(plan(db,'restore','news',request),/Restore unavailable/)
  }finally{await db.close()}
})
test('changed article blocks apply and newer evidence blocks restore without overwriting it',async()=>{
  const db=await setup();try{
    const p=await plan(db);await db.exec("update news_items set title='New fact'")
    await assert.rejects(apply(db,p.fingerprint),/Preview stale/)
    assert.equal((await db.query('select count(*)::int as n from operations_maintenance_audit')).rows[0].n,0)
    await apply(db,(await plan(db)).fingerprint)
    await db.exec("update news_items set title='Another newer fact'")
    await assert.rejects(plan(db,'restore','news',request),/Newer evidence/)
  }finally{await db.close()}
})
test('source pause and restore retain registry; malformed actions/roles cannot write',async()=>{
  const db=await setup();try{
    const p=await plan(db,'pause','news-source','1')
    await db.query('select dadspace_maintenance_apply($1,$2,$3,$4,$5,$6,$7)',[actor,request,'pause','news-source','1',p.fingerprint,'Reviewed pause evidence'])
    assert.equal((await db.query('select active from news_sources')).rows[0].active,false)
    for(const role of ['anon','authenticated']){
      await db.exec(`set role ${role}`)
      await assert.rejects(db.query('select * from original_content_attempts'),/permission denied/)
      await assert.rejects(db.query('select * from operations_maintenance_audit'),/permission denied/)
      await assert.rejects(plan(db),/permission denied/)
      await db.exec('reset role')
    }
    await assert.rejects(plan(db,'invented','news','1'),/Invalid maintenance action/)
    await assert.rejects(plan(db,'activate','news','1'),/wrong family/)
  }finally{await db.close()}
})
test('remote dispatch outbox consumes one request and blocks uncertain/concurrent requests',async()=>{
  const db=await setup();try{
    const claim=(id)=>db.query('select dadspace_maintenance_claim($1,$2,$3,$4,$5,$6) as claimed',[actor,id,'news','1','Approved bounded retry',{inputs:{source_id:'1',max_new:'10',max_minutes:'5'}}])
    assert.equal((await claim(request)).rows[0].claimed,true)
    assert.equal((await claim(request)).rows[0].claimed,false)
    await assert.rejects(claim(restore),/pending or cooling/)
    await db.exec("update operations_maintenance_audit set status='uncertain'")
    await assert.rejects(claim(restore),/pending or cooling/)
    await db.exec("update operations_maintenance_audit set status='reconciled',created_at=now()-interval '11 minutes'")
    assert.equal((await claim(restore)).rows[0].claimed,true)
  }finally{await db.close()}
})
test('unpublishing removes News from its public view and Originals from anon reads while keeping identity',async()=>{
  const db=await setup();try{
    await apply(db,(await plan(db)).fingerprint)
    assert.equal((await db.query('select count(*)::int as n from feed_items')).rows[0].n,0)
    const original=await plan(db,'hide','originals','daily-2026-10-17')
    await db.query('select dadspace_maintenance_apply($1,$2,$3,$4,$5,$6,$7)',[actor,restore,'hide','originals','daily-2026-10-17',original.fingerprint,'Reviewed Original unpublish'])
    await db.exec('set role anon')
    assert.equal((await db.query('select count(*)::int as n from original_posts')).rows[0].n,0)
    await db.exec('reset role')
    assert.equal((await db.query('select count(*)::int as n from original_posts')).rows[0].n,1)
  }finally{await db.close()}
})
