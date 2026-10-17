const {test}=require('node:test')
const assert=require('node:assert/strict')
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript')
function load(file,deps={},env={}){
  const module={exports:{}}
  const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText
  vm.runInNewContext(code,{module,exports:module.exports,Buffer,Date,Number,Intl,AbortSignal,process:{env},require:n=>deps[n]??require(n)})
  return module.exports
}
const tokens=load('lib/operations/maintenance-token.ts',{'server-only':{}})
const access=load('lib/operations/access.ts')
const owner='11111111-1111-4111-8111-111111111111',other='22222222-2222-4222-8222-222222222222',key='test-only-maintenance-key-longer-than-thirty-two'
const intent={action:'hide',family:'news',record:'1',reason:'Owner checked this exact article',dryRun:true}
test('maintenance signature binds identity, scope, mode and expiry; malformed intents fail',()=>{
  const signed=tokens.signMaintenance(intent,owner,'a'.repeat(32),key,1000)
  assert.equal(tokens.verifyMaintenance(signed,owner,key,2000).record,'1')
  assert.equal(tokens.verifyMaintenance(signed,other,key,2000),null)
  assert.equal(tokens.verifyMaintenance(signed,owner,key,601000),null)
  assert.equal(tokens.verifyMaintenance(signed+'x',owner,key,2000),null)
  for(const patch of [{record:'1&active=eq.true'},{action:'pause'},{family:'discovery-source',action:'retry'},{reason:'short'},{dryRun:'false'}])assert.equal(tokens.maintenanceIntent({...intent,...patch}),null)
})
function maintenance(user,env){
  let privileged=0
  const module=load('lib/operations/maintenance.ts',{'server-only':{},'./maintenance-token':tokens,'./access':access,'@/lib/supabase/server':{createClient:async()=>({auth:{getUser:async()=>({data:{user},error:null})}})},'@/lib/supabase':{getSupabase:()=>{privileged++;throw Error('must not read')}}},env)
  return {module,calls:()=>privileged}
}
const user={id:owner,email:'imransinvestments@gmail.com',email_confirmed_at:'2026-10-17T10:00:00Z'}
test('review access never grants maintenance; preview environment refuses live writes even with flags',async()=>{
  const reader=maintenance(user,{DADSPACE_REVIEWER_USER_IDS:owner})
  assert.equal((await reader.module.maintenanceIdentity()).maintainer,false)
  await assert.rejects(reader.module.applyMaintenance('unsigned'));assert.equal(reader.calls(),0)
  const preview=maintenance(user,{VERCEL_ENV:'preview',DADSPACE_MAINTENANCE_ENABLED:'true',DADSPACE_MAINTAINER_USER_IDS:owner,DADSPACE_MAINTENANCE_SIGNING_KEY:key,DADSPACE_SUPABASE_SERVICE_ROLE_KEY:'test'})
  await assert.rejects(preview.module.applyMaintenance('unsigned'));assert.equal(preview.calls(),0)
  const imposter=maintenance({...user,email:'other@example.com',user_metadata:{maintainer:true}},{DADSPACE_MAINTAINER_USER_IDS:owner})
  assert.equal(await imposter.module.maintenanceIdentity(),null)
  await assert.rejects(imposter.module.applyMaintenance('unsigned'));assert.equal(imposter.calls(),0)
})
test('service-reader Originals list and direct detail both exclude operator-hidden records',async()=>{
  const requests=[]
  const db={from:table=>{const chain={select:()=>chain,eq:(key,value)=>{requests.push({key,value,table});return chain},lte:()=>chain,order:()=>chain,limit:async()=>({data:[],error:null}),maybeSingle:async()=>({data:null,error:null})};return chain}}
  const originals=load('lib/originals.ts',{'server-only':{},'@/lib/supabase':{getSupabase:()=>db}})
  await originals.getOriginals();await originals.getOriginal('daily-2026-10-17')
  assert.equal(requests.filter(r=>r.key==='ops_hidden'&&r.value===false).length,2)
})
