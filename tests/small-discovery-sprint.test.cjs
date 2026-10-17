const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
function load(file,requires,extra={}){
  const module={exports:{}}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,{module,exports:module.exports,URL,URLSearchParams,process,...extra,require:name=>requires[name]??require(name)})
  return module.exports
}
const icons=new Proxy({},{get:()=>()=>null})
const nav=load('components/nav-items.ts',{'lucide-react':icons,'@/lib/launch':{FORUM_ENABLED:false}})
test('four explicit mobile destinations leave room for More and retain all public routes',()=>{
  assert.deepEqual(Array.from(nav.NAV_ITEMS.filter(i=>i.mobile),i=>i.label),['Home','Places','Events','Activities'])
  assert.deepEqual(Array.from(nav.NAV_ITEMS.filter(i=>!i.mobile&&['/news','/originals','/deals'].includes(i.href)),i=>i.label),['News','Ideas','Deals'])
  for(const path of ['/events','/events/camp']) assert.equal(nav.isActive(path,'/events'),true)
  assert.equal(nav.isActive('/news','/events'),false)
})
test('mobile More expands with active destination and Escape returns focus',()=>{
  const React=require('react'),{renderToStaticMarkup}=require('react-dom/server')
  let state=false,focused=false
  const refs=[{current:{focus:()=>{focused=true}}},{current:null}];let index=0
  const deps={react:{...React,useState:()=>[state,v=>{state=typeof v==='function'?v(state):v}],useRef:()=>refs[index++],useEffect:()=>{}},
    'next/link':{default:({children,...props})=>React.createElement('a',props,children)},'next/navigation':{usePathname:()=>'/originals'},
    './logo':{Logo:()=>null},'./auth/user-menu':{HeaderUserButton:()=>null,SidebarUserMenu:()=>null},'./theme-toggle':{ThemeToggle:()=>null},'./install-prompt':{InstallPrompt:()=>null},'./nav-items':nav,'@/lib/utils':{cn:(...values)=>values.filter(Boolean).join(' ')},'lucide-react':icons}
  const {AppShell}=load('components/app-shell.tsx',deps)
  const render=()=>{index=0;return AppShell({children:'Page'})}
  const all=n=>!n||typeof n!=='object'?[]:[n,...[n.props?.children].flat(Infinity).flatMap(all)]
  let tree=render(),button=all(tree).find(n=>n.type==='button'&&n.props['aria-controls']==='mobile-more-navigation')
  assert.equal(button.props['aria-expanded'],false);button.props.onClick()
  tree=render();const html=renderToStaticMarkup(tree)
  assert(html.includes('id="mobile-more-navigation"'));assert(html.includes('href="/originals" aria-current="page"'))
  all(tree).find(n=>n.type==='nav'&&n.props.onKeyDown).props.onKeyDown({key:'Escape'})
  assert.equal(state,false);assert.equal(focused,true)
})
test('anonymous News client has a separate nonpersistent auth storage identity',async()=>{
  let options
  const q={data:[],error:null};for(const method of ['select','order','range','eq','or']) q[method]=()=>q
  const news=load('lib/news.ts',{'@supabase/supabase-js':{createClient:(_url,_key,value)=>{options=value;return {from:()=>q}}},'./news-geography':{}},{process:{env:{NEXT_PUBLIC_DADSPACE_SUPABASE_URL:'https://test.supabase.co',NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY:'public-key'}}})
  await news.fetchNews({page:0,category:'all',region:'all'})
  assert.equal(options.auth.storageKey,'dadspace-public-news');assert.equal(options.auth.persistSession,false);assert.equal(options.auth.detectSessionInUrl,false)
})
test('128px mobile category tile has bounded DPR 1/2/3 optimizer candidates',()=>{
  const {getImageProps}=require('next/image')
  const {props}=getImageProps({src:'/images/venues/playground.png',alt:'',fill:true,sizes:'(min-width: 768px) 144px, 128px'})
  const candidates=props.srcSet.split(', ').map(value=>({url:value.split(' ')[0],width:Number(value.split(' ')[1].slice(0,-1))}))
  assert.deepEqual([1,2,3].map(dpr=>candidates.find(c=>c.width>=128*dpr).width),[128,256,384])
  assert.equal(props.loading,'lazy')
})
