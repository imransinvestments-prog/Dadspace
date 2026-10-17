// Review/rehearsal SQL only: ends in ROLLBACK. No database connection.
import fs from 'node:fs'
const plan=JSON.parse(fs.readFileSync('artefacts/data/sprint5-news-corrections.json','utf8'))
const quote=value=>`'${String(value).replaceAll("'","''")}'`
const geo=['region','geo_scope','geo_region','admin_area','locality']
const statements=plan.rows.filter(row=>row.fields.changed).map(row=>{
  const {before,proposed}=row.fields
  // Timestamp readback formatting can differ; compare it as timestamptz below.
  const expected={...before};delete expected.published_at
  const matches=`id=${Number(row.id)} and to_jsonb(n) @> ${quote(JSON.stringify(expected))}::jsonb and published_at is not distinct from ${before.published_at?quote(before.published_at)+'::timestamptz':'null::timestamptz'}`
  const setters=geo.map(key=>`${key}=${proposed[key]===null?'null':quote(proposed[key])}`).join(', ')
  return `-- ${row.id}: ${row.title.replaceAll('\n',' ')}\nDO $review$ BEGIN\n  PERFORM 1 FROM public.news_items n WHERE ${matches} FOR UPDATE;\n  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row ${row.id}; entire batch must be re-reviewed'; END IF;\n  UPDATE public.news_items n SET ${setters} WHERE id=${Number(row.id)};\nEND $review$;`
})
const sql=`-- Proposed News correction rehearsal. NOT owner approval or a production apply script.\n-- Full batch fails on stale selected fields. Held/no-op rows are excluded.\nBEGIN;\n${statements.join('\n\n')}\nSELECT id,region,geo_scope,geo_region,admin_area,locality FROM public.news_items WHERE id IN (${plan.rows.filter(r=>r.fields.changed).map(r=>r.id).join(',')}) ORDER BY id;\nROLLBACK;\n`
fs.writeFileSync('artefacts/data/sprint5-news-correction-rehearsal.sql',sql)
console.log(`Prepared ${statements.length} proposed updates; rehearsal always rolls back.`)
