import assert from 'node:assert/strict'
import { parsePoint, nearestFirst } from '../lib/distance.ts'
assert.equal(parsePoint(new URLSearchParams()),null)
for(const query of ['lat=&lng=0','lat=NaN&lng=0','lat=91&lng=0','lat=1&lng=-181','lat=1'])assert.equal(parsePoint(new URLSearchParams(query)),null)
assert.deepEqual(parsePoint(new URLSearchParams('lat=0&lng=0')),{lat:0,lng:0})
assert.deepEqual(parsePoint(new URLSearchParams('lat=53.4839&lng=-2.2446')),{lat:53.48,lng:-2.24})
const input=[{id:'unknown',distance_miles:null},{id:'far',distance_miles:250},{id:'zero',distance_miles:0},{id:'near',distance_miles:2},{id:'invalid',distance_miles:NaN}]
assert.deepEqual(nearestFirst(input,()=>0).map(r=>r.id),['zero','near','far','invalid','unknown'])
assert.equal(input[0].id,'unknown')
const rows=Array.from({length:60},(_,i)=>({id:String(i).padStart(3,'0'),distance_miles:60-i}))
const sorted=nearestFirst(rows,()=>0)
assert.equal(sorted.slice(0,24)[0].id,'059')
assert.equal(sorted.slice(24,48)[0].id,'035')
assert.deepEqual(nearestFirst([{id:'b',distance_miles:1},{id:'a',distance_miles:1}],()=>0).map(r=>r.id),['a','b'])
console.log('Distance tests passed: input validation, zero distance, unknowns last, stable ties and sorting before pagination.')
