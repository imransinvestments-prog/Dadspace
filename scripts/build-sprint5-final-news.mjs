// Approved final three mappings; generate forward/inverse rehearsals, never connect.
import fs from 'node:fs'
const {rows}=JSON.parse(fs.readFileSync('artefacts/data/sprint5-final-news-proposals.json','utf8'))
const quote=v=>`'${String(v).replaceAll("'","''")}'`
for(const direction of ['forward','rollback']){
  const statements=rows.map(row=>{
    const expected={...(direction==='forward'?row.before:row.proposed)}
    const after=direction==='forward'?row.proposed:row.before
    const published=expected.published_at;delete expected.published_at
    const setters=['region','geo_scope','geo_region','admin_area','locality'].map(k=>`${k}=${after[k]===null?'null':quote(after[k])}`).join(', ')
    return `DO $review$ BEGIN\n PERFORM 1 FROM public.news_items n WHERE id=${Number(row.id)} AND to_jsonb(n) @> ${quote(JSON.stringify(expected))}::jsonb AND published_at IS NOT DISTINCT FROM ${quote(published)}::timestamptz FOR UPDATE;\n IF NOT FOUND THEN RAISE EXCEPTION 'Stale final News row ${row.id}; abort whole batch'; END IF;\n UPDATE public.news_items SET ${setters} WHERE id=${Number(row.id)};\nEND $review$;`
  })
  fs.writeFileSync(`artefacts/data/sprint5-final-news-${direction}-rehearsal.sql`,'-- Exact three-row '+direction+' rehearsal. Application requires approved code deployed first.\nBEGIN;\n'+statements.join('\n')+'\nSELECT id,region,geo_scope,geo_region,admin_area,locality FROM public.news_items WHERE id IN (736,739,855) ORDER BY id;\nROLLBACK;\n')
}
