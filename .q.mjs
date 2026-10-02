import { createClient } from '@supabase/supabase-js'
import { writeFileSync } from 'fs'
const s = createClient(process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL, process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY)
let rows=[]; for (let from=0;;from+=1000){ const {data,error}=await s.from('venues').select('id,venue_label,address_line_1').ilike('venue_label','unnamed%playground%').not('address_line_1','is',null).order('id').range(from,from+999); if(error) throw error; rows.push(...data); if(data.length<1000) break }
writeFileSync('/tmp/unnamed_playgrounds_backup.json', JSON.stringify(rows))
const cap = (r) => r.replace(/(^|\s)([a-z])/g, (_, a, b) => a + b.toUpperCase())
const nameFor = (road) => { const r = /^[a-z]/.test(road) ? cap(road) : road; return /playground/i.test(r) ? r : `${r} Playground` }
let done=0, failed=[]; let i=0
async function worker(){ while(i<rows.length){ const r=rows[i++]; const {error}=await s.from('venues').update({venue_label:nameFor(r.address_line_1)}).eq('id',r.id); if(error) failed.push([r.id,error.message]); if(++done%5000===0) console.log('done',done) } }
await Promise.all(Array.from({length:25},worker))
console.log('updated', done-failed.length, 'failed', failed.length, failed.slice(0,5))
