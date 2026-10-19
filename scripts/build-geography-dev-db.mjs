import { PGlite } from '@electric-sql/pglite'
import fs from 'node:fs'
import path from 'node:path'

const directory=path.resolve('review/geography-dev-db')
fs.mkdirSync('review',{recursive:true})
const db=new PGlite(directory)
try {
  const exists=(await db.query("select to_regclass('public.geography_releases') as relation")).rows[0].relation
  if(!exists){
    await db.exec("do $$ begin create role anon; exception when duplicate_object then null; end $$; do $$ begin create role authenticated; exception when duplicate_object then null; end $$; do $$ begin create role service_role; exception when duplicate_object then null; end $$;")
    await db.exec(fs.readFileSync('supabase/migrations/20261018224639_uk_geography_reference.sql','utf8'))
  }
  await db.exec(fs.readFileSync('review/geography-seed.sql','utf8'))
  const summary=(await db.query(`select r.id,r.content_sha256,r.scope,
    (select count(*)::int from geography_areas a where a.release_id=r.id and a.kind='council') councils,
    (select count(*)::int from geography_postcodes p where p.release_id=r.id) postcodes
    from geography_releases r order by r.imported_at`)).rows
  fs.writeFileSync('review/geography-dev-db-status.json',JSON.stringify({engine:'PGlite / PostgreSQL-compatible local development database',directory,production_connected:false,releases:summary},null,2)+'\n')
  console.log(JSON.stringify(summary))
} finally {await db.close()}
