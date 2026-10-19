import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
import { PGlite } from '@electric-sql/pglite'

const schema=fs.readFileSync('supabase/migrations/20261018224639_uk_geography_reference.sql','utf8')
const inverse=fs.readFileSync('scripts/rollback-geography-empty.sql','utf8')
const reference=JSON.parse(fs.readFileSync('geography/reference.json','utf8'))
function seed(ref=reference){
  return execFileSync(process.env.PYTHON||'python',['-c',
    'import sys,json;sys.path.insert(0,"scripts");from geography_catalogue import emit_seed;emit_seed(json.load(sys.stdin),sys.stdout)'],
    {input:JSON.stringify(ref),encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'},maxBuffer:3_000_000})
}
async function database(){const db=new PGlite();await db.exec('create role anon;create role authenticated;create role service_role;');await db.exec(schema);return db}

test('real schema imports repeatably, preserves prior releases and forbids unreviewed edits',async()=>{
  const db=await database()
  try {
    const sql=seed();await db.exec(sql);await db.exec(sql)
    assert.equal((await db.query('select count(*)::int n from geography_postcodes')).rows[0].n,28)
    assert.equal((await db.query("select count(*)::int n from geography_areas where kind='council'")).rows[0].n,361)
    const changed=structuredClone(reference);changed.postcodes[0].latitude+=.001
    await assert.rejects(db.exec(seed(changed)),/Release content changed/);await db.exec('rollback')
    await assert.rejects(db.exec("update geography_areas set name='Changed'"),/immutable/)
    await assert.rejects(db.exec("insert into geography_areas values('"+reference.release_id+"','extra','Unreviewed','council')"),/creation transaction/)
    const newer=structuredClone(reference);newer.release_id='test-new-reference';newer.postcodes[0].terminated='202610'
    await db.exec(seed(newer))
    assert.equal((await db.query('select count(*)::int n from geography_releases')).rows[0].n,2)
    assert.equal((await db.query('select count(*)::int n from geography_postcodes where terminated is not null')).rows[0].n,1)
    await assert.rejects(db.exec(inverse),/Cannot discard/);await db.exec('rollback')
    assert.equal((await db.query('select count(*)::int n from geography_postcodes')).rows[0].n,56)
  } finally {await db.close()}
})

test('public roles cannot read reference data and service role cannot import or update',async()=>{
  const db=await database()
  try{
    await db.exec(seed())
    for(const role of ['anon','authenticated']){
      await db.exec('set role '+role)
      await assert.rejects(db.query('select * from geography_postcodes'),/permission denied/)
      await db.exec('reset role')
    }
    await db.exec('set role service_role')
    assert.equal((await db.query('select count(*)::int n from geography_postcodes')).rows[0].n,28)
    await assert.rejects(db.exec("delete from geography_postcodes"),/permission denied/)
    await assert.rejects(db.exec("insert into geography_releases(id) values('invalid')"),/permission denied/)
  } finally {await db.close()}
})

test('invalid graph and postcode mapping fail atomically; empty inverse is reversible',async()=>{
  const db=await database()
  try{
    const sql=seed()
    // Exercise SQL guards independently of the Python validator.
    const broken=sql.replace("'administrative' where", "'postal' where")
    await assert.rejects(db.exec(broken),/Invalid geography relationship/);await db.exec('rollback')
    assert.equal((await db.query('select count(*)::int n from geography_releases')).rows[0].n,0)
    const mismatched=sql.replace(/('W3 9LN'.*?)'E92000001'/,"$1'S92000003'")
    assert.notEqual(mismatched,sql)
    await assert.rejects(db.exec(mismatched),/nation disagrees/);await db.exec('rollback')
    await db.exec(inverse)
    assert.equal((await db.query("select to_regclass('public.geography_releases') relation")).rows[0].relation,null)
    await db.exec(schema);await db.exec(sql)
  } finally {await db.close()}
})
