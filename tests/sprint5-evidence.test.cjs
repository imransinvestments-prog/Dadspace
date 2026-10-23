const {test}=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs'), vm=require('node:vm'), ts=require('typescript')
const {createHash}=require('node:crypto')
function load(file,deps={},env={}) {
  const module={exports:{}}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText,{module,exports:module.exports,Intl,Date,URL,AbortSignal,process:{env},require:name=>deps[name]??(name.startsWith('@/artefacts/')?JSON.parse(fs.readFileSync(name.replace('@/',''),'utf8')):require(name))})
  return module.exports
}
const health=load('lib/operations/health.ts')
const run={id:1,event:'schedule',created_at:'2026-10-15T11:30:50Z',status:'completed',conclusion:'success'}
const obs=[{run,jobs:[{name:'activities / collect',status:'completed',conclusion:'success'}]}]
test('missing slots are visible before the old sixteen-hour warning; unavailable evidence stays unknown',()=>{
  const now=new Date('2026-10-15T08:00:00Z')
  assert.equal(health.scheduledSlotHealth([],'activities / collect',now).signal,'Missing scheduled dispatch')
  assert.equal(health.scheduledSlotHealth(null,'activities / collect',now).signal,'Evidence unavailable')
  assert.equal(health.scheduledSlotHealth([{...obs[0],run:{...run,event:'workflow_dispatch'}}],'activities / collect',now).signal,'Missing scheduled dispatch')
})
test('historical delayed run is late despite a passed job; individual failures stay independent',()=>{
  const now=new Date('2026-10-15T12:00:00Z')
  assert.equal(health.scheduledSlotHealth(obs,'activities / collect',now).delayMinutes,313)
  assert.equal(health.scheduledSlotHealth(obs,'activities / collect',now).signal,'Late dispatch; job passed')
  for(const [conclusion,expected] of [['failure','Feed failed — inspect source evidence'],['cancelled','Cancelled — inspect feed evidence'],['skipped','Feed skipped — refresh not established']]){
    const evidence=[{run,jobs:[...obs[0].jobs,{name:'deals / collect',status:'completed',conclusion}]}]
    assert.equal(health.scheduledSlotHealth(evidence,'deals / collect',now).signal,expected)
    assert.equal(health.scheduledSlotHealth(evidence,'activities / collect',now).signal,'Late dispatch; job passed')
  }
})
test('slot clock handles GMT and BST and checks the next slot independently',()=>{
  assert.equal(health.scheduledSlotHealth([],'x',new Date('2026-10-25T08:30:00Z')).expectedAt,'2026-10-25T07:17:00.000Z')
  assert.equal(health.scheduledSlotHealth([],'x',new Date('2026-03-29T07:30:00Z')).expectedAt,'2026-03-29T06:17:00.000Z')
  assert.equal(health.scheduledSlotHealth(obs,'activities / collect',new Date('2026-10-15T20:00:00Z')).signal,'Missing scheduled dispatch')
})
const pack=JSON.parse(fs.readFileSync('artefacts/data/sprint5-review-pack.json','utf8'))
test('frozen samples retain exact distinct membership and snapshots; automation never invents human scores',()=>{
  for(const [key,count] of [['venues',50],['activities',100],['deals',17]]){
    const p=pack[key];assert.equal(p.rows.length,count);assert.equal(new Set(p.rows.map(r=>r.id)).size,count)
    assert.equal(p.manifest_sha256,createHash('sha256').update(JSON.stringify(p.rows)).digest('hex'))
    for(const row of p.rows) assert.equal(p.fingerprints[row.id],createHash('sha256').update(JSON.stringify(row)).digest('hex'))
    assert.match(p.human_labels,/Not supplied/)
  }
  assert.equal(pack.activities.coverage.linked_within_10km,16)
  assert.equal(pack.deals.stored_count,198)
})
function material(access){return load('lib/operations/review-material.ts',{'server-only':{},'@/lib/supabase':{getSupabase:()=>{throw Error('must not read live DB for frozen cohorts')}},'@/lib/deals':{getDeals:()=>{throw Error('must not read live Deals')}},'./sprint11-venues':load('lib/operations/sprint11-venues.ts'),'./session':{operationsAccess:async()=>access},'./processes':{OPERATIONS_PROCESSES:[]},'./review-tasks':{reviewTask:id=>[34,130,136].includes(id)},'./news-sample':{NEWS_SAMPLE:{rows:[]}}})}
test('fixed review cohorts require operator access, survive missing live DB, and have stable page boundaries',async()=>{
  await assert.rejects(material('denied').getReviewMaterial(34),/denied/)
  const m=material('allowed')
  assert.equal((await m.getReviewMaterial(130,1)).total,17)
  const a=await m.getReviewMaterial(34,1),b=await m.getReviewMaterial(34,2)
  assert.equal(a.rows.length,10);assert.equal(b.rows.length,10)
  assert.equal(a.rows.some(r=>b.rows.some(s=>r.id===s.id)),false)
  assert.equal((await m.getReviewMaterial(34,6)).rows.length,0)
})
test('#34 shows the cohort as scored: 25 reviewed originals unchanged, then the 25 replacements',async()=>{
  const venues=load('lib/operations/sprint11-venues.ts'),sample=JSON.parse(fs.readFileSync('artefacts/data/venue-review-sample-2026-10-22.json','utf8'))
  const rows=venues.REVIEW34_ROWS,fp=row=>createHash('sha256').update(JSON.stringify(row)).digest('hex')
  assert.equal(rows.length,50);assert.equal(new Set(rows.map(r=>r.id)).size,50)
  assert.equal(JSON.stringify(rows.slice(0,25).map(r=>r.id).sort()),JSON.stringify([...sample.retained_original_ids].sort()))
  for(const row of rows.slice(0,25)) assert.equal(fp(row),fp(venues.SPRINT11_VENUE_ROWS.find(r=>r.id===row.id)))
  assert.equal(JSON.stringify(rows.slice(25)),JSON.stringify(sample.rows))
  const m=material('allowed'),last=await m.getReviewMaterial(34,5)
  assert.equal(last.total,50);assert.equal(last.rows.at(-1).id,sample.rows.at(-1).id)
  const progress=load('lib/operations/venue-checks.ts',{'server-only':{},'./venue-check-labels':load('lib/operations/venue-check-labels.ts')})
  const yes={identity:'yes',location:'yes',source:'yes',access:'yes',visitor_facts:'yes',photo_rights:'yes'}
  const comment=(id,row)=>({id,user:{login:'imransinvestments-prog'},body:`Dadspace owner review v1\n\nDecision: Approved for stated scope\nVenue quality checks: ${JSON.stringify(yes)}\nReviewed record: ${row.id}\nSnapshot SHA-256: ${fp(row)}\n`})
  const result=progress.venueProgress([comment(1,rows[0]),comment(2,rows[49]),comment(3,{...rows[49],title:'edited'})],rows)
  assert.equal(result.reviewed,2);assert.equal(result.passed,2)
})
test('#34 scoring applies the owner ruling and the recorded failures',()=>{
  const venues=load('lib/operations/sprint11-venues.ts'),rows=venues.REVIEW34_ROWS,fp=row=>createHash('sha256').update(JSON.stringify(row)).digest('hex')
  const progress=load('lib/operations/venue-checks.ts',{'server-only':{},'./venue-check-labels':load('lib/operations/venue-check-labels.ts')})
  const failures=JSON.parse(fs.readFileSync('artefacts/data/venue-review-34-scoring-2026-10-22.json','utf8')).failures.map(f=>f.id)
  assert.equal(failures.length,7);assert.ok(failures.every(id=>rows.some(r=>r.id===id)))
  const review=(id,row,decision,checks)=>({id,user:{login:'imransinvestments-prog'},body:`Dadspace owner review v1\n\nDecision: ${decision}\n${checks?`Venue quality checks: ${checks}\n`:''}Reviewed record: ${row.id}\nSnapshot SHA-256: ${fp(row)}\n`})
  const unknown=JSON.stringify({identity:'unknown',location:'unknown',source:'unknown',access:'unknown',visitor_facts:'unknown',photo_rights:'unknown'})
  const no=JSON.stringify({identity:'no',location:'yes',source:'yes',access:'unknown',visitor_facts:'unknown',photo_rights:'unknown'})
  const plain=rows.filter(r=>!failures.includes(r.id)),failure=rows.find(r=>r.id===failures[0])
  const result=progress.venueProgress([
    review(1,plain[0],'Approved for stated scope'),           // approval without ticks passes
    review(2,plain[1],'Approved for stated scope',unknown),   // unknown ticks do not undo an approval
    review(3,plain[2],'Changes requested'),                   // audience-only change request passes
    review(4,plain[3],'Approved for stated scope',no),        // an explicit no is scored as given
    review(5,plain[4],'Blocked — more evidence needed'),
    review(6,failure,'Approved for stated scope'),            // recorded failure, remediated
    review(7,plain[5],'Approved for stated scope','{"identity":"yes"}'), // malformed checks never count
  ],rows)
  assert.equal(result.reviewed,6);assert.equal(result.passed,3);assert.equal(result.remediated,1);assert.equal(result.afterRemediation,4)
  assert.equal(result.qualityGate,false)
})
const dealLabels=load('lib/operations/deal-check-labels.ts')
const dealReviews=load('lib/operations/deal-checks.ts',{'server-only':{},'./deal-check-labels':dealLabels})
test('Deal scores bind owner and frozen fingerprint, count once and keep unknown/failed checks out of passes',()=>{
  const row=pack.deals.rows[0],fingerprint=pack.deals.fingerprints[row.id]
  const yes=Object.fromEntries(Object.keys(dealLabels.DEAL_CHECK_LABELS).map(key=>[key,'yes']))
  const comment=(id,checks,author='imransinvestments-prog',fp=fingerprint)=>({id,user:{login:author},body:`Dadspace owner review v1\n\nDeal quality checks: ${JSON.stringify(checks)}\nReviewed record: ${row.id}\nSnapshot SHA-256: ${fp}\n`})
  assert.equal(dealReviews.dealProgress([comment(1,yes),comment(2,yes)]).allChecksPassed,1)
  assert.equal(dealReviews.dealProgress([comment(1,yes,'outsider')]).checked,0)
  assert.equal(dealReviews.dealProgress([comment(1,yes,'imransinvestments-prog','0'.repeat(64))]).checked,0)
  const unknown=dealReviews.dealProgress([comment(1,yes),comment(2,{...yes,available:'unknown'})])
  assert.equal(unknown.allChecksPassed,0);assert.equal(unknown.denominator,17)
  assert.equal(dealReviews.dealProgress([comment(1,{...yes,savings:'no'})]).knownFailures,1)
  assert.equal(dealReviews.dealProgress([comment(1,yes),{...comment(2,yes),body:`Dadspace owner review v1\nReviewed record: ${row.id}\nSnapshot SHA-256: ${fingerprint}\n`}]).checked,0)
})
test('News transport/configuration failures differ from empty results and tied dates use a stable ID order',async()=>{
  const geography=load('lib/news-geography.ts',{'../news_geography.json':JSON.parse(fs.readFileSync('news_geography.json','utf8'))})
  function news(response,env={NEXT_PUBLIC_SUPABASE_URL:'https://example.supabase.co',NEXT_PUBLIC_SUPABASE_ANON_KEY:'public'}){
    const calls=[],query={}
    for(const method of ['select','order','range','eq','or'])query[method]=(...args)=>{calls.push([method,...args]);return query}
    query.then=(resolve,reject)=>Promise.resolve().then(()=>{if(response instanceof Error)throw response;return response}).then(resolve,reject)
    return {module:load('lib/news.ts',{'@supabase/supabase-js':{createClient:()=>({from:()=>query})},'./news-geography':geography},env),calls}
  }
  const args={region:'england',category:'education',page:1}
  for(const result of [{data:null,error:{}},new Error('transport')]) await assert.rejects(news(result).module.fetchNews(args),/unavailable|transport/)
  await assert.rejects(news({data:[],error:null},{}).module.fetchNews(args),/missing/)
  const empty=news({data:[],error:null});assert.equal((await empty.module.fetchNews(args)).length,0)
  assert.deepEqual(empty.calls.filter(c=>c[0]==='order').map(c=>c[1]),['published_at','id'])
  assert.deepEqual(empty.calls.find(c=>c[0]==='range'),['range',20,39])
})
