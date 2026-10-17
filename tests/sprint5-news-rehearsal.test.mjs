import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {PGlite} from '@electric-sql/pglite'
const evidence=JSON.parse(fs.readFileSync('artefacts/data/sprint5-news-evidence.json','utf8'))
const rows=[...evidence.rows,...evidence.additional_negative_geography.rows]
const sql=fs.readFileSync('artefacts/data/sprint5-news-correction-rehearsal.sql','utf8')
async function database(){
  const db=new PGlite()
  const columns=Object.keys(rows[0]).map(k=>`${k} ${k==='id'?'bigint':k==='relevance'?'integer':k==='published_at'?'timestamptz':'text'}`)
  await db.exec(`create table public.news_items(${columns.join(',')})`)
  await db.query('insert into public.news_items select * from json_populate_recordset(null::public.news_items,$1::json)',[JSON.stringify(rows)])
  return db
}
test('all proposed News corrections rehearse on PostgreSQL and roll back, excluding held/no-op rows',async()=>{
  const db=await database()
  try{
    const before=await db.query('select * from news_items order by id')
    const results=await db.exec(sql)
    const readback=results.find(r=>r.rows?.length===16)
    assert.ok(readback,'16 changed rows read back inside rehearsal')
    assert.equal(readback.rows.find(r=>r.id===430).admin_area,'hampshire')
    assert.equal(readback.rows.find(r=>r.id===328).locality,'west_northamptonshire')
    assert.deepEqual(await db.query('select * from news_items order by id'),before)
  }finally{await db.close()}
})
test('a stale late-batch row aborts the entire correction batch without partial application',async()=>{
  const db=await database()
  try{
    await db.exec("update news_items set summary='Concurrent operator change' where id=877")
    const before=await db.query('select * from news_items order by id')
    await assert.rejects(db.exec(sql),/Stale\/missing News row 877/)
    await db.exec('rollback')
    assert.deepEqual(await db.query('select * from news_items order by id'),before)
  }finally{await db.close()}
})
