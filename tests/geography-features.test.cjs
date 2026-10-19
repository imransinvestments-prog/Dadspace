const {test}=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
const pack=require('../geography/test-pack.json'),reference=require('../geography/reference.json')
function load(file,dependencies={},globals={}){
  const module={exports:{}}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{fileName:file,compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true,jsx:ts.JsxEmit.ReactJSX}}).outputText,
    {module,exports:module.exports,URLSearchParams,URL,Number,Date,AbortSignal,Response,...globals,require:name=>name in dependencies?dependencies[name]:require(name)})
  return module.exports
}
const geography=load('lib/news-geography.ts',{'../news_geography.json':require('../news_geography.json')})
const distance=load('lib/distance.ts')
const radius=load('lib/discovery-radius.ts')
const next={'next/server':{NextResponse:{json:(body,options)=>({body,status:options?.status||200})}}}

test('28 verified locations retain current news mapping compatibility and official council identities',async()=>{
  for(const row of pack.cases.filter(c=>c.state==='reference_verified')){
    const nation=geography.newsSlug(row.expected_nation)
    const council=geography.newsDistrict(row.expected_council,nation)
    assert.ok(council,`${row.postcode} council is compatible`)
    const area=reference.areas.find(a=>a.code===row.expected_council_code)
    assert.equal(area.name,row.expected_council)
    assert.equal(geography.newsGeoRegion(row.expected_region),row.expected_nation==='England'?geography.newsSlug(row.expected_region):null)
    const region=load('app/api/region/route.ts',{...next,'@/lib/distance':distance,'@/lib/news-geography':geography},
      {fetch:async()=>({ok:true,json:async()=>({result:[{country:row.expected_nation,region:row.expected_region,admin_district:row.expected_council,admin_county:null}]})})})
    const result=await region.GET({url:`https://test.invalid/api/region?lat=${row.latitude}&lng=${row.longitude}`})
    assert.equal(result.body.region,nation)
    assert.equal(result.body.locality,council)
  }
  // NI administrative names are public ONS facts; no real NI postcode coordinates are used.
  assert.equal(geography.newsDistrict('Belfast','northern_ireland'),'belfast')
})

test('actual location handler covers verified points, invalid input, no match and upstream outage',async()=>{
  let mode='ok'
  const endpoint=load('app/api/location/route.ts',{...next,'@/lib/distance':distance},{fetch:async()=>({ok:mode==='ok',status:mode==='notfound'?404:503,json:async()=>({result:{postcode:'W3 9LN',latitude:51.5,longitude:-.25}})})})
  assert.equal((await endpoint.GET({url:'https://test.invalid/api/location?postcode=invalid'})).status,400)
  assert.equal((await endpoint.GET({url:'https://test.invalid/api/location?q=W3%209LN'})).body.results[0].label,'W3 9LN')
  mode='notfound';assert.equal((await endpoint.GET({url:'https://test.invalid/api/location?q=W3%209LN'})).status,404)
  mode='outage';assert.equal((await endpoint.GET({url:'https://test.invalid/api/location?q=W3%209LN'})).status,503)
})

test('radius eligibility crosses administrative boundaries and excludes unknown/online locations',()=>{
  const rows=[{id:'inside-other-council',location:'Library',distance_miles:9.999/1.609344},
    {id:'outside-same-council',location:'Park',distance_miles:10.001/1.609344},
    {id:'unknown',location:'Unresolved',distance_miles:null},{id:'online',location:'Online',distance_miles:0}]
  assert.equal(radius.withinDiscoveryScope(rows,10,'local').map(r=>r.id).join(','),'inside-other-council')
  assert.equal(radius.withinDiscoveryScope(rows,10,'unknown').map(r=>r.id).join(','),'unknown')
})

test('workspace uses exact manifest identity, explicit sample denominator and fail-closed owner access',async()=>{
  const geo=load('lib/geography.ts'),baseline=require('../geography/baseline.json'),crypto=require('node:crypto')
  const summary=geo.referenceSummary(reference.areas,pack.cases)
  assert.equal(summary.councils,361)
  assert.equal(summary.verifiedPostcodes,28)
  assert.equal(summary.blockedPostcodes,2)
  const hash=crypto.createHash('sha256').update(geo.canonicalJson(pack)).digest('hex')
  assert.equal(geo.baselineCompatible(reference.release_id,hash,baseline),true)
  assert.equal(geo.baselineCompatible('changed-release',hash,baseline),false)
  assert.equal(geo.observationLabel({status:'unavailable',count:null}),'Unavailable')
  const React=require('react'),render=require('react-dom/server').renderToStaticMarkup
  let access='allowed'
  const page=load('app/ops/geography/page.tsx',{
    'next/link':({href,children,...props})=>React.createElement('a',{href,...props},children),
    'next/navigation':{notFound:()=>{throw new Error('NOT_FOUND')},redirect:()=>{throw new Error('SIGN_IN')}},
    '@/lib/operations/session':{operationsAccess:async()=>access},'@/lib/seo':{pageMetadata:()=>({})},
    '@/lib/geography':geo,'@/geography/reference.json':reference,'@/geography/test-pack.json':pack,'@/geography/baseline.json':baseline,
  }).default
  const props={searchParams:Promise.resolve({nation:'Northern Ireland'})}
  const html=render(await page(props))
  assert.match(html,/Belfast/);assert.match(html,/Licence blocked/)
  assert.doesNotMatch(html,/Baseline and reference\/test pack do not match/)
  const original=baseline.reference_release
  baseline.reference_release='mismatched'
  const withheld=render(await page(props))
  assert.match(withheld,/National observations withheld/)
  assert.doesNotMatch(withheld,/Open feature for review/)
  baseline.reference_release=original
  access='denied';await assert.rejects(page(props),/NOT_FOUND/)
  access='sign-in';await assert.rejects(page(props),/SIGN_IN/)
  access='unavailable';assert.match(render(await page(props)),/could not be verified/)
})
