import assert from 'node:assert/strict'
import { mkdtemp, readFile, unlink, rmdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { runBackfill } from './backfill-venue-photos.mjs'
import { isPlayground } from '../lib/google-venue-match.mjs'
const directory=await mkdtemp(join(tmpdir(),'dadspace-photo-test-'))
const report=join(directory,'report.jsonl')
const uuid=n=>`00000000-0000-0000-0000-${String(n).padStart(12,'0')}`
function database(count) {
  const rows=Array.from({length:count},(_,i)=>({id:uuid(i+1),venue_name:'Jump Factory',postcode:'M1 1AA',latitude:53.48,longitude:-2.24,image_url:null}))
  const updates=[];let reads=0
  return {rows,updates,get reads(){return reads},from(table){
    assert.equal(table,'venues')
    let patch=null,after='',id=null,limit=500,guard=false
    const builder={
      select(){return builder},is(column,value){assert.equal(column,'image_url');assert.equal(value,null);guard=true;return builder},
      or(value){assert.ok(value.includes('category.not.ilike.%play%ground%'));return builder},
      order(column){assert.equal(column,'id');return builder},limit(value){limit=value;return builder},
      gt(column,value){assert.equal(column,'id');after=value;return builder},
      eq(column,value){assert.equal(column,'id');id=value;return builder},update(value){patch=value;return builder},
      then(resolve,reject){
        try {
          assert.ok(guard,'Reads and writes preserve existing photos')
          if (patch) {
            const row=rows.find(r=>r.id===id && r.image_url===null)
            if (row) {Object.assign(row,patch);updates.push(patch)}
            return Promise.resolve({data:row?[{id:row.id}]:[],error:null}).then(resolve,reject)
          }
          reads++;return Promise.resolve({data:rows.filter(r=>r.id>after && r.image_url===null && !isPlayground(r)).slice(0,limit),error:null}).then(resolve,reject)
        } catch(e){return Promise.reject(e).then(resolve,reject)}
      }
    };return builder
  }}
}
const fetcher=async()=>({ok:true,json:async()=>({places:[{id:'ChIJvalidPlaceId123',displayName:{text:'Jump Factory'},location:{latitude:53.4801,longitude:-2.24},addressComponents:[{types:['country'],shortText:'GB'},{types:['postal_code'],longText:'M1 1AA'}],photos:[{name:'temporary-photo-resource'}]}]})})
try {
 const db=database(501)
 const result=await runBackfill({db,apiKey:'test-key',limit:501,maxCalls:501,apply:true,report,fetcher,sleep:async()=>{}})
 assert.equal(result.updated,501);assert.equal(result.calls,501);assert.equal(db.reads,2)
 assert.ok(db.updates.every(p=>p.image_url==='google-places:ChIJvalidPlaceId123' && !JSON.stringify(p).includes('temporary-photo-resource')))
 const lines=(await readFile(report,'utf8')).trim().split('\n')
 assert.equal(lines.length,501);assert.equal(JSON.parse(lines[500]).venueId,uuid(501))
 assert.ok(lines.every(l=>!l.includes('test-key') && !l.includes('Jump Factory')))
 const dry=database(5)
 const capped=await runBackfill({db:dry,apiKey:'key',limit:5,maxCalls:1,report,fetcher,sleep:async()=>{}})
 assert.equal(capped.calls,1);assert.equal(capped.scanned,1);assert.equal(dry.updates.length,0)
 const quota=await runBackfill({db:database(5),apiKey:'key',report,fetcher:async()=>({ok:false,status:429}),sleep:async()=>{}})
 assert.equal(quota.stopped,true);assert.equal(quota.scanned,0);assert.equal(quota.resumeAfter,'')
 const noPhoto=database(1)
 const missing=await runBackfill({db:noPhoto,apiKey:'key',apply:true,report,fetcher:async()=>({ok:true,json:async()=>({places:[{id:'ChIJvalidPlaceId123',displayName:{text:'Jump Factory'},location:{latitude:53.48,longitude:-2.24},addressComponents:[{types:['country'],shortText:'GB'},{types:['postal_code'],longText:'M1 1AA'}]}]})}),sleep:async()=>{}})
 assert.equal(missing.updated,0)
 const excluded=database(2)
 excluded.rows[0].category='Children’s playground'
 excluded.rows[1].image_url='https://existing.example/photo.jpg'
 const skip=await runBackfill({db:excluded,apiKey:'key',report,fetcher:async()=>{throw new Error('Excluded rows must never make a billable call')},sleep:async()=>{}})
 assert.equal(skip.calls,0);assert.equal(skip.scanned,0)
 let request
 const linked=database(1)
 linked.rows[0].website='https://www.google.com/maps/?query_place_id=ChIJvalidPlaceId123'
 const direct=await runBackfill({db:linked,apiKey:'key',report,fetcher:async(url,options)=>{request={url,options};return {ok:true,json:async()=> (await fetcher()).json().then(x=>x.places[0])}},sleep:async()=>{}})
 assert.equal(direct.matched,1);assert.ok(request.url.endsWith('/places/ChIJvalidPlaceId123'));assert.equal(request.options.method,'GET')
 console.log('Backfill tests passed: keyset pagination, write guards, ID-only storage, dry run, request cap, quota resume and missing-photo handling.')
} finally {await unlink(report);await rmdir(directory)}
