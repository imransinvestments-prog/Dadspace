const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),test=require('node:test')
const ts=require(process.env.DADSPACE_TEST_DEPENDENCIES ? process.env.DADSPACE_TEST_DEPENDENCIES+'/typescript' : 'typescript')
const root=path.resolve(__dirname,'..')
function load(file,requires){
  const code=ts.transpileModule(fs.readFileSync(path.join(root,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText
  const sandbox={exports:{},require:name=>{if(!(name in requires))throw new Error(`Unexpected module ${name}`);return requires[name]},URLSearchParams,AbortSignal,TextEncoder}
  vm.runInNewContext(code,sandbox);return {module:sandbox.exports,sandbox}
}
test('public reads exclude hidden rows, bound first page and fail honestly',async()=>{
  const records=[{id:'visible',venue_name:'Visible',public_visible:true},{id:'hidden',venue_name:'Hidden',public_visible:false}]
  const calls=[];let error=null,configured=true
  const db={from:()=>{let filters=[];return {select(columns,options){calls.push({columns,options});return this},eq(k,v){filters.push([k,v]);return this},order(){return this},range(a,b){calls.push({range:[a,b]});return Promise.resolve({data:error?null:records.filter(r=>filters.every(([k,v])=>r[k]===v)),error,count:1})},maybeSingle(){return Promise.resolve({data:records.find(r=>filters.every(([k,v])=>r[k]===v))??null,error})}}}}
  const {module:m}=load('lib/venue-discovery.ts',{'server-only':{},react:{cache:f=>f},'./supabase':{getSupabase:()=>configured?db:null},'./venues':{toVenue:r=>({id:r.id,name:r.venue_name})}})
  const page=await m.publicVenuePage();assert.deepEqual(Array.from(page.venues,v=>v.id),['visible']);assert.deepEqual(calls.at(-1).range,[0,23])
  assert.equal(await m.publicVenueById('hidden'),null)
  error={message:'offline'};assert.equal((await m.publicVenuePage()).loadFailed,true);assert.equal((await m.publicVenuePage()).venues.length,0)
  configured=false;assert.equal((await m.publicVenuePage()).loadFailed,true);await assert.rejects(m.publicVenueById('visible'),/temporarily unavailable/)
  assert(!calls[0].columns.includes('notes'));assert(!calls[0].columns.includes('review_reason'))
})
test('location remains optional before selection and after denied geolocation',async()=>{
  let states=[],refs=[],i=0,j=0,geoError,geoCalls=0
  const jsx=(type,props)=>({type,props})
  const react={createContext:()=>({Provider:'provider'}),useState:init=>{const n=i++;if(!(n in states))states[n]=init;return[states[n],v=>states[n]=v]},useRef:init=>refs[j++]??=( {current:init}),useCallback:f=>f,useEffect:()=>{},useContext:()=>{}}
  const {module:m,sandbox}=load('components/location-provider.tsx',{react,'react/jsx-runtime':{jsx,jsxs:jsx},'@/lib/distance':{parsePoint:p=>({lat:Number(p.get('lat')),lng:Number(p.get('lng'))})}})
  Object.assign(sandbox,{window:{isSecureContext:true},navigator:{geolocation:{getCurrentPosition:(_s,e)=>{geoCalls++;geoError=e}}},sessionStorage:{setItem:()=>{}},fetch:async()=>({ok:true,json:async()=>({results:[{lat:51.47,lng:-.39,label:'Hounslow'}]})})})
  const render=()=>{i=j=0;return m.LocationProvider({children:'PUBLIC_CONTENT'})}
  const nodes=n=>!n||typeof n!=='object'?[]:[n,...[n.props?.children].flat(Infinity).flatMap(nodes)]
  let tree=render();assert(tree.props.children.includes('PUBLIC_CONTENT'));assert.equal(geoCalls,0);assert.equal(tree.props.value.browseAll,true)
  tree.props.value.request();geoError({code:1});tree=render();assert(tree.props.children.includes('PUBLIC_CONTENT'));assert.equal(tree.props.value.status,'denied')
  nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'Hounslow'}})
  tree=render();await nodes(tree).find(n=>n.type==='form').props.onSubmit({preventDefault(){}})
  tree=render();assert.equal(tree.props.value.label,'Hounslow');assert.equal(tree.props.value.browseAll,false);assert(tree.props.children.includes('PUBLIC_CONTENT'))
})
test('news homepage prefers actionable relevance, never pads with weak stories',()=>{
  const {module:m}=load('lib/home-selection.ts',{})
  const rows=[{id:'weak',category:'money',relevance:3},{id:'strong',category:'parenting',relevance:5},{id:'safety',category:'safety',relevance:4}]
  assert.deepEqual(Array.from(m.selectNewsCards(rows),r=>r.id),['strong','safety'])
})
