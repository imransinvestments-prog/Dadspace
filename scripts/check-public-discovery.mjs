// Read-only checks against a deployed build. No collector runs or database writes.
import assert from 'node:assert/strict'
import { isUnreleasedForumUrl } from './sitemap-checks.mjs'
const base=(process.env.DADSPACE_CHECK_URL || 'https://www.dad-space.co.uk').replace(/\/$/,'')
const report={base,date:new Date().toISOString(),pages:[],sitemaps:[]}
async function read(path){const start=performance.now();const r=await fetch(base+path,{signal:AbortSignal.timeout(60000)});const html=await r.text();return{status:r.status,html,ms:Math.round(performance.now()-start),bytes:Buffer.byteLength(html)}}
for(const path of ['/','/venues','/places/hounslow/libraries','/places/manchester/museums','/places/london/soft-play']){
 const r=await read(path);assert.equal(r.status,200,path)
 // Check actual visible markup, not a name present only in the RSC stream.
 assert.match(r.html,/<h1\b/,path)
 assert.match(r.html,/<a[^>]+href="\/venues\/[^"?]+--[a-f0-9-]+"/,`${path}: no crawlable venue links`)
 report.pages.push({path,status:r.status,ms:r.ms,bytes:r.bytes})
 if(path==='/venues'){
  const slug=/href="(\/venues\/[^"?]+--[a-f0-9-]+)"/.exec(r.html)[1]
  const detail=await read(slug);assert.equal(detail.status,200);assert.match(detail.html,/<h1\b/);assert.match(detail.html,/application\/ld\+json/)
  report.pages.push({path:slug,status:detail.status,ms:detail.ms,bytes:detail.bytes})
 }
}
for(const path of ['/venues/not-a-venue','/places/unknown/museums','/venues?page=0'])assert.equal((await read(path)).status,404,path)
const index=await read('/sitemap.xml');assert.equal(index.status,200);assert.match(index.html,/<sitemapindex/)
const urls=[...index.html.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1])
const seen=new Set()
for(const url of urls){
 const path=new URL(url).pathname,r=await read(path);assert.equal(r.status,200,path)
 const count=[...r.html.matchAll(/<url>/g)].length;assert(count<=50000);assert(r.bytes<=50*1024*1024)
 for(const match of r.html.matchAll(/<loc>([^<]+)<\/loc>/g)){
  const canonical=match[1].replace(/&amp;/g,'&')
  assert(!isUnreleasedForumUrl(canonical))
  assert(!seen.has(canonical),`Duplicate sitemap URL: ${canonical}`);seen.add(canonical)
  if(process.env.DADSPACE_HIDDEN_VENUE_ID)assert(!canonical.includes(process.env.DADSPACE_HIDDEN_VENUE_ID))
 }
 report.sitemaps.push({path,count,ms:r.ms,bytes:r.bytes})
}
report.venueUrls=report.sitemaps.filter(s=>s.path.includes('/venues/')).reduce((n,s)=>n+s.count,0)
if(process.env.DADSPACE_PUBLIC_VENUE_COUNT)assert.equal(report.venueUrls,Number(process.env.DADSPACE_PUBLIC_VENUE_COUNT))
console.log(JSON.stringify(report,null,2))
