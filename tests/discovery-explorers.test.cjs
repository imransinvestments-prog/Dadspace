const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')

function component(file, dependencies) {
  let index=0
  const states=[],refs=[]
  const react={useState:initial=>{const i=index++;if(!(i in states))states[i]=typeof initial==='function'?initial():initial;return[states[i],value=>states[i]=typeof value==='function'?value(states[i]):value]},useMemo:fn=>fn(),useEffect:()=>{},useRef:initial=>refs[index++]??={current:initial}}
  const jsx=(type,props)=>({type,props})
  const module={exports:{}}
  const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText
  vm.runInNewContext(code,{module,exports:module.exports,URLSearchParams,Intl,Date,requestAnimationFrame:()=>{},window:{matchMedia:()=>({matches:true})},require:name=>{
    if(name==='react')return react
    if(name==='react/jsx-runtime')return{jsx,jsxs:jsx}
    if(!(name in dependencies))throw new Error(`Unexpected dependency ${name}`)
    return dependencies[name]
  }})
  return props=>{index=0;return Object.values(module.exports)[0](props)}
}
const nodes=value=>!value||typeof value!=='object'?[]:[value,...[value.props?.children].flat(Infinity).flatMap(nodes)]
const text=value=>Array.isArray(value)?value.map(text).join(''):value&&typeof value==='object'?text(value.props?.children):typeof value==='string'||typeof value==='number'?String(value):''
const button=(tree,label)=>nodes(tree).find(n=>n.type==='button'&&text(n)===label)

test('places wire radius/scope, preserve national ordering and hide a surprise pick on scope change',()=>{
  let location={coords:{lat:51.5,lng:-.1}},url
  const venues=[{id:'z',name:'Zulu',category:'park',distance_miles:1},{id:'a',name:'Alpha',category:'park',distance_miles:2}]
  const dependencies={
    'lucide-react':{},'@/components/location-provider':{useLocation:()=>location},
    '@/hooks/use-directory-page':{useDirectoryPage:(value,_enabled,seed)=>{url=value;return{pages:[value===seed.url?seed.page:{venues,total:2,hasMore:false}],loading:false,error:'',loadMore:()=>{},retry:()=>{}}}},
    '@/components/venues/category-rail':{CategoryRail:'CategoryRail'},'@/components/venues/venue-card':{VenueCard:'VenueCard'},'@/components/venues/venue-spotlight':{VenueSpotlight:'VenueSpotlight'},
    '@/lib/venue-meta':{categoryPlural:key=>key},'@/lib/utils':{cn:()=>''},
    '@/lib/discovery-radius':{DEFAULT_RADIUS_KM:10},'@/components/discovery-radius-controls':{DiscoveryRadiusControls:'RadiusControls'},
  }
  const render=component('components/venues/venues-directory.tsx',dependencies)
  const props={venues,initialTotal:100,initialHasMore:true,allCategories:[{key:'park',count:99}]}
  let tree=render(props),controls=nodes(tree).find(n=>n.type==='RadiusControls')
  assert.equal(controls.props.radiusKm,10);assert.equal(controls.props.includeOnline,false);assert(url.includes('radiusKm=10'))
  button(tree,'Surprise me').props.onClick();tree=render(props);assert(nodes(tree).some(n=>n.type==='VenueSpotlight'))
  controls.props.onRadius(25);tree=render(props);assert(url.includes('radiusKm=25'));assert(!nodes(tree).some(n=>n.type==='VenueSpotlight'))
  nodes(tree).find(n=>n.type==='RadiusControls').props.onScope('unknown');tree=render(props);assert(url.includes('scope=unknown'))
  button(tree,'Browse all UK places').props.onClick();tree=render(props)
  assert(!url.includes('lat='));assert(!url.includes('radiusKm='));assert(text(tree).includes('100 places UK-wide'))
  assert.deepEqual(nodes(tree).filter(n=>n.type==='VenueCard').map(n=>n.props.venue.id),['z','a'])
  assert.equal(nodes(tree).find(n=>n.type==='CategoryRail').props.total,100)
  button(tree,'Return to nearby places').props.onClick();tree=render(props)
  location={coords:{lat:52,lng:-.2}};tree=render(props);assert(url.includes('lat=52'));assert(nodes(tree).some(n=>n.type==='RadiusControls'))
  const nationalPage=component('components/venues/venues-directory.tsx',dependencies)
  tree=nationalPage({...props,initialPage:2});assert(url.includes('offset=24'));assert(!url.includes('lat='));assert(text(tree).includes('100 places UK-wide'))
  const nationalStart=component('components/venues/venues-directory.tsx',dependencies)
  tree=nationalStart({...props,initialBrowseNational:true});assert(!url.includes('lat='));assert(text(tree).includes('100 places UK-wide'))
})

test('event totals/cards use the same age/time/free/text filters and failures never look like zero supply',()=>{
  const events=[
    {id:'free',title:'Free story',age_range:'0-4',start_date:'2026-10-17',cost_text:'Free'},
    {id:'paid',title:'Paid story',age_range:'0-4',start_date:'2026-10-18',cost_text:'£5'},
    {id:'older',title:'Older story',age_range:'8-11',start_date:'2026-10-17',cost_text:'Free'},
    {id:'later',title:'Later story',age_range:'0-4',start_date:'2026-11-01',cost_text:'Free'},
  ]
  let feed={pages:[{events}],loading:false,error:''}
  const render=component('components/events/events-explorer.tsx',{
    '@/components/location-provider':{useLocation:()=>({coords:{lat:51,lng:0},browseAll:false})},'@/hooks/use-directory-page':{useDirectoryPage:()=>feed},
    'lucide-react':{},'@/components/event-card':{EventCard:'EventCard'},'@/lib/dates':{addDays:()=> '2026-10-23'},
    '@/lib/event-meta':{EVENT_CATEGORIES:[],eventCategory:()=> 'story',isFreeEvent:value=>value==='Free'},
    '@/lib/discovery-radius':{DEFAULT_RADIUS_KM:10},'@/components/discovery-radius-controls':{DiscoveryRadiusControls:'RadiusControls',LocalCoverageGap:'CoverageGap'},'@/lib/utils':{cn:()=>''},
  })
  const props={events:[],today:'2026-10-16',saturday:'2026-10-17',sunday:'2026-10-18'}
  const counts=tree=>text(nodes(tree).find(n=>n.props?.['aria-live']==='polite'))
  let tree=render(props);assert.match(counts(tree),/^4 events/)
  button(tree,'This weekend').props.onClick();tree=render(props);assert.match(counts(tree),/^3 events/)
  button(tree,'Under 5').props.onClick();tree=render(props);assert.match(counts(tree),/^2 events/)
  button(tree,'Free only').props.onClick();tree=render(props);assert.match(counts(tree),/^1 event/)
  assert.deepEqual(nodes(tree).filter(n=>n.type==='EventCard').map(n=>n.props.event.id),['free'])
  nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'not a match'}});tree=render(props);assert.match(counts(tree),/^0 events/)
  assert(nodes(tree).some(n=>n.type==='CoverageGap'))
  feed={pages:[],loading:true,error:''};tree=render(props);assert.equal(counts(tree),'');assert(!nodes(tree).some(n=>n.type==='CoverageGap'))
  feed={pages:[],loading:false,error:'Unavailable'};tree=render(props);assert.equal(counts(tree),'');assert(!nodes(tree).some(n=>n.type==='CoverageGap'))
})
