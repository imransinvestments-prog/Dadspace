const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
function load(file,deps={},env={}){const m={exports:{}};const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;vm.runInNewContext(code,{module:m,exports:m.exports,URL,Response,Request,AbortSignal,Date,Number,Set,Map,process:{env},require:n=>n in deps?deps[n]:require(n)});return m.exports}
const cache={cache:f=>f},seo={siteUrl:'https://www.dad-space.co.uk',siteName:'Dadspace'}
function dbRows(records,mode='ok'){return{from(){let filters=[];return{select(){return this},eq(k,v){filters.push([k,v]);return this},is(k,v){filters.push([k,v]);return this},order(){return this},limit(){return this},range(){if(mode==='throw')throw Error('transport');return Promise.resolve({data:mode==='null'?null:records.filter(r=>filters.every(([k,v])=>(r[k]??null)===v)),error:mode==='error'?{}:null,count:records.length})},maybeSingle(){return Promise.resolve({data:records.find(r=>filters.every(([k,v])=>(r[k]??null)===v))||null,error:mode==='error'?{}:null})}}}}}
const mapping={toVenue:r=>({id:r.id,name:r.venue_name})}
function venues(db){return load('lib/venue-discovery.ts',{'server-only':{},react:cache,'./supabase':{getSupabase:()=>db},'./venues':mapping})}
test('reviewed aliases resolve only to a public survivor; cycles, private targets and unrelated shared names stay separate',async()=>{
 const rows=[{id:'old',venue_name:'Same name',public_visible:false,merged_into:'canonical'},{id:'canonical',venue_name:'Canonical name',public_visible:true},{id:'distinct',venue_name:'Same name',public_visible:true},{id:'cycle',merged_into:'cycle',public_visible:false}]
 const v=venues(dbRows(rows));assert.equal((await v.publicVenueDestination('old')).id,'canonical');assert.equal((await v.publicVenueDestination('distinct')).id,'distinct');assert.equal(await v.publicVenueDestination('cycle'),null)
 rows[1].public_visible=false;assert.equal(await v.publicVenueDestination('old'),null);assert.equal(await v.publicVenueById('canonical'),null)
 rows[1].public_visible=true;rows[0].merged_into=null;assert.equal(await v.publicVenueDestination('old'),null)
})
test('venue directory distinguishes configuration, transport, query and missing-page evidence from successful empty supply',async()=>{
 for(const db of [null,dbRows([],'throw'),dbRows([],'error'),dbRows([],'null')])assert.equal((await venues(db).publicVenuePage()).loadFailed,true)
 assert.equal((await venues(dbRows([])).publicVenuePage()).loadFailed,false)
 const db=dbRows([{id:'one',venue_name:'One',public_visible:true}]);assert.equal((await venues(db).publicVenuePage()).loadFailed,false)
 const q={from(){const b={select(){return b},eq(){return b},order(){return b},range:async()=>({data:[],count:25,error:null})};return b}}
 assert.equal((await venues(q).publicVenuePage()).loadFailed,true)
})
test('withdrawn event detail is absent and its source cannot become a public event',async()=>{
 const dependencies={'server-only':{},'./supabase':{getSupabase:()=>dbRows([{id:'withdrawn',listing_type:'event',withdrawn_at:'2026-10-17'}])},'./dates':{},'./distance':{},'./listing-distance':{},'./event-meta':{},'./discovery-radius':{}}
 const e=load('lib/events.ts',dependencies);assert.equal(await e.fetchEventById('withdrawn'),null)
})
test('nearby activities discard a complete first page if later transport evidence is missing',async()=>{
 let page=0;const db={from(){const b={};for(const k of ['select','order','eq','or'])b[k]=()=>b;b.range=async()=>++page===1?{data:Array.from({length:500},()=>({id:'example'})),error:null}:{data:null,error:null};return b}}
 const a=load('lib/activities.ts',{'server-only':{},'./supabase':{getSupabase:()=>db},'./activity-shared':{ACTIVITY_PAGE_SIZE:24},'./distance':{},'./listing-distance':{},'./discovery-radius':{}})
 const r=await a.fetchActivityPage({point:{lat:51,lng:0}});assert.equal(r.loadFailed,true);assert.equal(r.activities.length,0)
})
const slug=load('lib/venue-slug.ts'),eventSlug=load('lib/event-slug.ts')
const json=load('components/seo/json-ld.tsx',{'@/lib/seo':seo})
const venueSchema=load('components/venues/venues-json-ld.tsx',{'@/components/seo/json-ld':json,'@/lib/seo':seo,'@/lib/venue-slug':slug,'@/lib/venue-meta':{categoryLabel:()=> 'Place',venuePhotoUrl:()=>null}}).venueSchema
const eventSchema=load('components/events/events-json-ld.tsx',{'@/lib/event-meta':{eventImage:()=>({src:'/image.png'}),isFreeEvent:t=>t==='Free'},'@/lib/seo':seo,'@/lib/event-slug':eventSlug}).eventSchema
test('venue schema shares canonical identity, omits unknown access and avoids invented attraction types/reviews',()=>{
 const row={id:'venue-id',name:'Example',category:'unknown',facilities:[],access:'customers',is_free:null};const s=venueSchema(row)
 assert.equal(s['@type'],'Place');assert.equal(s['@id'],s.url+'#venue');assert.equal(s.publicAccess,undefined);assert.equal(s.isAccessibleForFree,undefined);assert.equal(s.geo,undefined);assert.equal(s.review,undefined)
 assert.equal(venueSchema({...row,access:'yes'}).publicAccess,true);assert.equal(venueSchema({...row,access:'private'}).publicAccess,false)
})
test('event list and detail builder uses stable Dadspace URLs and never guesses offer availability or price',()=>{
 const e={id:'event-id',title:'Family day',start_date:'2026-11-01',end_date:null,cost_text:'From £5, booking conditions apply',location:null,age_range:null}
 const s=eventSchema(e);assert.equal(s['@id'],s.url+'#event');assert.match(s.url,/dad-space.co.uk\/events\//);assert.equal(s.offers,undefined);assert.equal(s.location,undefined);assert.equal(s.typicalAgeRange,undefined);assert.equal(s.eventStatus,undefined)
})
test('JSON-LD output safely round-trips hostile names without closing the script',()=>{
 const {renderToStaticMarkup}=require('react-dom/server');const text='</script><script>alert(1)</script> & “place”';const html=renderToStaticMarkup(json.JsonLd({data:{'@context':'https://schema.org','@type':'Thing',name:text}}));const body=html.slice(html.indexOf('>')+1,html.lastIndexOf('</script>'))
 assert(!body.includes('<script>'));assert.equal(JSON.parse(body).name,text)
})
test('missing server credential does not silently fall back to an RLS-empty anonymous client',()=>{
 let created=0;const s=load('lib/supabase.ts',{'server-only':{},'@supabase/supabase-js':{createClient(){created++;return{}}}},{NEXT_PUBLIC_DADSPACE_SUPABASE_URL:'https://example.supabase.co',NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY:'public-test'})
 assert.equal(s.getSupabase(),null);assert.equal(created,0)
})
test('news and deals distinguish absent evidence and transport/query failures from genuine empty supply',async()=>{
 for(const mode of ['empty','null','error','throw']){
  const q={};for(const k of ['select','eq','like','gte','order','range','or'])q[k]=()=>q
  q.then=(resolve,reject)=>Promise.resolve().then(()=>{if(mode==='throw')throw Error('transport');return{data:mode==='null'?null:[],error:mode==='error'?{}:null}}).then(resolve,reject);q.limit=()=>q
  const db={from:()=>q};const deals=load('lib/deals.ts',{'server-only':{},react:cache,'./supabase':{getSupabase:()=>db},'./deals-selection':{selectDeals:r=>r}})
  assert.equal((await deals.getDeals()).loadFailed,mode!=='empty',mode)
  const news=load('lib/news.ts',{'@supabase/supabase-js':{createClient:()=>db},'./news-geography':{}},{NEXT_PUBLIC_DADSPACE_SUPABASE_URL:'https://example.supabase.co',NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY:'public-test'})
  const run=()=>news.fetchNews({region:'all',category:'all',page:0});if(mode==='empty')assert.equal((await run()).length,0);else await assert.rejects(run())
 }
})
test('merged detail URLs redirect temporarily and rollback restores the original URL',async()=>{
 const sourceId='12345678-1234-1234-1234-123456789abc', targetId='12345678-1234-1234-1234-123456789def'
 let destination={id:targetId,name:'Survivor'}
 const page=load('app/venues/[slug]/page.tsx',{'next/link':{},'next/navigation':{notFound(){throw Error('NOT_FOUND')},redirect:p=>{throw Error('TEMPORARY '+p)},permanentRedirect:p=>{throw Error('PERMANENT '+p)}},'@/lib/venue-discovery':{publicVenueDestination:async()=>destination},'@/lib/venue-slug':slug,'@/lib/venue-meta':{categoryLabel:()=> 'Place',venuePhotoUrl:()=>null,categoryImage:()=>null},'@/lib/seo':{...seo,pageMetadata:()=>({})},'@/components/venues/venue-photo':{},'@/components/venues/venues-json-ld':{},'@/components/seo/json-ld':{},'@/components/venues/venue-spotlight':{},'@/components/venues/venue-access':{}})
 const params={params:Promise.resolve({slug:'old--'+sourceId})};await assert.rejects(page.generateMetadata(params),/TEMPORARY.*survivor/)
 destination={id:sourceId,name:'Old'};await page.generateMetadata(params)
 destination=null;await assert.rejects(page.generateMetadata(params),/NOT_FOUND/)
})
