const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
function factory(createBrowserClient,browser=true){
  const module={exports:{}}
  const code=ts.transpileModule(fs.readFileSync('lib/supabase/client.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText
  vm.runInNewContext(code,{module,exports:module.exports,process:{env:{NEXT_PUBLIC_DADSPACE_SUPABASE_URL:'https://test.supabase.co',NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY:'public-test-key',NODE_ENV:'production'}},...(browser?{window:{}}:{}),require:()=>({createBrowserClient})})
  return module.exports.createClient
}
test('one browser instance, separate server calls and secure cookies',()=>{
  const calls=[],create=(url,key,options)=>{calls.push({url,key,options});return {auth:{}}}
  const browser=factory(create)
  assert.equal(browser(),browser());assert.equal(calls.length,1);assert.equal(calls[0].options.isSingleton,true);assert.equal(calls[0].options.cookieOptions.secure,true)
  const server=factory(create,false)
  assert.notEqual(server(),server());assert.equal(calls.at(-1).options.isSingleton,false)
})
test('real auth client shares sign-in, refresh and sign-out across browser consumers with mocked transport',async()=>{
  const {createBrowserClient}=require('@supabase/ssr')
  const jar=new Map(),events=[]
  const user={id:'00000000-0000-4000-8000-000000000001',aud:'authenticated',email:'test@example.invalid',app_metadata:{},user_metadata:{},created_at:'2026-01-01T00:00:00Z'}
  let version=0
  const token=()=>{
    const exp=Math.floor(Date.now()/1000)+3600
    const jwt=[{alg:'HS256',typ:'JWT'},{sub:user.id,exp,aud:'authenticated'},'test-signature'].map(v=>Buffer.from(typeof v==='string'?v:JSON.stringify(v)).toString('base64url')).join('.')
    return {access_token:jwt,refresh_token:'test-refresh-'+ ++version,expires_in:3600,token_type:'bearer',user}
  }
  const create=factory((url,key,options)=>createBrowserClient(url,key,{...options,isSingleton:false,cookies:{getAll:()=>[...jar].map(([name,value])=>({name,value})),setAll:values=>values.forEach(({name,value})=>value?jar.set(name,value):jar.delete(name))},global:{fetch:async url=>new Response(String(url).includes('/logout')?'':JSON.stringify(token()),{status:200,headers:{'content-type':'application/json'}})}}))
  const a=create(),b=create()
  const subscription=b.auth.onAuthStateChange(event=>{events.push(event)}).data.subscription
  const signed=await a.auth.signInWithPassword({email:user.email,password:'test-only-never-sent'})
  assert.equal(signed.error,null);assert.equal((await b.auth.getSession()).data.session.user.id,user.id)
  const refreshed=await b.auth.refreshSession();assert.equal(refreshed.error,null);assert.equal(version,2)
  assert.equal((await a.auth.signOut()).error,null);assert.equal((await b.auth.getSession()).data.session,null)
  assert(events.includes('SIGNED_IN'));assert(events.includes('TOKEN_REFRESHED'));assert(events.includes('SIGNED_OUT'))
  subscription.unsubscribe();a.auth.stopAutoRefresh()
})
