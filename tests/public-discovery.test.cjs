const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test')
const ts=require(process.env.DADSPACE_TEST_DEPENDENCIES ? process.env.DADSPACE_TEST_DEPENDENCIES+'/typescript' : 'typescript')
const root=path.resolve(__dirname,'..')
function load(file,requires){
  const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText
  const sandbox={exports:{},require:name=>{if(!(name in requires))throw new Error(`Unexpected module ${name}`);return requires[name]},URLSearchParams,URL,Request,Response,AbortSignal,TextEncoder}
  vm.runInNewContext(code,sandbox);return {module:sandbox.exports,sandbox}
}
test('retired indoor/outdoor URLs cannot activate unsupported RPC filters',async()=>{
  let rpcArgs=null,pageCalls=0
  const db={rpc:async(_name,args)=>{rpcArgs=args;return {data:{rows:[{id:'family'}],total:1},error:null}}}
  const {module:m}=load('app/api/venues/route.ts',{
    '@/lib/supabase':{getSupabase:()=>db},'@/lib/venues':{toVenue:r=>r},
    '@/lib/distance':{parsePoint:p=>p.has('lat')?{lat:51.5,lng:-.1}:null},
    '@/lib/discovery-radius':load('lib/discovery-radius.ts',{}).module,
    '@/lib/venue-discovery':{publicVenuePage:async()=>{pageCalls++;return {venues:[{id:'family'}],total:1,hasMore:false,loadFailed:false}}},
  })
  let response=await m.GET(new Request('https://dadspace.example/api/venues?indoor=true&outdoor=true'))
  assert.equal(response.status,200);assert.equal(pageCalls,1);assert.equal(rpcArgs,null)
  response=await m.GET(new Request('https://dadspace.example/api/venues?lat=51.5&lng=-.1&indoor=true&outdoor=true&free=true&q=family'))
  assert.equal(response.status,200);assert.equal(rpcArgs.p_indoor,undefined);assert.equal(rpcArgs.p_outdoor,undefined)
  assert.equal(rpcArgs.p_free,true);assert.equal(rpcArgs.p_query,'family')
  assert.equal((await response.json()).venues[0].id,'family')
})
test('public reads exclude hidden adult gaming, retain a family casino name and fail honestly',async()=>{
  const records=[{id:'visible',venue_name:'Grand Casino',public_visible:true},{id:'hidden',venue_name:'Reels Casino Slots',public_visible:false}]
  const calls=[];let error=null,configured=true
  const db={from:()=>{let filters=[];return {select(columns,options){calls.push({columns,options});return this},eq(k,v){filters.push([k,v]);return this},order(){return this},range(a,b){calls.push({range:[a,b]});return Promise.resolve({data:error?null:records.filter(r=>filters.every(([k,v])=>r[k]===v)),error,count:1})},maybeSingle(){return Promise.resolve({data:records.find(r=>filters.every(([k,v])=>r[k]===v))??null,error})},then(resolve,reject){return Promise.resolve({data:null,error,count:records.filter(r=>filters.every(([k,v])=>r[k]===v)).length}).then(resolve,reject)}}}}
  const {module:m}=load('lib/venue-discovery.ts',{'server-only':{},react:{cache:f=>f},'next/cache':{unstable_cache:f=>f},'./supabase':{getSupabase:()=>configured?db:null},'./venues':{toVenue:r=>({id:r.id,name:r.venue_name})},'node:crypto':require('node:crypto'),'./discovery-publication':load('lib/discovery-publication.ts',{}).module})
  const page=await m.publicVenuePage();assert.deepEqual(Array.from(page.venues,v=>v.id),['visible']);assert.deepEqual(calls.find(c=>c.range).range,[0,24])
  assert.equal(page.venues[0].name,'Grand Casino');assert.equal((await m.publicVenueById('visible')).name,'Grand Casino')
  assert.equal(await m.publicVenueById('hidden'),null)
  records[0].public_visible=false
  assert.equal(await m.publicVenueById('visible'),null)
  assert.equal((await m.publicVenuePage()).venues.length,0)
  records[0].public_visible=true
  error={message:'offline'};assert.equal((await m.publicVenuePage()).loadFailed,true);assert.equal((await m.publicVenuePage()).venues.length,0)
  configured=false;assert.equal((await m.publicVenuePage()).loadFailed,true);await assert.rejects(m.publicVenueById('visible'),/temporarily unavailable/)
  assert(!calls[0].columns.includes('notes'));assert(!calls[0].columns.includes('review_reason'))
})
test('location remains optional before selection and after denied geolocation',async()=>{
  let states=[],refs=[],i=0,j=0,geoError,geoCalls=0
  const jsx=(type,props)=>({type,props})
  const react={createContext:()=>({Provider:'provider'}),useState:init=>{const n=i++;if(!(n in states))states[n]=init;return[states[n],v=>states[n]=typeof v==='function'?v(states[n]):v]},useRef:init=>refs[j++]??=( {current:init}),useCallback:f=>f,useEffect:()=>{},useContext:()=>{}}
  const {module:m,sandbox}=load('components/location-provider.tsx',{react,'react/jsx-runtime':{jsx,jsxs:jsx},'@/lib/distance':{parsePoint:p=>({lat:Number(p.get('lat')),lng:Number(p.get('lng'))})}})
  Object.assign(sandbox,{window:{isSecureContext:true},navigator:{geolocation:{getCurrentPosition:(_s,e)=>{geoCalls++;geoError=e}}},sessionStorage:{setItem:()=>{}},fetch:async()=>({ok:true,json:async()=>({results:[{lat:51.47,lng:-.39,label:'Hounslow'}]})})})
  const render=()=>{i=j=0;return m.LocationProvider({children:'PUBLIC_CONTENT'})}
  sandbox.requestAnimationFrame=fn=>fn()
  const nodes=n=>!n||typeof n!=='object'?[]:[n,...[n.props?.children].flat(Infinity).flatMap(nodes)]
  let tree=render();assert(tree.props.children.includes('PUBLIC_CONTENT'));assert.equal(geoCalls,0)
  assert.equal(nodes(tree).find(n=>n.type==='form').props.hidden,true)
  nodes(tree).find(n=>n.type==='button'&&n.props['aria-controls']==='location-search-form').props.onClick()
  tree=render();assert.equal(nodes(tree).find(n=>n.type==='form').props.hidden,false)
  await nodes(tree).find(n=>n.type==='form').props.onSubmit({preventDefault(){}})
  tree=render();assert(nodes(tree).some(n=>n.props?.role==='alert'));assert.equal(nodes(tree).find(n=>n.type==='form').props.hidden,false)
  // Main now starts with the owner-approved London fallback (#58/#59).
  assert.equal(tree.props.value.browseAll,false);assert.equal(tree.props.value.label,'Central London')
  assert.equal(tree.props.value.coords.lat,51.5074);assert.equal(tree.props.value.coords.lng,-0.1278)
  tree.props.value.request();geoError({code:1});tree=render();assert(tree.props.children.includes('PUBLIC_CONTENT'));assert.equal(tree.props.value.status,'denied')
  nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'Hounslow'}})
  tree=render();await nodes(tree).find(n=>n.type==='form').props.onSubmit({preventDefault(){}})
  tree=render();assert.equal(tree.props.value.label,'Hounslow');assert.equal(tree.props.value.browseAll,false);assert(tree.props.children.includes('PUBLIC_CONTENT'))
  assert.equal(nodes(tree).find(n=>n.type==='form').props.hidden,true)
  nodes(tree).find(n=>n.type==='button'&&n.props['aria-controls']==='location-search-form').props.onClick()
  tree=render();assert.equal(nodes(tree).find(n=>n.type==='input').props.value,'Hounslow')
})
test('home data only queries the sections the dashboard renders',async()=>{
  const tables=[]
  const db={from:table=>{tables.push(table);const q={select:()=>q,limit:async()=>({data:[{id:1,title:'Nap tips',comments:[1,2]},{id:2,title:'Kit',comments:'5'}],error:null})};return q}}
  const homeData=forum=>load('lib/data.ts',{'server-only':{},'./launch':{FORUM_ENABLED:forum},'./news-monthly':{getMonthlyNews:async()=>({month:'October 2026',counts:{safety:3}})},'./supabase':{getSupabase:()=>db},'./dates':{londonHour:()=>12,londonToday:()=> '2026-10-08',upcomingWeekend:()=>({saturday:'2026-10-10',sunday:'2026-10-11',sleeps:2}),formatEventDate:()=> '10–11 October'}}).module
  const data=await homeData(false).getHomeData()
  assert.deepEqual(tables,[],'no table reads while the forum is hidden')
  assert.deepEqual(Object.keys(data).sort(),['greeting','monthlyNews','sleepsToWeekend','threads','weekendLabel'])
  assert.equal(data.greeting,'Afternoon, Dad.');assert.equal(data.weekendLabel,'10–11 October');assert.equal(data.monthlyNews.counts.safety,3)
  assert.equal(data.threads.items.length,0)
  const live=await homeData(true).getHomeData()
  assert.deepEqual(tables,['forum_threads'])
  assert.deepEqual(Array.from(live.threads.items,t=>t.id),['2','1'])
})
