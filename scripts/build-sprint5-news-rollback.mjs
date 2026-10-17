// Offline rollback rehearsal. Ends in ROLLBACK: does not undo production data.
import fs from 'node:fs'
const plan=JSON.parse(fs.readFileSync('artefacts/data/sprint5-news-corrections.json','utf8'))
const quote=v=>`'${String(v).replaceAll("'","''")}'`
const blocks=plan.rows.filter(r=>r.fields.changed).map(row=>{
  const expected={...row.fields.proposed};delete expected.published_at
  const setters=['region','geo_scope','geo_region','admin_area','locality'].map(k=>`${k}=${row.fields.before[k]===null?'null':quote(row.fields.before[k])}`).join(', ')
  return `DO $undo$ BEGIN\n PERFORM 1 FROM public.news_items n WHERE id=${Number(row.id)} AND to_jsonb(n) @> ${quote(JSON.stringify(expected))}::jsonb AND published_at IS NOT DISTINCT FROM ${quote(row.fields.proposed.published_at)}::timestamptz FOR UPDATE;\n IF NOT FOUND THEN RAISE EXCEPTION 'Rollback conflict for News ${row.id}; re-review newer changes'; END IF;\n UPDATE public.news_items SET ${setters} WHERE id=${Number(row.id)};\nEND $undo$;`
})
fs.writeFileSync('artefacts/data/sprint5-news-rollback-rehearsal.sql','-- Inverse of the 16 approved changes. Rehearsal only; never overwrites newer selected fields.\nBEGIN;\n'+blocks.join('\n')+'\nSELECT id,region,geo_scope,admin_area,locality FROM public.news_items WHERE id IN ('+plan.rows.filter(r=>r.fields.changed).map(r=>r.id).join(',')+') ORDER BY id;\nROLLBACK;\n')
