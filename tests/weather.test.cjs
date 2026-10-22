const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test')
const ts=require('typescript')
const root=path.resolve(__dirname,'..')
function load(file,deps,globals={}){
  const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText
  const m={exports:{}}
  vm.runInNewContext(code,{module:m,exports:m.exports,URLSearchParams,URL,AbortSignal,Intl,Date,Response,process:{env:globals.env||{}},fetch:globals.fetch,require:n=>{if(!(n in deps))throw new Error('Unexpected module '+n);return deps[n]}})
  return m.exports
}
const dates=load('lib/dates.ts',{})
// Mirrors unstable_cache: resolved values are reused, rejections are not stored.
const memo=f=>{const hits=new Map();return async(...a)=>{const k=JSON.stringify(a);if(hits.has(k))return hits.get(k);const v=await f(...a);hits.set(k,v);return v}}
const day=(time,o={})=>({time,daySignificantWeatherCode:1,nightSignificantWeatherCode:0,dayMaxScreenTemperature:14.6,nightMinScreenTemperature:6.2,dayProbabilityOfPrecipitation:10,nightProbabilityOfPrecipitation:30,...o})
const body=series=>({type:'FeatureCollection',features:[{type:'Feature',properties:{timeSeries:series}}]})
const series=[day('2026-10-20T00:00Z'),day('2026-10-21T00:00Z',{daySignificantWeatherCode:null,dayMaxScreenTemperature:null,dayProbabilityOfPrecipitation:null,nightSignificantWeatherCode:12}),day('2026-10-24T00:00Z',{daySignificantWeatherCode:15,dayProbabilityOfPrecipitation:85}),day('2026-10-25T00:00Z',{daySignificantWeatherCode:99})]
function weather(env,fetch){return load('lib/weather.ts',{'server-only':{},'next/cache':{unstable_cache:memo},'./dates':dates},{env,fetch})}

test('weekend forecast shows today and the coming weekend from Met Office daily fields, never a past or guessed day',()=>{
  const w=weather({})
  const daily=w.parseDaily(body(series))
  // Wednesday 21 Oct: daytime values have gone, so the night ones stand in.
  const wed=JSON.parse(JSON.stringify(w.selectDays(daily,'2026-10-21')))
  assert.deepEqual(wed.map(d=>d.label),['Today','Saturday','Sunday'])
  assert.deepEqual(wed[0],{date:'2026-10-21',label:'Today',summary:'Light rain',max:null,min:6,rainChance:30})
  assert.deepEqual(wed[1],{date:'2026-10-24',label:'Saturday',summary:'Heavy rain',max:15,min:6,rainChance:85})
  assert.equal(wed[2].summary,null,'an unknown weather code is not invented')
  // Sunday 25 Oct: Saturday is in the past and is dropped.
  assert.deepEqual(Array.from(w.selectDays(daily,'2026-10-25'),d=>d.label),['Today'])
  // Thursday 22 Oct is missing from the series: left out, not filled in.
  assert.deepEqual(Array.from(w.selectDays(daily,'2026-10-22'),d=>d.label),['Saturday','Sunday'])
  assert.throws(()=>w.parseDaily({features:[]}),/Unexpected/)
})

test('locations share one forecast per 0.25 degree cell and failures are retried, not cached',async()=>{
  const calls=[];let fail=true
  const fetch=async(url,init)=>{calls.push({url,key:init.headers.apikey});return fail?new Response('quota',{status:429}):Response.json(body(series))}
  const w=weather({MET_OFFICE_DATAHUB_API_KEY:'k-123'},fetch)
  assert.deepEqual(JSON.parse(JSON.stringify(w.gridPoint({lat:51.51,lng:-0.27}))),{lat:51.5,lng:-0.25})
  await assert.rejects(w.forecastDays({lat:51.51,lng:-0.27}),/HTTP 429/)
  fail=false
  await w.forecastDays({lat:51.51,lng:-0.27})
  await w.forecastDays({lat:51.47,lng:-0.31})
  assert.equal(calls.length,2,'the 429 was retried; the nearby point reused the cell')
  assert.equal(calls[1].key,'k-123')
  assert.match(calls[1].url,/sitespecific\/v0\/point\/daily\?latitude=51\.5&longitude=-0\.25&/)
})

test('weather route: hidden until configured, IP area only when no location is chosen, honest failures',async()=>{
  let configured=true,result=[{label:'Today'}],seen=null
  const route=load('app/api/home/weather/route.ts',{'next/server':{NextRequest:class{},NextResponse:{json:(b,i)=>Response.json(b,i)}},
    '@/lib/distance':load('lib/distance.ts',{}),
    '@/lib/weather':{weatherConfigured:()=>configured,forecastDays:async p=>{seen=p;if(result instanceof Error)throw result;return result}}})
  const get=async(query='',headers={})=>{const r=await route.GET({nextUrl:new URL('https://x.test/api/home/weather'+query),headers:new Headers(headers)});return {status:r.status,body:await r.json(),cache:r.headers.get('cache-control')}}
  configured=false;assert.deepEqual((await get()).body,{status:'not_configured'});configured=true
  assert.equal((await get('?lat=abc&lng=1')).status,400)
  let r=await get('?lat=51.509&lng=-0.271')
  assert.deepEqual(JSON.parse(JSON.stringify(seen)),{lat:51.51,lng:-0.27});assert.equal(r.body.approximate,false);assert.equal(r.cache,'private, no-store')
  r=await get('',{'x-vercel-ip-latitude':'53.48','x-vercel-ip-longitude':'-2.24','x-vercel-ip-city':'Manchester%20City'})
  assert.equal(r.body.approximate,true);assert.equal(r.body.area,'Manchester City')
  assert.deepEqual((await get()).body,{status:'no_location'},'no chosen location and no IP area: ask, never guess')
  result=new Error('HTTP 503');r=await get('?lat=51.5&lng=-0.1');assert.equal(r.status,503);assert.equal(r.body.status,'unavailable')
  result=[];assert.equal((await get('?lat=51.5&lng=-0.1')).body.status,'unavailable','an empty forecast is not shown as weather')
})
