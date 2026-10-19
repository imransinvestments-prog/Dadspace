import test from 'node:test'
import assert from 'node:assert/strict'
import { discoveryPublicationReady as ready } from '../lib/discovery-publication.ts'
const rows=[1,2,3].map(n=>({id:String(n),fingerprint:'hash'+n}))
const approved=[{area:'hounslow',category:'libraries',approvedBy:'Owner',approvedAt:'2026-10-19T00:00:00Z',venues:rows}]
test('supply alone is not publication approval; exact public cohorts expire on changed facts',()=>{
 assert.equal(ready('hounslow','libraries',rows,3,false),false)
 assert.equal(ready('hounslow','libraries',rows,3,false,approved),true)
 for(const [r,n,f] of [[rows,3,true],[rows.slice(1),2,false],[rows.slice(1),3,false],[[...rows,{id:'4',fingerprint:'x'}],4,false],[[rows[0],rows[0],rows[2]],3,false],[[{...rows[0],fingerprint:'changed'},...rows.slice(1)],3,false]]) assert.equal(ready('hounslow','libraries',r,n,f,approved),false)
 assert.equal(ready('london','libraries',rows,3,false,approved),false)
 assert.equal(ready('hounslow','museums',rows,3,false,approved),false)
})
